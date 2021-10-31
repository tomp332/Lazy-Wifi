import logging
from pathlib import Path

from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.rsakey import RSAKey

from lazy_wifi.context_manager.context import Context
from lazy_wifi.src.utils import print_error, print_status

logging.getLogger("paramiko").setLevel(logging.ERROR)


class RemoteConnection:
    def __init__(self, context: Context):
        self.context = context
        self.remote_hostname = self.context.ec2_public_hostname
        self.remote_username = self.context.remote_username
        # Paramiko required conversion between types of private key files
        if self.context.private_key_path:
            self.private_key_file = RSAKey.from_private_key_file(self.context.private_key_path)
        # Set up a remote ssh connection
        self.ssh_connection = SSHClient()
        self.ssh_connection.set_missing_host_key_policy(AutoAddPolicy())

    def __enter__(self):
        """
            :return: Init for ssh connection once class is used
        """
        try:
            # Use password
            if self.context.remote_password:
                self.ssh_connection.connect(self.remote_hostname,
                                            username=self.remote_username,
                                            password=self.context.remote_password,
                                            auth_timeout=self.context.remote_connection_timeout)
            else:
                # Use private key only
                self.ssh_connection.connect(self.remote_hostname, username=self.remote_username,
                                            pkey=self.private_key_file)
        except TimeoutError:
            print_error("Time out while trying to connect to remote machine")
            self.context.main_logger.info("Time out while trying to connect to remote machine")
            self.context.remote_machine_available = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
            :return: closes the ssh connection on finish
        """
        self.ssh_connection.close()

    def _execute_command(self, command: str):
        """
            Execute command on remote machine

            :param command: Specified string command to execute on remote machine
            :return: Prints out the resulting output from the execution of the command
        """
        # Make the command run in background on remote machine
        _, output, errors = self.ssh_connection.exec_command(f'{command}  > /dev/null 2>&1 &')
        try:
            output = output.read().decode()
        except UnicodeDecodeError:
            output = output.read()
        try:
            errors = errors.read().decode()
        except UnicodeDecodeError:
            errors = errors.read()
        if errors:
            print_error(f'Executing ssh command {command} - {errors}')
            self.context.main_logger.info(f'Executing ssh command {command} - {errors}')
        else:
            output and print_status(f'{output}')

    def _upload_file_to_remote(self, filename: str):
        """
            Upload file to remote machine

            :param filename: File name that is to uploaded to remote host
        """
        sftp = self.ssh_connection.open_sftp()
        filename = Path(filename)
        # Create remote path if doesnt exist
        try:
            sftp.mkdir(self.context.remote_upload_dir)
        except IOError:
            pass
        sftp.put(localpath=f'{filename.resolve()}', remotepath=f'{self.context.remote_upload_dir}/{filename.name}')
        print_status(f"Uploaded file {filename} to remote machine")
        self.context.main_logger.info(f"Uploaded file {filename} to remote machine")
        sftp.close()

    def start_brute_force_on_file(self, filename: str, ssid: str):
        """
            Uploads captured EAPOL file and uploads to remote machine, then initiates cracking process for it

            :param ssid: SSID to name the file after for the attack
            :param filename: Filename of the pcap file to upload and start brute force on
        """
        self._upload_file_to_remote(filename)
        self._execute_command(f"/home/ubuntu/crack.py '{ssid}' '{Path(filename).name}'")
        self.context.main_logger.info(f"Send crack task to remote machine for ssid : {ssid}")
