### Modified version of EMG script used to play Chrome Dino Game
### https://docs.openbci.com/Examples/EMGProjects/EMG_Chrome_Dino_Game/
###
### This time, we will use EMG to play a free version of Pong!
### Found @ https://PeacePong.com
###
### Run this script using the following command:
### python3 OpenBCI_EMG_Controller_Ganglion_PyQt.py --serial-port /dev/cu.usbmodem11 --board-id 1
### Ganglion + WiFi command:
### python3 OpenBCI_EMG_Controller_Ganglion_PyQt.py --board-id 4 --ip-address 10.0.1.37 --ip-port 3000

import sys
import argparse
import time
from time import ctime
import numpy as np
import collections
import pyautogui
import pandas as pd
from typing import Any

import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, WindowFunctions

class BrainFlowObject(object):

    __instance = None

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance
    
    def __init__(self):
        self.time_to_play_game = True

        parser = argparse.ArgumentParser ()
        
        # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port
        parser.add_argument ('--timeout', type = int, help  = 'timeout for device discovery or connection', required = False, default = 0)
        parser.add_argument ('--ip-port', type = int, help  = 'ip port', required = False, default = 0)
        parser.add_argument ('--ip-protocol', type = int, help  = 'ip protocol, check IpProtocolType enum', required = False, default = 0)
        parser.add_argument ('--ip-address', type = str, help  = 'ip address', required = False, default = '')
        parser.add_argument ('--serial-port', type = str, help  = 'serial port', required = False, default = '')
        parser.add_argument ('--mac-address', type = str, help  = 'mac address', required = False, default = '')
        parser.add_argument ('--other-info', type = str, help  = 'other info', required = False, default = '')
        parser.add_argument ('--streamer-params', type = str, help  = 'streamer params', required = False, default = '')
        parser.add_argument ('--serial-number', type = str, help  = 'serial number', required = False, default = '')
        parser.add_argument ('--board-id', type = int, help  = 'board id, check docs to get a list of supported boards', required = True)
        parser.add_argument ('--log', action = 'store_true')
        args = parser.parse_args ()

        params = BrainFlowInputParams ()
        params.ip_port = args.ip_port
        params.serial_port = args.serial_port
        params.mac_address = args.mac_address
        params.other_info = args.other_info
        params.serial_number = args.serial_number
        params.ip_address = args.ip_address
        params.ip_protocol = args.ip_protocol
        params.timeout = args.timeout

        self.sampling_rate = BoardShim.get_sampling_rate (args.board_id)
        # 5 second window
        self.window = self.sampling_rate * 5
        # initialize calibration and time variables
        self.prev_time = int(round(time.time() * 1000))
        self.time_thres =  1000
        self.flex_thres = 0.8

        if (args.log):
            BoardShim.enable_dev_board_logger ()
        else:
            BoardShim.disable_board_logger ()

        self.board = BoardShim (args.board_id, params)
        print("Arguments have been parsed...")

        tries = 3
        for x in range(0, tries):
            try:
                print("Attempting to connect. Try #%d" % x)
                self.board.prepare_session ()
                break
            except brainflow.board_shim.BrainFlowError as e:
                print(e)
                print("Error attempting to connect. Trying again, up to %d times." % tries)
                if x == tries:
                    print("Unable to connect to board. :(")
                    sys.exit()
                time.sleep(3)

        print("Instantiated BrainFlow Board! Now streaming data from Board!")
        self.board.start_stream (45000)       

    def run(self):        
        # Do the magic and control key presses if user toggles the controls button
        if (self.time_to_play_game):
            data = self.board.get_current_board_data(self.window)
            # denoise data
            DataFilter.perform_rolling_filter (data[1], 2, AggOperations.MEAN.value)
            maximum = max(data[1])
            minimum = min(data[1])
            # normalize as many samples as needed
            norm_data = (data[1,(self.window-(int)(self.sampling_rate/2)):(self.window-1)] - minimum) / (maximum - minimum)
            # if enough time has gone by since the last flex
            do_action = (int(round(time.time() * 1000)) - self.time_thres) > self.prev_time
            if(do_action):
                # update time
                self.prev_time = int(round(time.time() * 1000))
                for element in norm_data:
                    if(element >= self.flex_thres):
                        ##pyautogui.press('up') # jump
                        print("Jump! - " + ctime(time.time()))
                        break
    
    def stop_session(self):
        print("Stopping data stream and ending session.")
        self.board.stop_stream ()
        self.board.release_session ()

def main ():
    brainflow_board = BrainFlowObject.get_instance()
    while True:
        brainflow_board.run()
    brainflow_board.stop_session()
    

if __name__ == "__main__":
    main()