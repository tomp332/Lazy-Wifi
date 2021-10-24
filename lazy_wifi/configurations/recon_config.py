from lazy_wifi.configurations.context import Context


class ReconConfig:
    def __init__(self, context: Context):
        self.context = context
        self.current_config_section = self.context.config['RECON']

    def setup(self):
        """
            Validate RECON section in config file
        """
        recon_scan_time = int(self.current_config_section.get('recon_scan_time'))
        self.context.validate_scan_times(recon_scan_time,
                                         section='RECON',
                                         message="recon_scan_time is not set to a valid number")
        self.context.recon_scan_time = recon_scan_time
