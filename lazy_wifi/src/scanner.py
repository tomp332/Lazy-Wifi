import glob
import os
import signal
from pathlib import Path
from subprocess import Popen, PIPE, CalledProcessError
from time import sleep

import pandas.errors
from alive_progress import alive_bar
from pandas import read_csv
from lazy_wifi.context_manager.context import Context
from lazy_wifi.class_exceptions.exceptions import LazyWifiException
from lazy_wifi.src.interfaces import Interfaces
from lazy_wifi.src.utils import print_error, print_status, print_module


class Scanner:
    def __init__(self, interface_handler: Interfaces, context: Context):
        self.context = context
        self.interface_handler = interface_handler
        self.networks_base_file_name = 'wifi_networks'
        self.networks_file_path = Path(self.context.data_directory, self.networks_base_file_name)
        self.networks_file = None
        self.networks_data_frame = None
        self.main_process = None

    def start_scan(self):
        """
            Starts a full wifi network scan and prints the  BSSID, ESSID and SIGNAL results
        """
        try:
            print_module(f"Starting scanning on interface: {self.context.main_interface.dev}")
            self.context.main_logger.info(f"Starting scanning on interface: {self.context.main_interface.dev}")
            self.interface_handler.kill_interrupting()
            self._scan_wrapper()
            self._scanning_progress_bar(self.context.recon_scan_time)
            self._load_scanned_networks()
            self._print_networks()
        except (KeyboardInterrupt, SystemExit, pandas.errors.EmptyDataError) as e:
            if e == pandas.errors.EmptyDataError:
                print_error("Wifi scanned failed, no access points were found")
            raise LazyWifiException

    def _scan_wrapper(self):
        """
            Creates and starts airodump-ng scan command
        """
        try:
            command = ['airodump-ng',
                       '-a',
                       '-w',
                       self.networks_file_path.as_posix(),
                       '--output-format',
                       'csv',
                       '--band',
                       'bag',
                       self.context.main_interface.dev]
            self.main_process = Popen(command, stdout=PIPE, preexec_fn=os.setsid)

        except CalledProcessError:
            print_error("Starting scan process")
            raise LazyWifiException

    def _load_scanned_networks(self):
        """
            Loads the csv file from airodump-ng to pandas data frame
        """
        try:
            # Send kill signal to airodump-ng scan process
            os.killpg(os.getpgid(self.main_process.pid), signal.SIGTERM)
            self.main_process.kill()
            # Process is still alive
            while self.main_process.poll() is None:
                sleep(2)
                os.kill(self.main_process.pid, signal.SIGTERM)
            sleep(2)
            self._search_for_prefix_networks_file()
            self.networks_data_frame = read_csv(self.networks_file, index_col='BSSID')
            self._edit_keys()
            self._remove_temp_files()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            raise LazyWifiException

    def _edit_keys(self):
        """
            Edit some column names and removes redundant NaN values
        """
        self.networks_data_frame.rename(columns={' ESSID': 'ESSID',
                                                 ' channel': 'CHANNEL',
                                                 ' Cipher': 'CIPHER',
                                                 ' Authentication': 'AUTHENTICATION',
                                                 ' Power': 'POWER',
                                                 }, inplace=True)
        # Clean NaN values
        self.networks_data_frame.replace("", float("NaN"), inplace=True)
        self.networks_data_frame.dropna(subset=['ESSID'], how='any', inplace=True)
        df_obj = self.networks_data_frame.select_dtypes(['object'])
        # Remove all extra spaces from ESSID
        self.networks_data_frame[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())

    def _remove_temp_files(self):
        """
            Cleans up after temp csv files created by airodump-ng
        """
        try:

            os.remove(self.networks_file)
        except PermissionError:
            print_error("Unable to remove temp wifi networks csv file")

    def _search_for_prefix_networks_file(self):
        """
            Get latest csv file created by airodump-ng, exits if there were no results
        """
        network_files = glob.glob(f'{self.context.data_directory.as_posix()}/{self.networks_base_file_name}*.csv')
        try:
            self.networks_file = max(network_files, key=os.path.getctime)
        except ValueError:
            print_error("Scan finished with no results")
            exit()

    def _print_networks(self):
        """
            Print relevant column results from data frame
        """
        print(self.networks_data_frame[['ESSID', 'CHANNEL', 'POWER']])
        print_status(f'Found {len(self.networks_data_frame.index)} clients')
        self.context.main_logger.info(f'Stopped scanning, found {len(self.networks_data_frame.index)} clients')

    @staticmethod
    def _scanning_progress_bar(limit: int = 30000):
        try:
            with alive_bar(limit * 1000) as bar:
                for _ in range(limit * 1000):
                    sleep(.001)
                    bar()
        except KeyboardInterrupt:
            pass
