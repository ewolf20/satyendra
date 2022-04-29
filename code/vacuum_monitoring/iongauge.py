"""
Library to communicate with Agilent XGS-600 ion gauge controller through serial RS-232 communication.

Use a ***STRAIGHT THROUGH*** cable to connect to your PC. See manual: 
"""


import serial
import os
import time
import datetime

DEFAULT_ADDRESS = 0


class IonGauge:

    """Constructor.

    Args:
        COM_PORT: str, the string describing the COM port of the pump serial connection, e.g. 'COM7'
        gauge_label: str, a string describing the type of ion gauge. Currently unused, should be passed as 'xgs-600'
        wait_time: float, the wait time for a read after a send command
        sendwidget: Widget; ignore unless making a gui
        recvwidget: Widget; ignore unless making a gui
    """

    def __init__(self, COM_PORT, gauge_label, address=None, wait_time=0.1, sendwidget=None, recvwidget=None):
        # Default port settings for ion gauge
        PORT_SETTINGS = {'baudrate': 9600, 'bytesize': serial.EIGHTBITS,
                         'parity': serial.PARITY_NONE, 'stopbits': serial.STOPBITS_ONE, 'timeout': 1}
        self.serial_port = serial.Serial(COM_PORT, **PORT_SETTINGS)
        self.gauge_label = gauge_label
        self.wait_time = wait_time
        self.sendwidget = sendwidget
        self.recvwidget = recvwidget
        if(address is None):
            self.address = DEFAULT_ADDRESS
        else:
            self.address = address
        self.address_string = self.get_address_string()

    """Create address_string for constructing commands in init. """
    def get_address_string(self):
        address_string = hex(self.address)[2:]
        address_string = address_string.upper()
        if(self.address < 16):
            address_string = "0" + address_string
        return address_string

    """
    Sends an arbitrary command.

    Args: 
        command: str, the command to be sent to the ion pump
        add_checksum_and_end: Convenience. If True, the command string has a checksum and carriage return character 
        appended, following the initial tilde convention
    
    Returns:
        the return value of serial.write() 
    """

    def send(self, command):
        return_value = self.serial_port.write(bytes(command, encoding="ASCII"))
        self.serial_port.flush()
        time.sleep(self.wait_time)
        return return_value

    def send_and_get_response(self, command):
        self.send(command)
        return self.serial_port.read_until("\r".encode("ASCII"))

    """Turns on the filament, requires 10 seconds warmup time before making measurements."""
    def turn_on(self, filament_index = 1):
        if(filament_index == 1):
            on_cmd = '#{address}31I1\r'.format(
            address=self.address_string)
        elif(filament_index == 2):
            on_cmd = '#{address}33I1\r'.format(
            address=self.address_string)
        self.send_and_get_response(on_cmd)
        #TODO: Handle this better!
        # time.sleep(10)

    """Turns off the filament."""
    def turn_off(self):
        off_cmd = '#{address}30I1\r'.format(
            address=self.address_string)
        return self.send_and_get_response(off_cmd)

    """Returns the pressure in Torr as a float."""
    def measure_pressure(self):
        read_cmd = '#{address}02I1\r'.format(
            address=self.address_string)
        pressure_bytes = self.send_and_get_response(read_cmd)
        return self.parse_pressure_bytes(pressure_bytes)


    def toggle_and_measure_pressure(self, filament_index = 1, toggle_wait_time = 10.0):
        self.turn_on(filament_index) 
        time.sleep(toggle_wait_time)
        pressure_value = self.measure_pressure()
        self.turn_off(filament_index)
        return pressure_value

    def failsafe(self):
        self.turn_off() 
        return True



    @staticmethod
    def parse_pressure_bytes(pressure_bytes):
        pressure_string = pressure_bytes.decode("ASCII")
        if pressure_string != '?FF':
            # The XGS-600 sends ?FF as a response if the command or data is invalid, or if the command
            # length is incorrect. There is no response to a wrong address, or lack of termination
            # character.
            trimmed_pressure_string = pressure_string[1:-1]
            return float(trimmed_pressure_string)
        else:
            return -1