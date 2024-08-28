from utils.request import make_request
from utils.validation import validate_schema, validate_content, validate_content_type, validate_headers
from utils.report import generate_html_report
from helpers.output import print_header, print_info, print_warning, print_error
from helpers.formatting import format_size, format_time

import argparse
from typing import Dict, Any
from colorama import init
import json

init()


def run_test_cases(test_cases: list[Dict[str, Any]], show_response: bool, verify_ssl: bool = True) -> None:
    cookies = None
    valid_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH'}
    time_threshold = 2

    results = {
        'pass': 0,
        'fail': 0,
        'total_time': 0,
        'total_length': 0,
        'length_count': 0,
        'test_cases': []
    }
    total_tests = len(test_cases)
    executed_tests = 0

    for index, case in enumerate(test_cases, start=1):
        if case.get('skip', False):
            print_header(f"Test Case {index} is skipped.")
            total_tests -= 1
            continue

        method = case['method']
        url = case['url']
        headers = case.get('headers', {})
        json_data = case.get('json')
        params = case.get('params')
        expected_status = case.get('expected_status')
        expected_schema = case.get('expected_schema')
        expected_headers = case.get('expected_headers', {})
        forbidden_headers = case.get('forbidden_headers', [])
        expected_response = case.get('expected_response', {})
        expected_content = case.get('expected_content', {})
        expected_types = case.get('expected_types', {})
        retry_count = case.get('retry_count', 3)
        retry_delay = case.get('retry_delay', 2000) / 1000
        timeout = case.get('timeout')

        if method not in valid_methods:
            print_error(f"Invalid HTTP method: {method}")
            continue

        if cookies:
            headers.update({'Cookie': cookies})

        print_header(f"Test Case {index}: {method} {url}")

        test_case_result = {
            'id': index,
            'description': case.get('description', f"Test Case {index}"),
            'method': method,
            'url': url,
            'passed': True,
            'validation_results': []
        }

        response = make_request(method, url, headers=headers, json=json_data, params=params,
                                retries=retry_count, delay=retry_delay, timeout=timeout,
                                verify_ssl=verify_ssl)

        if not response:
            results['fail'] += 1
            test_case_result['passed'] = False
            test_case_result['validation_results'].append({
                'passed': False,
                'message': "Request failed"
            })
            results['test_cases'].append(test_case_result)
            continue

        executed_tests += 1
        status_code = response.status_code
        response_time = response.elapsed.total_seconds()
        content_length = response.headers.get('Content-Length', 'Unknown')

        test_case_result['status_code'] = status_code
        test_case_result['expected_status'] = expected_status
        test_case_result['response_time'] = format_time(response_time)
        test_case_result['content_length'] = format_size(
            int(content_length)) if content_length.isdigit() else content_length

        if expected_status and status_code != expected_status:
            print_warning(f"Status Code Mismatch: Expected {expected_status}, but got {status_code}")
            results['fail'] += 1
            test_case_result['passed'] = False
            test_case_result['validation_results'].append({
                'passed': False,
                'message': f"Status Code Mismatch: Expected {expected_status}, but got {status_code}"
            })
            results['test_cases'].append(test_case_result)
            continue

        print_info("Status Code", f"{status_code}" + (f" (Expected: {expected_status})" if expected_status else ""))
        print_info("Response Time", format_time(response_time))
        results['total_time'] += response_time

        if response_time > time_threshold:
            print_warning(f"Response time exceeds threshold of {time_threshold} seconds")
            test_case_result['validation_results'].append({
                'passed': True,
                'warning': True,
                'message': f"Response time exceeds threshold of {time_threshold} seconds"
            })

        formatted_length = format_size(int(content_length)) if content_length.isdigit() else content_length
        print_info("Content Length", formatted_length)

        if content_length.isdigit():
            results['total_length'] += int(content_length)
            results['length_count'] += 1

        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            try:
                response_json = response.json()
                schema_valid = True

                if expected_schema:
                    missing_keys, extra_keys = validate_schema(response_json, expected_schema)
                    if missing_keys or extra_keys:
                        schema_valid = False
                        print_warning("Schema Validation Failed")
                        if missing_keys:
                            print_warning(f"Missing keys: {missing_keys}")
                        if extra_keys:
                            print_warning(f"Extra keys: {extra_keys}")
                        test_case_result['validation_results'].append({
                            'passed': False,
                            'message': f"Schema Validation Failed. Missing keys: {missing_keys}, Extra keys: {extra_keys}"
                        })
                    else:
                        print_info("Schema Validation", "Passed")

                headers_valid, headers_message = validate_headers(response.headers, expected_headers, forbidden_headers)
                if not headers_valid:
                    print_warning(f"Header Validation Failed: {headers_message}")
                    schema_valid = False
                    test_case_result['validation_results'].append({
                        'passed': False,
                        'message': f"Header Validation Failed: {headers_message}"
                    })
                else:
                    print_info("Header Validation", "Passed")

                if expected_content:
                    content_valid, content_message = validate_content(response_json, expected_content)
                    if not content_valid:
                        print_warning(f"Content Validation Failed: {content_message}")
                        schema_valid = False
                        test_case_result['validation_results'].append({
                            'passed': False,
                            'message': f"Content Validation Failed: {content_message}"
                        })
                    else:
                        print_info("Content Validation", "Passed")

                if expected_types:
                    types_valid, types_message = validate_content_type(response_json, expected_types)
                    if not types_valid:
                        print_warning(f"Content Type Validation Failed: {types_message}")
                        schema_valid = False
                        test_case_result['validation_results'].append({
                            'passed': False,
                            'message': f"Content Type Validation Failed: {types_message}"
                        })
                    else:
                        print_info("Content Type Validation", "Passed")

                if 'length' in expected_response:
                    min_length = expected_response['length'].get('min', 0)
                    if not (isinstance(response_json, list) and len(response_json) >= min_length):
                        print_warning(f"Response length is less than the minimum expected {min_length}")
                        schema_valid = False
                        test_case_result['validation_results'].append({
                            'passed': False,
                            'message': f"Response length is less than the minimum expected {min_length}"
                        })

                if show_response:
                    print_info("Response Body", json.dumps(response_json, indent=2))

                if schema_valid:
                    results['pass'] += 1
                else:
                    results['fail'] += 1
                    test_case_result['passed'] = False

            except json.JSONDecodeError:
                print_error(f"Response body is not JSON => {response.text}")
                results['fail'] += 1
                test_case_result['passed'] = False
                test_case_result['validation_results'].append({
                    'passed': False,
                    'message': "Response body is not JSON"
                })
        elif 'text/html' in content_type:
            print_info("Response Body", f"HTML content: {response.text[:100]}...")
            results['pass'] += 1
        else:
            print_warning(f"Unexpected Content-Type: {content_type}")
            results['fail'] += 1
            test_case_result['passed'] = False
            test_case_result['validation_results'].append({
                'passed': False,
                'message': f"Unexpected Content-Type: {content_type}"
            })

        if status_code == 200 and 'Set-Cookie' in response.headers:
            cookies = response.headers['Set-Cookie']
            print_info("Cookies", "Updated for subsequent requests")

        results['test_cases'].append(test_case_result)

    avg_time = results['total_time'] / executed_tests if executed_tests else 0
    avg_length = results['total_length'] / results['length_count'] if results['length_count'] else 0

    print_header("Test Summary")
    print_info("Total Test Cases", total_tests)
    print_info("Executed Test Cases", executed_tests)
    print_info("Passed", results['pass'])
    print_info("Failed", results['fail'])
    print_info("Average Response Time", format_time(avg_time))
    print_info("Average Content Length", format_size(avg_length))

    # Generate HTML report
    report_results = {
        'total_tests': total_tests,
        'executed_tests': executed_tests,
        'pass': results['pass'],
        'fail': results['fail'],
        'avg_response_time': format_time(avg_time),
        'avg_content_length': format_size(avg_length),
        'test_cases': results['test_cases']
    }
    generate_html_report(report_results)


def main() -> None:
    parser = argparse.ArgumentParser(description='Run API tests based on a JSON file.')
    parser.add_argument('test_cases_file', type=str, help='Path to the JSON file containing test cases.')
    parser.add_argument('-R', '--response', action='store_true',
                        help='Print the response body even if the structure matches.')
    parser.add_argument('--no-verify-ssl', action='store_true', help='Disable SSL certificate verification')
    args = parser.parse_args()

    try:
        with open(args.test_cases_file, 'r') as file:
            test_cases = json.load(file)
    except json.JSONDecodeError:
        print_error(f"Failed to parse JSON from file: {args.test_cases_file}")
        return
    except FileNotFoundError:
        print_error(f"File not found: {args.test_cases_file}")
        return

    run_test_cases(test_cases, args.response, not args.no_verify_ssl)


if __name__ == "__main__":
    main()
