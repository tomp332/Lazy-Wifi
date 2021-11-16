#!/usr/bin/python3

import sys
import requests
from shlex import split
from subprocess import Popen, PIPE


class AWSAutomation:
    """
    USAGE:
    1. Upload to AWS machine
    2. Add your file settings to const variables
    3. Add your mailgun configurations to const variables
    """
    # Files settings
    _MAIN_DICTIONARY_FILE = ''
    _PCAP_FILES_DIRECTORY = ''

    # Cracking settings
    _SUCCESS_KEY = 'The PSK is'
    _FAILED_KEY = 'Unable to identify the PSK from the dictionary file'

    # Email settings
    _MAILGUN_USER = ''
    _MAILGUN_API_KEY = ''
    _MAILGUN_DOMAIN = ''
    _DESTINATION_EMAIL = ''

    def __init__(self):
        self.ssid = None
        self.file = None
        self.cracked_password = None

        self.validate_args()
        self.validate_cowpatty()

    def validate_args(self):
        len_args = len(sys.argv)
        if len_args == 3:  # Valid number of arguments
            self.ssid = sys.argv[1].strip()
            self.file = sys.argv[2].strip()
        else:  # Print help message because of invalid arguments
            self.help_message()
            raise Exception("[-] Invalid amount of arguments")

    def start_cracking(self):
        """
        Start cracking password, send mail if password was cracked
        """
        print("[+] Starting password cracking!")
        command = f"cowpatty " \
                  f"-r '{self._PCAP_FILES_DIRECTORY}/{self.file}' " \
                  f"-s '{self.ssid}' -f '{self._MAIN_DICTIONARY_FILE}' -2"
        output, _ = self.execute_command(command)
        output = output.decode()
        # Start parsing cowpatty output until error, success or failure is outputted
        while output:
            # Check if the success key is in output
            if self._SUCCESS_KEY in output:
                parsed, self.cracked_password, _ = output.split('"')
                self.cracked_password.strip()
                self.send_mail()
                print("[+] Sent email with cracked password")
                break
            elif self._FAILED_KEY in output:
                print("[-] Unable to crack cracked_password")
                break

    def send_mail(self):
        """
        Send mailgun api mail for cracked password
        """
        self.write_password_to_file()
        return requests.post(
            f"https://api.mailgun.net/v3/{self._MAILGUN_DOMAIN}/messages",
            auth=("api", self._MAILGUN_API_KEY),
            data={"from": f"User <{self._MAILGUN_USER}@{self._MAILGUN_DOMAIN}>",
                  "to": [self._DESTINATION_EMAIL],
                  "subject": "Results",
                  "text": f"Your cracked_password has been cracked for {self.ssid}:{self.cracked_password}"})

    def write_password_to_file(self):
        with open(f'{self.ssid}_cracked.txt', 'w') as file:
            file.write(f'{self.ssid}:{self.cracked_password}')

    def validate_cowpatty(self):
        """
        Validate cowpatty installation on machine
        """
        output, errors = self.execute_command('which cowpatty')
        if not output.decode():
            print("[-] Please install cowpatty to continue!")
            exit(1)

    @staticmethod
    def execute_command(command, shell=False):
        """
        Execute shell command
        """
        proc = Popen(split(command), stdout=PIPE, stderr=PIPE, shell=shell)
        output, errors = proc.communicate()
        return output, errors

    @staticmethod
    def help_message():
        print("[-] Invalid arguments, Usage: crack.py [ssid] [pcap file path]")


if __name__ == '__main__':
    AWSAutomation().start_cracking()
