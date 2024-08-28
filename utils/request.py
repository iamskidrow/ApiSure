import requests
import time
from requests.exceptions import RequestException, SSLError
from typing import Optional, Any
from helpers.output import print_error, print_warning


def make_request(
        method: str,
        url: str,
        retries: int = 3,
        delay: float = 2,
        timeout: Optional[int] = None,
        verify_ssl: bool = True,
        **kwargs: Any
) -> Optional[requests.Response]:
    for attempt in range(retries):
        try:
            response = requests.request(method, url, timeout=timeout, verify=verify_ssl, **kwargs)
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
