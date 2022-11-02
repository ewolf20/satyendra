import tkinter as tk
from tkinter import *
from tkinter import ttk
from turtle import color
from tkinter import filedialog
import re
import datetime
import importlib.resources as pkg_resources
import json
import shutil
import sys 
import os 
import warnings
from threading import Thread
import time

import image_saver_script as saver

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

from satyendra.code.image_watchdog import ImageWatchdog
from BEC1_Analysis.scripts import imaging_resonance_processing
from BEC1_Analysis.scripts import rf_spect_processing

IMAGE_EXTENSION = ".fits"

SPECIAL_CHARACTERS = "!@#$%^&*()-+?_=,<>/"

ALLOWED_RESONANCE_TYPES = ["12_AB", "12_BA",  "21_AB", "21_BA", 
                         "13_AB", "13_BA", "31_AB", "31_BA", 
                         "23_AB", "23_BA", "32_AB", "32_BA"]

RF_DIRECTIONS = [
    "1 to 2, Imaging 1 then 2",
    "1 to 2, Imaging 2 then 1",
    "2 to 1, Imaging 1 then 2",
    "2 to 1, Imaging 2 then 1",
    "1 to 3, Imaging 1 then 3",
    "1 to 3, Imaging 3 then 1",
    "3 to 1, Imaging 1 then 3",
    "3 to 1, Imaging 3 then 1",
    "2 to 3, Imaging 2 then 3",
    "2 to 3, Imaging 3 then 2",
    "3 to 2, Imaging 2 then 3",
    "3 to 2, Imaging 3 then 2"
]

