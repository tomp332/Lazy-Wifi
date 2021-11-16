from lazy_wifi.class_exceptions.exceptions import ConfigurationException
from lazy_wifi.src.utils import print_status
from lazy_wifi.context_manager.context import Context


class RemoteConnectionConfig:
    def __init__(self, context: Context):
        self.context = context
        self.current_config_section = self.context.config['REMOTE_CONNECTION']

    def setup(self):
        """
        Validate remote machine SSH configurations
        """
        self.context.private_key_path = self.current_config_section.get('private_key_path').strip()
        self.context.remote_password = self.current_config_section.get('remote_ssh_password')
        if self.context.private_key_path and self.context.remote_password:
            raise ConfigurationException(message='Error in authentication type for remote connection, '
                                                 'can not specify both private key and password',
                                         section='REMOTE_CONNECTIONS')
        # Validate ssh hostname
        self.context.remote_hostname = self.current_config_section.get('remote_ssh_hostname').strip()
        if not self.context.remote_hostname:
            raise ConfigurationException(message='Invalid remote hostname', section='REMOTE_CONNECTIONS')

        # Validate port
        port = int(self.current_config_section.get('remote_connection_port'))
        Context.validate_positive_int(port, message="Invalid remote port specified", section="REMOTE_CONNECTION")
        self.context.remote_connection_port = port or 22

        # Validate auth type
        # if (self.context.private_key_path or self.context.remote_password) is None:
        #     raise ConfigurationException(message='Error in authentication type for remote connection, no valid '
        #                                          'private key nor password were specified!',
        #                                  section='REMOTE_CONNECTIONS')

        self.context.remote_username = self.current_config_section.get('remote_ssh_username')

        remote_upload_path = self.current_config_section.get('remote_upload_dir')
        self.context.remote_upload_dir = remote_upload_path if remote_upload_path else \
            f'/home/{self.context.remote_username}/wifi_uploads'

        # Remote script path
        self.context.remote_automation_script_path = self.current_config_section.get('remote_automation_script_path')

        # Validate for aws and remote configurations
        if self.context.remote_machine_is_aws:
            print_status("Remote machine configuration set for AWS instance")
        else:
            print_status("AWS configurations setup incorrectly, continuing with SSH remote connection without AWS instance")
        self.context.remote_machine_available = True
