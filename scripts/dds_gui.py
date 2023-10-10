import sys
import tkinter as tk
from tkinter import ttk

import serial

PATH_TO_REPOSITORIES_FOLDER = "C:/Users/BEC1 Top/Repositories"
sys.path.insert(0, PATH_TO_REPOSITORIES_FOLDER)

from satyendra.code.instruments import dds_wrapper
from satyendra.code import loading_functions



#Hard-coded constants

#DDS Frequencies
DDS_DEFAULT_OFFSET = 142.5
DEFAULT_FREQ_SELECTION_DICT = {"Resonance":466.5, "Polrot_Box":490.5, "Polrot_Box_Exp":484.5, "Rapid_Ramp":389.75}


#DDS com address
DEFAULT_DDS_ADDRESS = "COM3"
DDS_REVISION_CODE = "legacy"

#DDS Scan Amount
DDS_SCAN_INCREMENT_MHZ = 1.0 

class DDS_GUI():

    def __init__(self, master):
        self.master = master
        self.dds = None
        initialize_button = tk.Button(self.master, text = "Initialize DDS", relief = "raised", width = 12, command = self.initialize_dds)
        initialize_button.pack()
        address_label = tk.Label(self.master, text = "DDS Address", width = 10)
        address_label.pack()
        address_entry_text = tk.StringVar()
        address_entry_text.set(DEFAULT_DDS_ADDRESS)
        self.dds_address_entry = tk.Entry(self.master, textvariable = address_entry_text, width = 10)
        self.dds_address_entry.pack()
        dds_offset_entry_text = tk.StringVar() 
        dds_offset_entry_text.set(str(DDS_DEFAULT_OFFSET))
        self.dds_offset_label = tk.Label(self.master, text = "DDS Offset (MHz)")
        self.dds_offset_label.pack()
        self.dds_offset_entry = tk.Entry(self.master, textvariable = dds_offset_entry_text, width = 25)
        self.dds_offset_entry.pack()
        self.selected_frequency_button_name = None
        self.selected_frequency = 0.0
        self.frequency_selection_button_dict = {}
        for freq_selection_name in DEFAULT_FREQ_SELECTION_DICT:
            new_button = tk.Button(self.master, text = freq_selection_name, relief = "raised", width = 12,
                            command = (lambda n=freq_selection_name: self.set_frequency_button_clicked(n)))
            self.frequency_selection_button_dict[freq_selection_name] = new_button
            new_button.pack()
        custom_freq_button = tk.Button(self.master, text = "Custom", relief = "raised", width = 12, command = self.custom_frequency_button_clicked)
        custom_freq_button.pack()
        self.frequency_selection_button_dict["Custom"] = custom_freq_button
        custom_freq_text = tk.StringVar() 
        custom_freq_text.set(str(1337.0))
        self.custom_freq_entry = tk.Entry(self.master, textvariable=custom_freq_text, width = 25)
        self.custom_freq_entry.pack()
        self.target_frequency_text = tk.StringVar()
        self.update_target_frequency_label()
        target_frequency_label = tk.Label(self.master, textvariable = self.target_frequency_text)
        target_frequency_label.pack()
        self.set_dds_button = tk.Button(self.master, text = "Set_DDS", relief = "raised", width = 12, command = self.set_dds)
        self.set_dds_button.pack()
        self.dds_status_text = tk.StringVar() 
        self.dds_status_text.set("Not Initialized")
        dds_status_label = tk.Label(self.master, textvariable = self.dds_status_text)
        dds_status_label.pack()


    def set_dds(self):
        dds_offset_val = float(self.dds_offset_entry.get())
        target_dds_frequency = self.selected_frequency + dds_offset_val
        try:
            self.dds.set_frequency_MHz(target_dds_frequency, confirm = True, ramp_to_setpoint = True, ramp_step_size_MHz = DDS_SCAN_INCREMENT_MHZ)
        except RuntimeError:
            self.dds_status_text.set("Freq setting error")
        else:
            loading_functions.update_central_experiment_parameters("hf_lock_setpoint", self.selected_frequency)
            self.dds_status_text.set("DDS frequency set at: {0:.3f} + {1:.3f} MHz".format(self.selected_frequency, dds_offset_val))


    
    def set_frequency_button_clicked(self, button_name):
        self.selected_frequency = DEFAULT_FREQ_SELECTION_DICT[button_name]
        self.update_target_frequency_label()
        self.selected_frequency_button_name = button_name
        self.set_mode_button_reliefs()

    def custom_frequency_button_clicked(self):
        self.selected_frequency_button_name = "Custom"
        try:
            self.selected_frequency = float(self.custom_freq_entry.get())
            self.update_target_frequency_label()
        except ValueError:
            self.target_frequency_text.set("Target frequency: Error")
        self.set_mode_button_reliefs()


    def initialize_dds(self):
        dds_address = self.dds_address_entry.get()
        try:
            self.dds = dds_wrapper.DS_Instruments_DDS(dds_address, confirm_throws_error = True, revision_code = DDS_REVISION_CODE)
            if self.dds.ping_test():
                #Unfortunately the ancient dds we use doesn't support output on checking
                self.dds.turn_output_on(confirm = False)
                self.dds_status_text.set("Initialized")
            else:
                self.dds_status_text.set("Not responding")
        except (serial.serialutil.SerialException, RuntimeError) as e:
            print(e)
            self.dds_status_text.set("Initialization Error")

    def update_target_frequency_label(self):
        self.target_frequency_text.set("Target Frequency: {0:.3f} MHz".format(self.selected_frequency))




    def set_mode_button_reliefs(self):
        for button_name in self.frequency_selection_button_dict:
            button = self.frequency_selection_button_dict[button_name]
            if not button_name == self.selected_frequency_button_name:
                button.config(relief = "raised")
            else:
                button.config(relief = "sunken")



    
        





def main():
    root = tk.Tk()
    root.title('BEC1 Image Browser')
    root.geometry("500x500")
    BEC1_exp_portal = DDS_GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()