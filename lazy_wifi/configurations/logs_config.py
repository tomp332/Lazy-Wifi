from pathlib import Path

from lazy_wifi.configurations.context import Context
from lazy_wifi.src.main_logger import MainLogger


class LogsConfig:

    def __init__(self, context: Context):
        self.context = context
        self.current_config_section = self.context.config['LOGS']

    def setup(self):
        """
            Validate LOGS section in config file
        """
        # Validate logs directory
        Path(self.context.logs_directory).mkdir(exist_ok=True, parents=True)
        self.context.log_level = self.current_config_section.get('log_level')
        self.context.main_logger = MainLogger(self.context).main_logger
        return self
