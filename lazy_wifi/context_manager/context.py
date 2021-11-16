import os
from configparser import ConfigParser
from pathlib import Path

from lazy_wifi.class_exceptions.exceptions import ConfigurationException


class Context:
    _FULL_CONFIG_PATH = Path(os.path.dirname(__file__)).parent.joinpath('configs', 'config.ini')
    FILE = 'file'
    DIRECTORY = 'directory'

    def __init__(self):
        self.current_config_section = None
        # Main config file parser object
        self.config = ConfigParser()
        self.config.read(Path(self._FULL_CONFIG_PATH).absolute())

        self.data_directory = Path(Path(os.path.realpath(__file__)).parent.parent, 'data')

        # Basic config
        self.main_interface = None
        self.main_interface_name = None

        # Logging
        self.logs_directory = Path(self.data_directory / 'logs')
        self.log_level = None
        self.main_logger = None

        # Recon
        self.recon_scan_time = None

        # Attack
        self.num_deauth_packets = None
        self.target_ssid_list = []

        # Handshakes
        self.handshake_scan_time = None
        self.saved_pcap_files_directory = f'{self.data_directory}/handshakes'

        # Remote connections
        self.remote_hostname = None
        self.remote_private_key_path = None
        self.remote_username = None
        self.remote_password = None
        self.remote_connection_port = None
        self.remote_files_dir = None
        self.remote_connection_timeout = 10
        self.remote_upload_dir = None
        self.remote_automation_script_path = f'/home/{self.remote_username}/automation.py'

        # AWS configuration
        self.instance_id = None
        self.aws_access_key_id = None
        self.aws_secret_access_key = None
        self.shut_down_on_finish = None
        self.region = None

        # Main feature control
        self.remote_machine_available = False
        self.remote_machine_is_aws = False

    def setup(self):
        pass

    @staticmethod
    def validate_positive_int(num, section, message) -> None or ConfigurationException:
        if num < 0:
            raise ConfigurationException(section=section, message=message)

    def validate_path(self, path: str, section: str, type_path=FILE,
                      message: str = None) -> Path or ConfigurationException:
        """
            Validates a path on current system if doesn't exists, it creates it

            :param section: Config section to specify where to throw the error from, if needed
            :param path: string path for a file :param section: section of config file that is validating the path
            :param type_path: type of path to validate from the type_paths variable in current class (dictionary,file etc.)
            :param message: message to specify if there is an error
            :return: Initializes Pathlib object for the specified path
        """
        try:
            file = Path(path)
            if type_path == self.DIRECTORY:  # Validate directory
                if not file.is_dir():
                    file.mkdir(parents=True, exist_ok=True)
            elif type_path == self.FILE:  # Validate filer
                if not file.is_file():
                    file.touch(exist_ok=True)
            else:
                raise "Invalid type in path validator"
            return file
        except (PermissionError, FileNotFoundError) as e:
            raise ConfigurationException(section=section, message=message, special_exception=e)
