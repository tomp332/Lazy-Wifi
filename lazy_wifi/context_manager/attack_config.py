import ast

from lazy_wifi.context_manager.context import Context, ConfigurationException


class AttackConfig:

    def __init__(self, context: Context):
        self.context = context
        self.current_config_section = self.context.config['ATTACK']

    def setup(self):
        """
            Validate ATTACK section in config file
        """
        try:
            # Validate num of packets
            num_deauth_packets = int(self.current_config_section.get('num_deauth_packets').strip())
            self.context.validate_scan_times(num_deauth_packets,
                                             section='ATTACK',
                                             message="num_deauth_packets is not set to a valid number")
            self.context.num_deauth_packets = num_deauth_packets
            # Validate target list format and structure
            target_list = ast.literal_eval(self.current_config_section.get('target_ssid_list').strip())
            self.context.target_ssid_list = target_list
        except AttributeError:
            raise ConfigurationException(section='ATTACK', message="num_deauth_packets is not set to a valid number")
        except (SyntaxError, ValueError):
            raise ConfigurationException(section='ATTACK', message="target_list is not a valid list")
