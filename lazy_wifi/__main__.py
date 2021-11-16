from lazy_wifi.src.aws_handler import AWSHandler
from lazy_wifi.context_manager.context import ConfigurationException
from lazy_wifi.context_manager.context_manager import ContextManager
from lazy_wifi.class_exceptions.exceptions import LazyWifiException
from lazy_wifi.src.handshake_manager import HandshakeManager
from lazy_wifi.src.interfaces import Interfaces
from lazy_wifi.src.remote_connection import RemoteConnection
from lazy_wifi.src.scanner import Scanner
from lazy_wifi.src.utils import print_status


class LazyWifi:
    def __init__(self):
        self.context = ContextManager().setup()
        self.interface = Interfaces(self.context)
        self.wifi_recon = Scanner(self.interface, self.context)
        self.handshake_manager = None
        self.aws = None

        # If ec2 was configured, initialize the instance and the connection
        if self.context.remote_machine_is_aws:
            self.aws = AWSHandler(self.context)
            self.remote_connection = RemoteConnection(self.context)
        elif self.context.remote_machine_available:
            self.remote_connection = RemoteConnection(self.context)

    def start_app(self):
        try:
            self.wifi_recon.start_scan()
            if self.wifi_recon:
                self.handshake_manager = HandshakeManager(self.wifi_recon.networks_data_frame, self.context)
                self.handshake_manager.gather_handshakes()
                self.cleanup()
        except (KeyboardInterrupt, LazyWifiException):
            self.cleanup()

    def cleanup(self):
        print_status("Exiting..")
        self.interface.interfaces_cleanup()
        if self.aws:
            self.aws.aws_handler_cleanup()


if __name__ == "__main__":
    lazy_wifi = None
    try:
        lazy_wifi = LazyWifi()
        lazy_wifi.start_app()
    except (KeyboardInterrupt, ConfigurationException, LazyWifiException) as e:
        lazy_wifi and lazy_wifi.cleanup()
