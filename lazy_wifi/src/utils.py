from termcolor import colored


def print_status(message: str = None, color: str = "green"):
    print(colored(f"[+] {message}", color))


def print_message(message: str = None, color: str = 'yellow'):
    print(colored(f"\t[->] {message}", color))


def print_alert(message: str = None, color: str = 'yellow'):
    print(colored(f"[->] {message}", color))


def print_module(message: str = None, color: str = "blue"):
    print(colored(f"[+] {message}", color))


def print_error(message: str = None, color: str = "red"):
    print(colored(f"[-] Error: {message}", color))
