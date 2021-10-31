from lazy_wifi.context_manager.context import Context, ConfigurationException


class RemoteConnectionConfig:
    def __init__(self, context: Context):
        self.context = context
        self.current_config_section = self.context.config['REMOTE_CONNECTION']

    def setup(self):
        """
        Validate remote machine SSH configurations
        """
        self.context.private_key_path = self.current_config_section.get('private_key_path')
        self.context.remote_password = self.current_config_section.get('remote_ssh_password')

        # Validate auth type
        if (self.context.private_key_path or self.context.remote_password) is None:
            raise ConfigurationException(message='Error in authentication type for remote connection, no valid '
                                                 'private key nor password were specified!',
                                         section='REMOTE_CONNECTIONS')

        self.context.remote_username = self.current_config_section.get('remote_ssh_username')

        default_path = self.current_config_section.get('remote_upload_dir')
        self.context.remote_upload_dir = default_path if default_path else f'/home/{self.context.remote_username}/wifi_attack_files '
