from lazy_wifi.configurations.context import ConfigurationException
from lazy_wifi.src.interfaces import Interfaces


class BasicConfig:
    def __init__(self, context):
        self.context = context
        self.current_config_section = self.context.config['BASIC_CONF']

    def setup(self):
        """
        Validate BASIC CONFIG section in config file
        """
        interface = self.current_config_section.get('interface_name')
        self.context.main_interface = Interfaces(self.context).create_and_validate_device(interface) or None
        if not self.context.main_interface:
            raise ConfigurationException(message=f'Invalid interface specified {interface}', section='BASIC_CONF')
