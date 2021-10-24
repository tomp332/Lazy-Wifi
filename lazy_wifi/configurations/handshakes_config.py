from lazy_wifi.configurations.context import ConfigurationException, Context


class HandshakesConfig:
    def __init__(self, context: Context):
        self.context = context
        self.current_config_section = self.context.config['HANDSHAKES']

    def setup(self):
        """
            Validate HANDSHAKES section in config file
        """
        try:
            # Validate num of packets
            handshake_scan_time = int(self.current_config_section.get('handshake_scan_time'))
            self.context.validate_scan_times(handshake_scan_time,
                                             section='HANDSHAKES',
                                             message="handshake_scan_time is not set to a valid number")
            self.context.handshake_scan_time = int(handshake_scan_time)
        except (AttributeError, TypeError):
            raise ConfigurationException(section='HANDSHAKES',
                                         message="handshake_scan_time is not set to a valid number")
        self.context.saved_pcap_files_directory = self.context.validate_path(self.context.saved_pcap_files_directory,
                                                                             section='HANDSHAKES',
                                                                             type_path=self.context.DIRECTORY,
                                                                             message='Invalid data directory path')
