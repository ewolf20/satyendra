import serial 
import warnings




class DS_Instruments_DDS:


    #Manual for commands is hosted here as of 2023-02-19: https://www.dsinstruments.com/wp-content/uploads/2022/11/SG6000L-Command-List.pdf

    DS_INSTRUMENTS_SEND_EOL = "\n"
    DS_INSTRUMENTS_REPLY_EOL = "\r\n"
    DS_INSTRUMENTS_PORT_SETTINGS = {'baudrate':115200, 'bytesize':serial.EIGHTBITS, 'parity':serial.PARITY_NONE, 'stopbits':serial.STOPBITS_ONE, 'timeout':1.0}



    def __init__(self, com_port, echo = False, confirm_throws_error = False, turnoff_at_exit = False, 
                revision_code = "legacy"):
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
                if self.confirm_throws_error:
                    raise RuntimeError(error_string) 
                else:
                    warnings.warn(error_string)

    def get_name(self):
        DS_INSTRUMENTS_NAME_CHECK_MSG = "*UNITNAME?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_NAME_CHECK_MSG)

        #Unused; documentation 
        DS_INSTRUMENTS_NAME_REPLY_FORMATTING = "{0}\r\n" 

        reply_string = reply_bytes.decode("ASCII") 
        name_string = reply_string.split("\r\n")[0] 
        return name_string



    def set_frequency_MHz(self, freq_in_MHz, confirm = False):
        DS_INSTRUMENTS_FREQUENCY_SET_BASESTRING = "FREQ:CW {0:f}MHz"
        message_string = DS_INSTRUMENTS_FREQUENCY_SET_BASESTRING.format(freq_in_MHz)
        self.send(message_string)
        if confirm:
            reply_MHz = self.get_frequency_MHz() 
            if not abs(freq_in_MHz - reply_MHz) < 1e-4:
                error_string = "The stipulated frequency was {0:.4f} MHz, but the DDS set frequency was {1:.4f} MHz.".format(freq_in_MHz, reply_MHz)
                if self.confirm_throws_error:
                    raise RuntimeError(error_string)
                else:
                    warnings.warn(error_string)


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
        message_string = DS_INSTRUMENTS_POWER_SET_BASESTRING.format(power_val)
        self.send(message_string) 
        if confirm:
            reply_power = self.get_power_dBm() 
            if not abs(power_val - reply_power) < 0.01:
                error_string = "The stipulated power was {0:.2f} dBm, but the DDS set frequency was {1:.2f} dBm.".format(power_val, reply_power)
                if self.confirm_throws_error:
                    raise RuntimeError(error_string)
                else:
                    warnings.warn(error_string)


    def turn_output_on(self, confirm = False):
        DS_INSTRUMENTS_OUTPUT_ON_STRING = "OUTP:STAT ON"
        self.send(DS_INSTRUMENTS_OUTPUT_ON_STRING)
        if confirm and (not self.is_output_on()):
            error_string = "The DDS output was set to be on, but is off."
            if self.confirm_throws_error:
                raise RuntimeError(error_string) 
            else:
                warnings.warn(error_string)


    def turn_output_off(self, confirm = False):
        DS_INSTRUMENTS_OUTPUT_OFF_STRING = "OUTP:STAT OFF"
        self.send(DS_INSTRUMENTS_OUTPUT_OFF_STRING)
        if confirm and self.is_output_on():
            error_string = "The DDS output was set to be off, but is on."
            if self.confirm_throws_error:
                raise RuntimeError(error_string) 
            else:
                warnings.warn(error_string)


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
        DS_INSTRUMENTS_POWER_CHECK_MSG = "POWER?" 
        reply_bytes = self.send_and_get_reply(DS_INSTRUMENTS_POWER_CHECK_MSG, check_reply = True) 

        #Unused; documentation 
        DS_INSTRUMENTS_POWER_REPLY_FORMATTING = "{0:+.1f}dBm\r\n"

        reply_string = reply_bytes.decode("ASCII") 
        reply_dBm_string = reply_string.split("dBm")[0] 
        reply_dBm = float(reply_dBm_string) 
        return reply_dBm


    def send(self, msg):
        terminated_msg = msg + self.send_eol
        self.serial_port.write(terminated_msg.encode("ASCII"))
        self.serial_port.flush() 
        if self.echo:
            print("Sent msg: {0}".format(msg))
    
    def send_and_get_reply(self, msg, check_reply = False):
        self.send(msg)
        received_bytes = self.serial_port.read_until(self.reply_eol.encode("ASCII"))
        if self.echo:
            print("Received reply: {0}".format(received_bytes))
        received_string = received_bytes.decode("ASCII") 
        if check_reply and not "\r\n" in received_string:
            raise RuntimeError("DDS reply is missing or appears to be incorrectly formatted.")
        return received_bytes



