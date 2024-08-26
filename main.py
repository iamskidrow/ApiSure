import requests
import json
import argparse
import time
from requests.exceptions import RequestException, SSLError
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init()


def print_header(text):
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 50}")
    print(f" {text}")
    print(f"{'=' * 50}{Style.RESET_ALL}")


def print_info(label, value):
    print(f"{Fore.GREEN}{label}:{Style.RESET_ALL} {value}")


def print_warning(text):
    print(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")


def print_error(text):
    print(f"{Fore.RED}{text}{Style.RESET_ALL}")


def make_request(method, url, headers=None, json=None, retries=3, delay=2, verify_ssl=True):
    for attempt in range(retries):
        try:
            response = requests.request(method, url, headers=headers, json=json, verify=verify_ssl)
            response.raise_for_status()
            return response
        except SSLError as e:
            print_error(f"SSL Error occurred: {e}")
            if not verify_ssl:
                print_warning("SSL verification is disabled. This is not recommended for production use.")
            return None
        except RequestException as e:
            if attempt < retries - 1:
                print_warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                time.sleep(delay)
            else:
                print_error(f"Request failed after {retries} attempts: {e}")
                return None


def extract_keys_from_schema(schema):
    keys = set()
    if schema.get('type') == 'object':
        properties = schema.get('properties', {})
        keys.update(properties.keys())
    elif schema.get('type') == 'array' and 'items' in schema:
        items = schema['items']
        if items.get('type') == 'object':
            keys.update(extract_keys_from_schema(items))
    return keys


def extract_keys_from_response(response):
    keys = set()
    if isinstance(response, list):
        for item in response:
            if isinstance(item, dict):
                keys.update(item.keys())
    elif isinstance(response, dict):
        keys.update(response.keys())
    return keys


def validate_keys(response, expected_keys):
    response_keys = extract_keys_from_response(response)
    return expected_keys.issubset(response_keys)


def load_test_cases(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def run_test_cases(test_cases, show_response, verify_ssl=True):
    cookies = None
    valid_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH'}
    time_threshold = 2

    for index, case in enumerate(test_cases, start=1):
        method = case['method']
        url = case['url']
        headers = case.get('headers', {})
        json_data = case.get('json', None)
        expected_status = case.get('expected_status', None)
        expected_schema = case.get('expected_schema', None)

        # Validate HTTP method
        if method not in valid_methods:
            print_error(f"Invalid HTTP method: {method}")
            continue

        # Add cookies to headers if available
        if cookies:
            headers.update({'Cookie': cookies})

        print_header(f"Test Case {index}: {method} {url}")

        response = make_request(method, url, headers=headers, json=json_data, verify_ssl=verify_ssl)

        if response:
            status_code = response.status_code
            response_time = response.elapsed.total_seconds()

            # Print status code with expected value
            if expected_status is not None:
                if status_code == expected_status:
                    print_info("Status Code", f"{status_code} (Expected: {expected_status})")
                else:
                    print_warning(f"Status Code Mismatch: Got {status_code}, Expected {expected_status}")
            else:
                print_info("Status Code", status_code)

            # Check if response time is within the acceptable threshold
            print_info("Response Time", f"{response_time:.6f} seconds")
            if response_time > time_threshold:
                print_warning(f"Response time exceeds threshold of {time_threshold} seconds")

            # Attempt to print JSON response if the content type is JSON
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    response_json = response.json()

                    schema_matches = True
                    missing_keys = set()

                    # Check if expected schema is present
                    if expected_schema:
                        expected_keys = extract_keys_from_schema(expected_schema)
                        if not validate_keys(response_json, expected_keys):
                            schema_matches = False
                            missing_keys = expected_keys - extract_keys_from_response(response_json)

                    if schema_matches:
                        print_info("Schema Validation", "Passed")
                    else:
                        print_warning("Schema Validation Failed")
                        if missing_keys:
                            print_warning(f"Missing keys in response: {missing_keys}")

                    if show_response:
                        print_info("Response Body", json.dumps(response_json, indent=2))

                except json.JSONDecodeError:
                    print_error(f"Response body is not JSON => {response.text}")
            elif 'text/html' in content_type:
                print_info("Response Body", f"HTML content: {response.text[:100]}...")
            else:
                print_warning(f"Unexpected Content-Type: {content_type}")

            # Handle cookies if login was successful
            if status_code == 200 and 'Set-Cookie' in response.headers:
                cookies = response.headers['Set-Cookie']
                print_info("Cookies", "Updated for subsequent requests")

        else:
            print_error("Request failed.")


def main():
    parser = argparse.ArgumentParser(description='Run API tests based on a JSON file.')
    parser.add_argument('test_cases_file', type=str, help='Path to the JSON file containing test cases.')
    parser.add_argument('-R', '--response', action='store_true',
                        help='Print the response body even if the structure matches.')
    parser.add_argument('--no-verify-ssl', action='store_true',
                        help='Disable SSL certificate verification')
    args = parser.parse_args()

    test_cases_file = args.test_cases_file
    show_response = args.response
    verify_ssl = not args.no_verify_ssl

    try:
        with open(test_cases_file, 'r') as file:
            test_cases = json.load(file)
    except json.JSONDecodeError:
        print_error(f"Failed to parse JSON from file: {test_cases_file}")
        return
    except FileNotFoundError:
        print_error(f"File not found: {test_cases_file}")
        return

    run_test_cases(test_cases, show_response, verify_ssl)


if __name__ == "__main__":
    main()
