from typing import Any

from colorama import Fore, Style


def print_colored(color: str, text: str) -> None:
    print(f"{color}{text}{Style.RESET_ALL}")


def print_header(text: str) -> None:
    print_colored(Fore.CYAN + Style.BRIGHT, f"\n{'=' * 50}\n {text}\n{'=' * 50}")


def print_info(label: str, value: Any) -> None:
    print_colored(Fore.GREEN, f"{label}: {value}")


def print_warning(text: str) -> None:
    print_colored(Fore.YELLOW, text)


def print_error(text: str) -> None:
    print_colored(Fore.RED, text)
