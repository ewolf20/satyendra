import tkinter as tk
from tkinter import *
from tkinter import ttk
from turtle import color
import re
import image_saver_script as saver
import datetime
import importlib.resources as pkg_resources
import json
import shutil
import sys 
import os 
import warnings
from threading import Thread
import time


path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

from satyendra.code.image_watchdog import ImageWatchdog

IMAGE_EXTENSION = ".fits"

SPECIAL_CHARACTERS = "!@#$%^&*()-+?_=,<>/"

class BEC1_Portal():
    def __init__(self, master):
        self.othello_frame = Frame(master)
        self.othello_frame.pack() 

        tabControl = ttk.Notebook(master)
        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)
  
        tabControl.add(tab1, text ='Image Saver Control')
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
 
        # second tab 
        ttk.Label(tab2, text ="BLAH").grid(column = 0, row = 0, padx = 30, pady = 30)

        # third tab
        ttk.Label(tab3, text ="BLAH").grid(column = 0, row = 0, padx = 30, pady = 30)

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


def main():
    root = Tk()
    root.title('BEC1 Image Saver')
    root.geometry("600x150")
    BEC1_exp_portal = BEC1_Portal(root)
    root.mainloop()

    return 

if __name__ == "__main__":
	main()