from distutils.util import strtobool

from lazy_wifi.src.utils import print_error


class AWSConfig:
    def __init__(self, context):
        self.context = context
        self.current_config_section = self.context.config['AWS']

    def setup(self):
        """
        Validate AWS configurations
        """
        self.context.aws_secret_access_key = self.current_config_section.get('aws_secret_access_key')
        self.context.aws_access_key_id = self.current_config_section.get('aws_access_key_id')
        self.context.shut_down_on_finish = strtobool(self.current_config_section.get('shut_down_on_finish'))
        self.context.instance_id = self.current_config_section.get('instance_id')
        self.context.region = self.current_config_section.get('main_region_zone')
        if self.context.region \
                and self.context.instance_id \
                and self.context.aws_access_key_id \
                and self.context.aws_secret_access_key \
                and self.context.remote_username \
                and (self.context.private_key_path or self.context.remote_password):
            self.context.remote_machine_available = True
        else:
            print_error("Remote machine configuration not specified, continuing without")
            self.context.main_logger.info("Remote machine configuration not specified, continuing without")
