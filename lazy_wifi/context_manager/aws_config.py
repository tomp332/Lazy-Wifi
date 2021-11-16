from distutils.util import strtobool

from lazy_wifi.src.utils import print_status


class AWSConfig:
    def __init__(self, context):
        self.context = context
        self.current_config_section = self.context.config['AWS']

    def setup(self):
        """
        Validate AWS configurations
        """
        self.context.aws_secret_access_key = self.current_config_section.get('aws_secret_access_key').strip()
        self.context.aws_access_key_id = self.current_config_section.get('aws_access_key_id').strip()
        self.context.shut_down_on_finish = strtobool(self.current_config_section.get('shut_down_on_finish'))
        self.context.instance_id = self.current_config_section.get('instance_id').strip()
        self.context.region = self.current_config_section.get('main_region_zone').strip()
        self.validate_aws_machine()

    def validate_aws_machine(self):
        if self.context.region \
                and self.context.instance_id \
                and self.context.aws_access_key_id \
                and self.context.aws_secret_access_key \
                and self.context.remote_username \
                and (self.context.private_key_path or self.context.remote_password):
            self.context.remote_machine_is_aws = True
        else:
            self.context.main_logger.info("AWS configuration error, continuing without")
