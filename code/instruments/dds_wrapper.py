import math
import serial 
import time
import warnings




class DS_Instruments_DDS:


    #Manual for commands is hosted here as of 2023-02-19: https://www.dsinstruments.com/wp-content/uploads/2022/11/SG6000L-Command-List.pdf

    DS_INSTRUMENTS_SEND_EOL = "\n"
    DS_INSTRUMENTS_REPLY_EOL = "\r\n"
    DS_INSTRUMENTS_PORT_SETTINGS = {'baudrate':115200, 'bytesize':serial.EIGHTBITS, 'parity':serial.PARITY_NONE,
                                 'stopbits':serial.STOPBITS_ONE, 'timeout':1.0}
    DS_INSTRUMENTS_DELAY_TIME_SECS = 0.15



    def __init__(self, com_port, echo = False, confirm_throws_error = False, turnoff_at_exit = False, 
                revision_code = "modern"):
        #Default port settings for DS instruments DDS
        port_settings = DS_Instruments_DDS.DS_INSTRUMENTS_PORT_SETTINGS
        self.serial_port = serial.Serial(com_port, **port_settings)
        self.echo = echo 
        self.send_eol = DS_Instruments_DDS.DS_INSTRUMENTS_SEND_EOL
        self.reply_eol = DS_Instruments_DDS.DS_INSTRUMENTS_REPLY_EOL
        self.confirm_throws_error = confirm_throws_error
        self.turnoff_at_exit = turnoff_at_exit
        self.revision_code = revision_code


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.turnoff_at_exit:
            self.turn_output_off()
        self.serial_port.close()


    def ping_test(self):
        DS_INSTRUMENTS_PING_MSG = "*PING?"
        DS_INSTRUMENTS_EXPECTED_PONG_REPLY = b'PONG!\r\n'
        return self.send_and_get_reply(DS_INSTRUMENTS_PING_MSG) == DS_INSTRUMENTS_EXPECTED_PONG_REPLY

    def save_state(self):
        DS_INSTRUMENTS_SAVESTATE_MSG = "*SAVESTATE"
        self.send(DS_INSTRUMENTS_SAVESTATE_MSG)



    def set_name(self, name, confirm = False):
        DS_INSTRUMENTS_NAME_SET_BASESTRING = "*UNITNAME {0}"
        msg_string = DS_INSTRUMENTS_NAME_SET_BASESTRING.format(name) 
        self.send(msg_string) 
        if confirm:
            reply_name = self.get_name()
            if name != reply_name:
                error_string = "The stipulated name was {0}, but the DDS set name was {1}".format(name, reply_name)
                self._handle_confirm_error(error_string)

    def get_name(self):
        DS_INSTRUMENTS_NAME_CHECK_MSG = "*UNITNAME?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_NAME_CHECK_MSG)

        #Unused; documentation 
        DS_INSTRUMENTS_NAME_REPLY_FORMATTING = "{0}\r\n" 

        reply_string = reply_bytes.decode("ASCII") 
        name_string = reply_string.split("\r\n")[0] 
        return name_string



    def set_frequency_MHz(self, freq_in_MHz, confirm = False, ramp_to_setpoint = False, ramp_step_size_MHz = 1.0):
        DS_INSTRUMENTS_FREQUENCY_SET_BASESTRING = "FREQ:CW {0:f}MHz"
        if not ramp_to_setpoint:
            message_string = DS_INSTRUMENTS_FREQUENCY_SET_BASESTRING.format(freq_in_MHz)
            self.send(message_string)
        else:
            current_frequency_MHz = self.get_frequency_MHz()
            while abs(current_frequency_MHz - freq_in_MHz) > 1e-4:
                increment = math.copysign(min(ramp_step_size_MHz, abs(freq_in_MHz - current_frequency_MHz)), freq_in_MHz - current_frequency_MHz)
                temp_target_frequency_MHz = current_frequency_MHz + increment
                message_string = DS_INSTRUMENTS_FREQUENCY_SET_BASESTRING.format(temp_target_frequency_MHz)
                self.send(message_string)
                current_frequency_MHz += increment
        if confirm:
            reply_MHz = self.get_frequency_MHz() 
            if not abs(freq_in_MHz - reply_MHz) < 1e-4:
                error_string = "The stipulated frequency was {0:.4f} MHz, but the DDS set frequency was {1:.4f} MHz.".format(freq_in_MHz, reply_MHz)
                self._handle_confirm_error(error_string)


    def get_frequency_MHz(self):
        DS_INSTRUMENTS_FREQUENCY_CHECK_MSG = "FREQ:CW?"
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_FREQUENCY_CHECK_MSG, check_reply = True)


        if self.revision_code == "legacy":
            DS_INSTRUMENTS_FREQUENCY_REPLY_FORMATTING = "{0:4.5f}MHZ\r\n"
            reply_string = reply_bytes.decode("ASCII") 
            reply_MHz_string = reply_string.split("MHZ")[0] 
            reply_MHz = float(reply_MHz_string)
        elif self.revision_code == "modern":
            #Unused constant; documents formatting
            DS_INSTRUMENTS_FREQUENCY_REPLY_FORMATTING = "{0:d}HZ\r\n"
            reply_string = reply_bytes.decode("ASCII") 
            reply_Hz_string = reply_string.split("HZ")[0] 
            reply_Hz = float(reply_Hz_string) 
            reply_MHz = reply_Hz / 1e6
        return reply_MHz


    def set_power_dBm(self, power_val, confirm = False):
        DS_INSTRUMENTS_POWER_SET_BASESTRING = "POWER {0:f}"
        if not self.revision_code == "modern":
            raise NotImplementedError("Setting calibrated power in dBm not supported for non-modern DDS boxes.")
        message_string = DS_INSTRUMENTS_POWER_SET_BASESTRING.format(power_val)
        self.send(message_string) 
        if confirm:
            reply_power = self.get_power_dBm() 
            if not abs(power_val - reply_power) < 0.01:
                error_string = "The stipulated power was {0:.2f} dBm, but the DDS set power was {1:.2f} dBm.".format(power_val, reply_power)
                self._handle_confirm_error(error_string)


    def set_attenuation_dB(self, att_val, confirm = False):
        DS_INSTRUMENTS_ATTENUATION_SET_BASESTRING = "ATT {0:f}"
        if not self.revision_code == "legacy":
            raise NotImplementedError("Setting uncalibrated power attenuation is not supported for non-legacy DDS boxes")
        message_string = DS_INSTRUMENTS_ATTENUATION_SET_BASESTRING.format(att_val)
        self.send(message_string)
        if confirm:
            reply_attenuation = self.get_attenuation_dB()
            if not abs(att_val - reply_attenuation) < 0.01:
                error_string = "The stipulated attenuation was {0:.2f} dB, but the DDS set attenuation was {1:.2f} dB".format(att_val, reply_attenuation)
                self._handle_confirm_error(error_string)

    def turn_output_on(self, confirm = False):
        DS_INSTRUMENTS_OUTPUT_ON_STRING = "OUTP:STAT ON"
        self.send(DS_INSTRUMENTS_OUTPUT_ON_STRING)
        if confirm and (not self.is_output_on()):
            error_string = "The DDS output was set to be on, but is off."
            self._handle_confirm_error(error_string)


    def turn_output_off(self, confirm = False):
        DS_INSTRUMENTS_OUTPUT_OFF_STRING = "OUTP:STAT OFF"
        self.send(DS_INSTRUMENTS_OUTPUT_OFF_STRING)
        if confirm and self.is_output_on():
            error_string = "The DDS output was set to be off, but is on."
            self._handle_confirm_error(error_string)


    #Returns True if DDS output is on, false otherwise
    def is_output_on(self):
        DS_INSTRUMENTS_OUTPUT_CHECK_MSG = "OUTP:STAT?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_OUTPUT_CHECK_MSG)

        #Unused; documentation
        DS_INSTRUMENTS_OUTPUT_REPLY_FORMATTING = "{0}\r\n"
        DS_INSTRUMENTS_OUTPUT_OFF_STRING = "OFF"
        DS_INSTRUMENTS_OUTPUT_ON_STRING = "ON" 

        reply_string = reply_bytes.decode("ASCII") 
        if DS_INSTRUMENTS_OUTPUT_ON_STRING in reply_string:
            return True 
        elif DS_INSTRUMENTS_OUTPUT_OFF_STRING in reply_string:
            return False 
        else:
            raise RuntimeError("DDS response improper or missing.")


    def get_power_dBm(self):
        if not self.revision_code == "modern":
            raise NotImplementedError("Getting calibrated power in dBm not supported for non-modern DDS boxes.")
        DS_INSTRUMENTS_POWER_CHECK_MSG = "POWER?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_POWER_CHECK_MSG, check_reply = True) 

        #Unused; documentation 
        DS_INSTRUMENTS_POWER_REPLY_FORMATTING = "{0:+.1f}dBm\r\n"

        reply_string = reply_bytes.decode("ASCII") 
        reply_dBm_string = reply_string.split("dBm")[0] 
        reply_dBm = float(reply_dBm_string) 
        return reply_dBm
    
    def get_attenuation_dB(self):
        if not self.revision_code == "legacy":
            raise NotImplementedError("Getting uncalibrated power attenuation in dB not supported for non-legacy DDS boxes.") 
        DS_INSTRUMENTS_ATT_CHECK_MSG = "ATT?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_ATT_CHECK_MSG, check_reply = True) 

        #Unused; documentation 
        DS_INSTRUMENTS_ATT_REPLY_FORMATTING = "{0:+.1f}\r\n"

        reply_string = reply_bytes.decode("ASCII")
        reply_att_string = reply_string.split(DS_Instruments_DDS.DS_INSTRUMENTS_REPLY_EOL)[0]
        reply_att_dB = float(reply_att_string)
        return reply_att_dB
    

    
    def enter_sweep_mode_scan(self, confirm = False):
        #TODO check if supported on legacy DDS
        DS_INSTRUMENTS_ENTER_SWEEP_SCAN_MSG = "SWE:MODE SCAN"
        self.send(DS_INSTRUMENTS_ENTER_SWEEP_SCAN_MSG)
        if confirm:
            reply_status = self.get_sweep_mode()
            if not reply_status == "SCAN":
                error_string = "Sweep mode status was '{0}' instead of 'SCAN'".format(reply_status)
                self._handle_confirm_error(error_string)

    def enter_sweep_mode_list(self, confirm = False):
        #TODO check if supported on legacy DDS
        DS_INSTRUMENTS_ENTER_SWEEP_LIST_MSG = "SWE:MODE LIST"
        self.send(DS_INSTRUMENTS_ENTER_SWEEP_LIST_MSG)
        if confirm:
            reply_status = self.get_sweep_mode()
            if not reply_status == "LIST":
                error_string = "Sweep mode status was '{0}' instead of 'LIST'".format(reply_status)
                self._handle_confirm_error(error_string)

    def exit_sweep_mode(self, confirm = False):
        #TODO check if supported on legacy DDS
        DS_INSTRUMENTS_EXIT_SWEEP_MSG = "SWE:MODE OFF"
        self.send(DS_INSTRUMENTS_EXIT_SWEEP_MSG)
        if confirm:
            reply_status = self.get_sweep_mode()
            if not reply_status == "OFF":
                error_string = "Sweep mode status was '{0}' instead of 'OFF'".format(reply_status)
                self._handle_confirm_error(error_string)

    def get_sweep_mode(self):
        DS_INSTRUMENTS_SWEEP_CHECK_MSG = "SWE:MODE?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_SWEEP_CHECK_MSG, check_reply = True)
        #Unused, documentation
        DS_INSTRUMENTS_SWEEP_REPLY_FORMATTING = "{0}\r\n" 
        reply_string = reply_bytes.decode("ASCII") 
        reply_sweep_status_string = reply_string.split(DS_Instruments_DDS.DS_INSTRUMENTS_REPLY_EOL)[0]
        return reply_sweep_status_string


    def set_sweep_points(self, num_sweep_points, confirm = False):
        DS_INSTRUMENTS_SWEEP_POINTS_SET_BASESTRING = "SWE:POINTS {0:d}"
        message_string = DS_INSTRUMENTS_SWEEP_POINTS_SET_BASESTRING.format(num_sweep_points)
        self.send(message_string) 
        if confirm:
            reply_points = self.get_sweep_points() 
            if not reply_points == num_sweep_points:
                error_string = "The stipulated number of sweep points was {0:d}, but the set number was {1:d}".format(num_sweep_points, reply_points)
                self._handle_confirm_error(error_string)


    def get_sweep_points(self):
        DS_INSTRUMENTS_GET_SWEEP_POINTS_MSG = "SWE:POINTS?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_GET_SWEEP_POINTS_MSG, check_reply = True)
        #Unused, documentation
        DS_INSTRUMENTS_SWEEP_POINTS_REPLY_FORMATTING = "{0:d}\r\n" 
        reply_string = reply_bytes.decode("ASCII")
        reply_sweep_points_string = reply_string.split(DS_Instruments_DDS.DS_INSTRUMENTS_REPLY_EOL)[0]
        reply_sweep_points = int(reply_sweep_points_string)
        return reply_sweep_points

    def get_sweep_dwell_time_ms(self):
        DS_INSTRUMENTS_GET_SWEEP_DWELL_TIME_MSG = "SWE:DWELL?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_GET_SWEEP_DWELL_TIME_MSG, check_reply = True)
        #Unused, documentation
        DS_INSTRUMENTS_SWEEP_DWELL_TIME_REPLY_FORMATTING = "{0:d}\r\n" 
        reply_string = reply_bytes.decode("ASCII")
        reply_sweep_dwell_time_string = reply_string.split(DS_Instruments_DDS.DS_INSTRUMENTS_REPLY_EOL)[0]
        reply_sweep_dwell_time = int(reply_sweep_dwell_time_string)
        return reply_sweep_dwell_time

    def set_sweep_dwell_time_ms(self, dwell_time_ms, confirm = False):
        DS_INSTRUMENTS_SWEEP_POINTS_SET_BASESTRING = "SWE:DWELL {0:d}"
        message_string = DS_INSTRUMENTS_SWEEP_POINTS_SET_BASESTRING.format(dwell_time_ms)
        self.send(message_string) 
        if confirm:
            reply_dwell_time = self.get_sweep_dwell_time_ms() 
            if not reply_dwell_time == dwell_time_ms:
                error_string = "The stipulated dwell time was {0:d} ms, but the set dwell time was {1:d} ms".format(dwell_time_ms, reply_dwell_time)
                self._handle_confirm_error(error_string)

    def get_sweep_start_freq_MHz(self):
        DS_INSTRUMENTS_GET_SWEEP_START_FREQ_MSG = "FREQ:START?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_GET_SWEEP_START_FREQ_MSG, check_reply = True)
        #Unused, documentation
        DS_INSTRUMENTS_SWEEP_START_FREQ_REPLY_FORMATTING = "{0:d}HZ\r\n" 
        reply_string = reply_bytes.decode("ASCII")
        reply_sweep_start_frequency_Hz_string = reply_string.split('HZ')[0]
        reply_sweep_start_frequency_MHz_string = int(reply_sweep_start_frequency_Hz_string) / 1e6
        return reply_sweep_start_frequency_MHz_string

    def set_sweep_start_freq_MHz(self, start_freq_MHz, confirm = False):
        DS_INSTRUMENTS_SWEEP_START_FREQ_SET_BASESTRING = "FREQ:START {0:f}MHZ"
        message_string = DS_INSTRUMENTS_SWEEP_START_FREQ_SET_BASESTRING.format(start_freq_MHz)
        self.send(message_string) 
        if confirm:
            reply_sweep_start_freq_MHz = self.get_sweep_start_freq_MHz() 
            if not reply_sweep_start_freq_MHz == start_freq_MHz:
                error_string = "The stipulated start freq was {0:f} MHz, but the set start freq was {1:f} ms".format(start_freq_MHz, reply_sweep_start_freq_MHz)
                self._handle_confirm_error(error_string)

    def get_sweep_stop_freq_MHz(self):
        DS_INSTRUMENTS_GET_SWEEP_STOP_FREQ_MSG = "FREQ:STOP?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_GET_SWEEP_STOP_FREQ_MSG, check_reply = True)
        #Unused, documentation
        DS_INSTRUMENTS_SWEEP_STOP_FREQ_REPLY_FORMATTING = "{0:d}HZ\r\n" 
        reply_string = reply_bytes.decode("ASCII")
        reply_sweep_stop_frequency_Hz_string = reply_string.split('HZ')[0]
        reply_sweep_stop_frequency_MHz_string = int(reply_sweep_stop_frequency_Hz_string) / 1e6
        return reply_sweep_stop_frequency_MHz_string

    def set_sweep_stop_freq_MHz(self, stop_freq_MHz, confirm = False):
        DS_INSTRUMENTS_SWEEP_STOP_FREQ_SET_BASESTRING = "FREQ:STOP {0:f}MHZ"
        message_string = DS_INSTRUMENTS_SWEEP_STOP_FREQ_SET_BASESTRING.format(stop_freq_MHz)
        self.send(message_string) 
        if confirm:
            reply_sweep_stop_freq_MHz = self.get_sweep_stop_freq_MHz() 
            if not reply_sweep_stop_freq_MHz == stop_freq_MHz:
                error_string = "The stipulated stop freq was {0:f} MHz, but the set stop freq was {1:f} ms".format(stop_freq_MHz, reply_sweep_stop_freq_MHz)
                self._handle_confirm_error(error_string)

    def get_is_sweep_repeating(self):
        DS_INSTRUMENTS_GET_CONTINUOUS_REPETITION_MSG = "INIT:CONT?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_GET_CONTINUOUS_REPETITION_MSG, check_reply = True)
        #Unused, documentation
        DS_INSTRUMENTS_SWEEP_STOP_FREQ_REPLY_FORMATTING = "{0:d}\r\n" 
        reply_string = reply_bytes.decode("ASCII")
        reply_repetition_code_string = reply_string.split('\r\n')[0]
        is_repeating = (reply_repetition_code_string == 1)
        return is_repeating

    def set_is_sweep_repeating(self, is_repeating, confirm = False):
        DS_INSTRUMENTS_SWEEP_REPETITION_BASESTRING = "INIT:CONT {0:d}"
        if is_repeating: 
            repetition_code = 1
        else:
            repetition_code = 0 
        message_string = DS_INSTRUMENTS_SWEEP_REPETITION_BASESTRING.format(repetition_code)
        self.send(message_string)
        if confirm:
            reply_is_repeating = self.get_is_sweep_repeating()
            if not reply_is_repeating == is_repeating:
                error_string = "The stipulated sweep repetition status was {0}, but the set status was {1}".format(is_repeating, reply_is_repeating)
                self._handle_confirm_error(error_string)


    def get_is_sweep_active(self):
        DS_INSTRUMENTS_GET_SWEEP_ACTIVE_MESSAGE = "SWE:ACTIVE?"
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_GET_SWEEP_ACTIVE_MESSAGE, check_reply = True)
        DS_INSTRUMENTS_SWEEP_ACTIVE_REPLY_FORMATTING = "{0:d}\r\n" 
        reply_string = reply_bytes.decode("ASCII")
        reply_sweep_active_code_string = reply_string.split('\r\n')[0]
        is_active = (reply_sweep_active_code_string == 1)
        return is_active

    def trigger_sweep(self):
        DS_INSTRUMENTS_TRIGGER_MESSAGE = "INIT:IMM"
        self.send(DS_INSTRUMENTS_TRIGGER_MESSAGE)

    def set_stepwise_trigger(self):
        DS_INSTRUMENTS_STEPWISE_TRIGGER_MESSAGE = "TRIG:STEP"
        self.send(DS_INSTRUMENTS_STEPWISE_TRIGGER_MESSAGE)

    
    def set_full_sweep_trigger(self):
        DS_INSTRUMENTS_FULL_SWEEP_TRIGGER_MESSAGE = "TRIG:SWEEP"
        self.send(DS_INSTRUMENTS_FULL_SWEEP_TRIGGER_MESSAGE)

    def abort_sweep(self):
        DS_INSTRUMENTS_ABORT_SWEEP_MESSAGE = "ABORT" 
        self.send(DS_INSTRUMENTS_ABORT_SWEEP_MESSAGE)


    def send(self, msg):
        terminated_msg = msg + self.send_eol
        self.serial_port.write(terminated_msg.encode("ASCII"))
        self.serial_port.flush()
        time.sleep(DS_Instruments_DDS.DS_INSTRUMENTS_DELAY_TIME_SECS)
        if self.echo:
            print("Sent msg: {0}".format(msg))
    
    def send_and_get_reply(self, msg, check_reply = False):
        self.send(msg)
        received_bytes = self.serial_port.read_until(self.reply_eol.encode("ASCII"))
        self.serial_port.reset_input_buffer()
        if self.echo:
            print("Received reply: {0}".format(received_bytes))
        received_string = received_bytes.decode("ASCII") 
        if check_reply and not "\r\n" in received_string:
            raise RuntimeError("DDS reply is missing or appears to be incorrectly formatted.")
        return received_bytes
    

    def _handle_confirm_error(self, error_string):
        if self.confirm_throws_error:
            raise RuntimeError(error_string) 
        else:
            warnings.warn(error_string)




