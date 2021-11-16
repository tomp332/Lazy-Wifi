import os
import subprocess
from shlex import split

import pyric
import pyric.pyw as pyw

from lazy_wifi.context_manager.context import Context
from lazy_wifi.src.utils import print_status, print_error


class Interfaces:

    def __init__(self, context: Context):
        self.context = context

    def create_and_validate_device(self, main_interface: str) -> pyw.Card:
        """
            Validates monitor mode availability for the interface specified

            :param main_interface: Interface name
            :return: pyw interface card for a newly created virtual device
        """
        available_interfaces = self._get_interfaces()
        for interface in available_interfaces:
            if interface == main_interface:
                self.context.main_interface = pyw.getcard(main_interface)
                self._switch_to_monitor_mode()
                self.context.main_logger.info(f"Finished setting up wifi interface {main_interface}")
                break
        return self.context.main_interface

    def _switch_to_monitor_mode(self):
        try:
            pyw.down(self.context.main_interface)
            pyw.modeset(self.context.main_interface, 'monitor')
            pyw.up(self.context.main_interface)
        except pyric.error:
            print_error("PermissionDenied, please run this project as root in order to control network interfaces")
            exit(1)

    def switch_to_managed_mode(self):
        pyw.down(self.context.main_interface)
        pyw.modeset(self.context.main_interface, 'managed')
        pyw.up(self.context.main_interface)
        print_status(f"Device {self.context.main_interface.dev} is back in managed mode")
        self.context.main_logger.info(msg=f"Device {self.context.main_interface.dev} is back in managed mode")

    def interfaces_cleanup(self):
        self.switch_to_managed_mode()
        self.restart_network_manager()

    @staticmethod
    def restart_network_manager():
        os.system('systemctl restart network-manager.service')

    @staticmethod
    def kill_interrupting():
        command = 'airmon-ng check kill'
        proc = subprocess.Popen(split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()

    @staticmethod
    def _get_interfaces() -> list:
        """
            Get all available wifi interfaces that are connected to host

            :return: Returns a list of available interfaces
        """
        available_interfaces = []
        wifi_interfaces = pyw.winterfaces()
        for interface in wifi_interfaces:
            device = pyw.getcard(interface)
            if 'monitor' in pyw.devmodes(device):
                available_interfaces.append(interface)
        return available_interfaces

    @staticmethod
    def change_channel(interface_handle: pyw.Card, channel: int):
        """
        Change interface channel
        """
        try:
            pyw.chset(interface_handle, int(channel), None)
        except (TypeError, OSError) as e:
            print_error(f"unable to change adapter {interface_handle.dev} channel to {channel}, {e}")
