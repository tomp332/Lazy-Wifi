from lazy_wifi.context_manager.attack_config import AttackConfig
from lazy_wifi.context_manager.aws_config import AWSConfig
from lazy_wifi.context_manager.basic_config import BasicConfig
from lazy_wifi.context_manager.context import Context
from lazy_wifi.context_manager.handshakes_config import HandshakesConfig
from lazy_wifi.context_manager.logs_config import LogsConfig
from lazy_wifi.context_manager.recon_config import ReconConfig
from lazy_wifi.context_manager.remote_connection_config import RemoteConnectionConfig
from lazy_wifi.class_exceptions.exceptions import ConfigurationException
from lazy_wifi.src.utils import print_error


class ContextManager:
    def __init__(self):
        # Init for Context class
        self.context = Context()

    def setup(self):
        """
        Handles all validation classes for each configuration section in config.ini
        """
        try:
            LogsConfig(self.context).setup()
            BasicConfig(self.context).setup()
            ReconConfig(self.context).setup()
            AttackConfig(self.context).setup()
            HandshakesConfig(self.context).setup()
            RemoteConnectionConfig(self.context).setup()
            AWSConfig(self.context).setup()
            # Return a configured and initialized Context class object
            return self.context
        except ConfigurationException as e:
            print_error(e.message)
            exit(1)