class BEC1_Portal():
    def __init__(self, master):
        self.othello_frame = Frame(master)
        self.othello_frame.pack() 

        tabControl = ttk.Notebook(master)
        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)
  
        tabControl.add(tab1, text ='Image Saver')
        tabControl.add(tab2, text ='Imaging Resonance Processing')
        tabControl.add(tab3, text ='RF Spectroscopy')
        tabControl.pack(expand = 1, fill ="both")
  
        # first tab: for image_saver_script.py
        self.run_bttn = Button(tab1, text="Do it", relief="raised",  width=20, command= self.run_button)
        self.run_bttn.place(x=20,y=20)
        self.run_bttn["state"] = DISABLED

        self.dryrun_bttn = Button(tab1, text="Dry run", relief="raised", command= self.dryrun_toggle)
        self.dryrun_bttn.place(x=225, y=20)

        self.custom_bttn = Button(tab1, text="Custom ", relief="raised", command= self.custom_toggle)
        self.custom_bttn.place(x=300, y=20)

        self.is_dryrun = True
        self.dryrun_state_before = NORMAL
        self.custom_state_before = DISABLED
        self.folder_name_entry_state_before = DISABLED
        self.confirm_button_state_before = DISABLED

        self.folder_name_entry = Entry(tab1, width=30)
        self.folder_name_entry.place(x=380, y=23)

        self.folder_name_entry["state"] = DISABLED
        self.folder_name = 'dryrun'
        self.acquisition_state = "STOPPED"

        self.image_saver_status = Entry(tab1, text="Status: ", width=69)
        self.image_saver_status.place(x = 20, y = 80)
        self.status_bar = Label(tab1, text="Status: ").place(x=20, y = 55)

        self.confirm_bttn = Button(tab1, text="Confirm", command=self.confirm_button)
        self.confirm_bttn.place(x=450,y=76)
        self.confirm_bttn["state"] = DISABLED

        self.add_bttn = Button(tab1, text="Add", command=self.add_button)
        self.add_bttn.place(x=520,y=76)
        self.add_bttn["state"] = DISABLED
 
        # second tab: for image_resonance_processing.py
        ttk.Label(tab2, text ="BLAH").grid(column = 0, row = 0, padx = 30, pady = 30)
        self.browse_bttn = Button(tab2, text="Browse", relief="raised",  width=20, command= self.browse_button)
        self.browse_bttn.place(x=20,y=20)
        self.image_processing_folder_path = ''

        self.res_image_folder_entry = Entry(tab2, text="Resonance imaging folder name", width=55)
        self.res_image_folder_entry.place(x = 20, y = 80)
        self.res_image_folder_entry_label = Label(tab2, text="Resonance imaging folder: ").place(x=20, y = 55)

        self.resonance_imaging_mode = 'TopAB' # set to this by default

        self.side_lf_bttn = Button(tab2, text="Side LF", relief="raised",  width=7, command= self.side_lf)
        self.side_lf_bttn.place(x=200,y=20)
        self.side_lf_bttn["state"] = DISABLED

        self.side_hf_bttn = Button(tab2, text="Side HF", relief="raised",  width=7, command= self.side_hf)
        self.side_hf_bttn.place(x=275,y=20)
        self.side_hf_bttn["state"] = DISABLED

        self.TopA_bttn = Button(tab2, text="Top A", relief="raised",  width=7, command= self.TopA)
        self.TopA_bttn.place(x=350,y=20)
        self.TopA_bttn["state"] = DISABLED

        self.TopB_bttn = Button(tab2, text="Top B", relief="raised",  width=7, command= self.TopB)
        self.TopB_bttn.place(x=425,y=20)
        self.TopB_bttn["state"] = DISABLED

        self.TopAB_bttn = Button(tab2, text="Top AB", relief="raised",  width=7, command= self.TopAB)
        self.TopAB_bttn.place(x=500,y=20)
        self.TopAB_bttn["state"] = DISABLED

        self.analyze_bttn = Button(tab2, text="Analyze", relief="raised",  width=15, command= self.analyze_button)
        self.analyze_bttn.place(x=400,y=78)
        self.analyze_bttn["state"] = DISABLED

        # third tab
        self.browse_rf_bttn = Button(tab3, text="Browse", relief="raised",  width=20, command= self.browse_rf_button)
        self.browse_rf_bttn.place(x=20,y=20)
        self.rf_processing_folder_path = ''

        self.rf_spect_folder_entry = Entry(tab3, text="RF spectroscopy folder name", width=55)
        self.rf_spect_folder_entry.place(x = 20, y = 80)
        self.rf_spect_folder_entry_label = Label(tab3, text="RF spectroscopy folder: ").place(x=20, y = 55)

        self.rf_analyze_bttn = Button(tab3, text="Analyze", relief="raised",  width=15, command= self.rf_analyze_button)
        self.rf_analyze_bttn.place(x=400,y=78)
        self.rf_analyze_bttn["state"] = DISABLED

        self.RF_direction_label = Label(tab3, text="RF transfer: ").place(x=200, y=20)

        self.RF_direction = StringVar()
        self.RF_direction.set( "1 to 2, Imaging 1 then 2")
        self.RF_directions_menu = OptionMenu(tab3, self.RF_direction, *RF_DIRECTIONS, command = self.RF_imaging_options)
        self.RF_directions_menu.place(x = 270, y = 16)
        self.rf_resonance_key = self.RF_direction.get()

        self.Rabi_guess_var = StringVar()
        self.RF_center_guess_var = StringVar()

        self.Rabi_guess_label = Label(tab3, text= "Rabi frequency guess (kHz): ").place(x=450, y=20)
        self.RF_center_guess_label = Label(tab3, text= "RF center guess (MHz): ").place(x=450, y=40)

        self.Rabi_guess = Entry(tab3, textvariable = self.Rabi_guess_var, width=15).place(x=610,y=20)
        self.RF_center_guess = Entry(tab3, textvariable = self.RF_center_guess_var, width=15).place(x=610,y=40)

        self.rf_analyze_with_guess_bttn = Button(tab3, text="Analyze with guess", relief="raised",  width=15, command= self.rf_analyze_with_guess_button)
        self.rf_analyze_with_guess_bttn.place(x=550,y=78)
        self.rf_analyze_with_guess_bttn["state"] = DISABLED


    # TAB 1 functions:

    def confirm_button(self):
        
        self.folder_name = self.folder_name_entry.get()

        # check for duplicates and validity:
        if (saver.is_savefolder_name_forbidden(self.folder_name)) or (self.folder_name == "") or (self.folder_name == 'dryrun'):

            self.image_saver_status.delete(0,'end')
            self.image_saver_status.insert(0,"Invalid folder name!")
            if self.folder_name == 'dryrun':
                # reset status box:
                self.image_saver_status.delete(0,'end')
                self.image_saver_status.insert(0,"Click 'Dry run' to run a a dryrun...")
        
        else: # if all is GRAND...
            # check if folder name already exists:
            camera_saving_folder_pathname, saving_location_root_pathname, image_specification_list = saver.load_config()
            user_entered_name = self.folder_name
            is_dryrun = user_entered_name == "dryrun"
            savefolder_pathname = saver.initialize_savefolder_portal(saving_location_root_pathname, user_entered_name, is_dryrun)

            if (os.path.isdir(savefolder_pathname) and not is_dryrun):
                self.image_saver_status.delete(0,'end')
                self.image_saver_status.insert(0,"Folder already exists. Click 'Add' to add or try again.")
                self.add_bttn["state"] = NORMAL
            else:
                self.image_saver_status.delete(0,'end')
                self.image_saver_status.insert(0,"Folder OK. Click 'Do it' to run.")
                self.run_bttn["state"] = NORMAL

    def add_button(self):
        self.run_bttn["state"] = NORMAL
        self.add_bttn["state"] = DISABLED

        # reset status box:
        self.image_saver_status.delete(0,'end')
        self.image_saver_status.insert(0,"Adding to existing folder. 'Do it' to run, or try different folder name.")

    def dryrun_toggle(self):
        if self.dryrun_bttn.config('relief')[-1] == 'sunken':
            self.dryrun_bttn.config(relief="raised")
            self.dryrun_bttn.config(fg='black')
            self.custom_bttn["state"] = NORMAL
            self.folder_name_entry["state"] = DISABLED
            self.run_bttn["state"] = DISABLED
        else:
            self.dryrun_bttn.config(relief="sunken")  
            self.dryrun_bttn.config(fg='red')
            self.custom_bttn["state"] = DISABLED
            self.folder_name_entry["state"] = DISABLED
            self.run_bttn["state"] = NORMAL
            self.is_dryrun = True
            # reset status box:
            self.image_saver_status.delete(0,'end')
            self.image_saver_status.insert(0,"dryrun mode selected")

    def custom_toggle(self):
        if self.custom_bttn.config('relief')[-1] == 'sunken':
            self.custom_bttn.config(relief="raised")
            self.custom_bttn.config(fg='black')
            self.dryrun_bttn["state"] = NORMAL
            self.run_bttn["state"] = DISABLED
            self.folder_name_entry["state"] = DISABLED

            # disable confirm button
            self.confirm_bttn["state"] = DISABLED
        else:
            self.custom_bttn.config(relief="sunken")   
            self.custom_bttn.config(fg='red')
            self.dryrun_bttn["state"] = DISABLED
            
            self.is_dryrun = False
            self.folder_name_entry["state"] = NORMAL

            # enable confirm button:
            self.confirm_bttn["state"] = NORMAL


    def run_button(self):

        self.confirm_bttn["state"] = DISABLED
        self.add_bttn["state"] = DISABLED

        if self.run_bttn.config('relief')[-1] == 'sunken': # if RUNNING: this initiates STOP
            self.run_bttn.config(text='Do it')
            self.run_bttn.config(relief="raised")
            self.run_bttn.config(fg='black')

            self.run_bttn["state"] = DISABLED

            if self.is_dryrun:
                self.dryrun_bttn["state"] = DISABLED
                self.custom_bttn["state"] = NORMAL
                self.folder_name_entry["state"] = NORMAL
            else:
                self.dryrun_bttn["state"] = NORMAL
                self.custom_bttn["state"] = DISABLED
                self.folder_name_entry["state"] = DISABLED

            # returns button to original states
            self.dryrun_bttn["state"] = self.dryrun_state_before
            self.custom_bttn["state"] = self.custom_state_before
            self.folder_name_entry["state"] = self.folder_name_entry_state_before
            self.confirm_bttn["state"] = self.confirm_button_state_before
            # reset status box:
            self.image_saver_status.delete(0,'end')
            self.image_saver_status.insert(0,"Done")

            self.acquisition_state = "STOPPED"

        elif (self.dryrun_bttn["state"] == DISABLED and self.custom_bttn["state"] == NORMAL) or (self.dryrun_bttn["state"] == NORMAL and self.custom_bttn["state"] == DISABLED):

            # gathers button states before RUN:
            if self.dryrun_bttn["state"] == DISABLED:
                # means that we're running in custom mode
                self.dryrun_state_before = DISABLED 
                self.custom_state_before = NORMAL 
                self.confirm_button_state_before = NORMAL
                self.folder_name_entry_state_before = NORMAL

                # proceed if folder name is valid
                if not(saver.is_savefolder_name_forbidden(self.folder_name)) and not(self.folder_name == "") and not(self.folder_name == 'dryrun'):

                    self.run_bttn.config(relief="sunken")  
                    self.run_bttn.config(text='STOP')
                    self.run_bttn.config(fg='red')
                    # once running, disable other buttons
                    self.dryrun_bttn["state"] = DISABLED
                    self.custom_bttn["state"] = DISABLED
                    self.folder_name_entry["state"] = DISABLED

                    self.image_saver_status.delete(0, 'end')
                    self.image_saver_status.insert(0,"Saving into custom folder")

                    # run acquisition: custom
                    self.acquisition_state = "RUNNING"
                    t = Thread (target = self.acquire)
                    t.start()

                else:
                    # reset status box:
                    self.image_saver_status.delete(0,'end')
                    self.image_saver_status.insert(0,"Invalid folder name!")
                    if self.folder_name == 'dryrun':
                        # reset status box:
                        self.image_saver_status.delete(0,'end')
                        self.image_saver_status.insert(0,"Click 'Dry run' to run a a dryrun...")

            else:
                # means that we're running in dryrun mode
                self.dryrun_state_before = NORMAL 
                self.custom_state_before = DISABLED 
                self.folder_name_entry_state_before = DISABLED
                self.confirm_button_state_before = DISABLED
                

                self.run_bttn.config(relief="sunken")  
                self.run_bttn.config(text='STOP')
                self.run_bttn.config(fg='red')
                # once running, disable other buttons
                self.dryrun_bttn["state"] = DISABLED
                self.custom_bttn["state"] = DISABLED
                self.folder_name_entry["state"] = DISABLED

                self.image_saver_status.delete(0, 'end')
                self.image_saver_status.insert(0,"Saving into dryrun")    
                self.folder_name = 'dryrun'   

                # run acquisition: dryrun
                self.acquisition_state = "RUNNING"
                t = Thread (target = self.acquire)
                t.start()

                
    def acquire(self):
        camera_saving_folder_pathname, saving_location_root_pathname, image_specification_list = saver.load_config()
        user_entered_name = self.folder_name
        is_dryrun = user_entered_name == "dryrun"
        savefolder_pathname = saver.initialize_savefolder_portal(saving_location_root_pathname, user_entered_name, is_dryrun)

        if is_dryrun:
            print("Running as a dry run. WARNING: All images will be deleted on termination.\n")

        print("Initializing watchdog...\n")
        my_watchdog = ImageWatchdog(camera_saving_folder_pathname, savefolder_pathname, image_specification_list, image_extension = IMAGE_EXTENSION)
        print("Running!") 

        while True:
            # main while loop goes here
            image_saved = my_watchdog.associate_images_with_run()
            if(image_saved):
                print("Saved something at: ") 
                t = datetime.datetime.now().strftime("%H-%M-%S")
                print(t)
                status_string =  'Saved to: ' + self.folder_name + ', at ' + t
                # reset status box:
                self.image_saver_status.delete(0,'end')
                self.image_saver_status.insert(0, status_string)
                
            if self.acquisition_state == "STOPPED":   
                # reset status box:
                self.image_saver_status.delete(0,'end')
                self.image_saver_status.insert(0,"Saving last image...")
                print("Trying to save the last images...") 
                my_watchdog.associate_images_with_run() 
                my_watchdog.save_run_parameters()
                print("Success!") 

                time.sleep(1)
                # reset status box:
                self.image_saver_status.delete(0,'end')
                self.image_saver_status.insert(0,"Success!")

                if (is_dryrun):
                    saver.nuke_savefolder(savefolder_pathname)
                break  

    # TAB 2 functions:

    def enable_resonance_imaging_mode_buttons(self):
        # enable buttons:
        self.side_lf_bttn["state"] = NORMAL
        self.side_hf_bttn["state"] = NORMAL
        self.TopA_bttn["state"] = NORMAL
        self.TopB_bttn["state"] = NORMAL
        self.TopAB_bttn["state"] = NORMAL
        self.analyze_bttn["state"] = DISABLED
        
    def browse_button(self):
        self.image_processing_folder_path = filedialog.askdirectory()
        if self.image_processing_folder_path:
            self.res_image_folder_entry.delete(0,'end')
            self.res_image_folder_entry.insert(0, self.image_processing_folder_path)
            # print(self.image_processing_folder_path)
        self.enable_resonance_imaging_mode_buttons()

    def side_lf(self):
        if self.side_lf_bttn.config('relief')[-1] == 'sunken':
            self.side_lf_bttn.config(relief="raised")
            self.side_lf_bttn.config(fg='black')
            
            self.enable_resonance_imaging_mode_buttons()
        else:
            self.side_lf_bttn.config(relief="sunken")  
            self.side_lf_bttn.config(fg='red')
            self.resonance_imaging_mode = 'Side_lf'
            # enable buttons:
            self.side_hf_bttn["state"] = DISABLED
            self.TopA_bttn["state"] = DISABLED
            self.TopB_bttn["state"] = DISABLED
            self.TopAB_bttn["state"] = DISABLED
            self.analyze_bttn["state"] = NORMAL

    def side_hf(self):
        if self.side_hf_bttn.config('relief')[-1] == 'sunken':
            self.side_hf_bttn.config(relief="raised")
            self.side_hf_bttn.config(fg='black')
            
            self.enable_resonance_imaging_mode_buttons()
        else:
            self.side_hf_bttn.config(relief="sunken")  
            self.side_hf_bttn.config(fg='red')
            self.resonance_imaging_mode = 'Side_hf'
            # enable buttons:
            self.side_lf_bttn["state"] = DISABLED
            self.TopA_bttn["state"] = DISABLED
            self.TopB_bttn["state"] = DISABLED
            self.TopAB_bttn["state"] = DISABLED

            self.analyze_bttn["state"] = NORMAL

    def TopA(self):
        if self.TopA_bttn.config('relief')[-1] == 'sunken':
            self.TopA_bttn.config(relief="raised")
            self.TopA_bttn.config(fg='black')
            
            self.enable_resonance_imaging_mode_buttons()
        else:
            self.TopA_bttn.config(relief="sunken")  
            self.TopA_bttn.config(fg='red')
            self.resonance_imaging_mode = 'TopA'
            # enable buttons:
            self.side_lf_bttn["state"] = DISABLED
            self.side_hf_bttn["state"] = DISABLED
            self.TopB_bttn["state"] = DISABLED
            self.TopAB_bttn["state"] = DISABLED

            self.analyze_bttn["state"] = NORMAL

    def TopB(self):
        if self.TopB_bttn.config('relief')[-1] == 'sunken':
            self.TopB_bttn.config(relief="raised")
            self.TopB_bttn.config(fg='black')
            
            self.enable_resonance_imaging_mode_buttons()
        else:
            self.TopB_bttn.config(relief="sunken")  
            self.TopB_bttn.config(fg='red')
            self.resonance_imaging_mode ='TopB'
            # enable buttons:
            self.side_hf_bttn["state"] = DISABLED
            self.side_lf_bttn["state"] = DISABLED
            self.TopA_bttn["state"] = DISABLED
            self.TopAB_bttn["state"] = DISABLED

            self.analyze_bttn["state"] = NORMAL

    def TopAB(self):
        if self.TopAB_bttn.config('relief')[-1] == 'sunken':
            self.TopAB_bttn.config(relief="raised")
            self.TopAB_bttn.config(fg='black')
            
            self.enable_resonance_imaging_mode_buttons()
        else:
            self.TopAB_bttn.config(relief="sunken")  
            self.TopAB_bttn.config(fg='red')
            self.resonance_imaging_mode = 'TopAB'
            # enable buttons:
            self.side_hf_bttn["state"] = DISABLED
            self.TopA_bttn["state"] = DISABLED
            self.TopB_bttn["state"] = DISABLED
            self.side_lf_bttn["state"] = DISABLED

            self.analyze_bttn["state"] = NORMAL

    def analyze_button(self):
        # print(self.resonance_imaging_mode)

        self.analyze_bttn["state"] = DISABLED

        measurement_directory_path = self.image_processing_folder_path
        imaging_mode_string = self.resonance_imaging_mode

        # talk to imaging_resonance_processing
        imaging_resonance_processing.main_after_inputs(measurement_directory_path,imaging_mode_string)
    
    # TAB 3 functions:

    def browse_rf_button(self):
        self.rf_processing_folder_path = filedialog.askdirectory()
        if self.rf_processing_folder_path:
            self.rf_spect_folder_entry.delete(0,'end')
            self.rf_spect_folder_entry.insert(0, self.rf_processing_folder_path)
            # print(self.rf_processing_folder_path)
            self.rf_analyze_bttn["state"] = NORMAL
            self.rf_analyze_with_guess_bttn["state"] = NORMAL

    def rf_analyze_button(self):        
        rf_spect_processing.main_after_inputs(self.rf_processing_folder_path, self.rf_resonance_key)

    def rf_analyze_with_guess_button(self):        
        # need add guesses here
        Rabi_guess = self.Rabi_guess_var.get()
        RF_center_guess = self.RF_center_guess_var.get()

        print(Rabi_guess)
        print(RF_center_guess)

        if Rabi_guess == '':
            Rabi_guess = None
        if RF_center_guess == '':
            RF_center_guess = None

        rf_spect_processing.main_after_inputs(self.rf_processing_folder_path, self.rf_resonance_key, RF_center_guess, Rabi_guess)

    def RF_imaging_options(self, event):
        RF_direction = self.RF_direction.get()

        for i in range(0,len(RF_DIRECTIONS)):
            if RF_direction == RF_DIRECTIONS[i]:
                self.rf_resonance_key = ALLOWED_RESONANCE_TYPES[i]

        print(self.rf_resonance_key)

    def RF_center_guess_set(self):
        print('hello')

    def Rabi_guess_set(self):
        print('hello')
            

def main():
    root = Tk()
    root.title('BEC1 Image Saver')
    root.geometry("725x150")
    BEC1_exp_portal = BEC1_Portal(root)
    root.mainloop()

    return 

if __name__ == "__main__":
	main()