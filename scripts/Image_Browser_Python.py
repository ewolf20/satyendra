# Huan Q Bui
# BEC1@MIT
# First updated: Dec 2022
# Last updated: Jan 31, 2023 @ 04:06 pm

import tkinter as tk
from tkinter import *
from tkinter import ttk
from turtle import color
import re
from tkinter import filedialog
import datetime
import importlib.resources as pkg_resources
import json
import shutil
import sys 
import os 
import warnings
import glob
from xml.etree.ElementTree import tostring
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.widgets import RectangleSelector
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from astropy.io import fits
import numpy as np
from threading import Thread
import threading
import time
import logging
import pickle
# from vimba import Vimba, VimbaCameraError, VimbaFeatureError, PixelFormat
# import cv2
from PIL import Image, ImageTk
from queue import SimpleQueue

logger = logging.getLogger(__name__)
path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

import image_saver_script as saver
from satyendra.code.image_watchdog import ImageWatchdog
from satyendra.code import loading_functions as satyendra_loading_functions
from BEC1_Analysis.scripts import imaging_resonance_processing, rf_spect_processing, hybrid_top_processing
from BEC1_Analysis.code import measurement, analysis_functions
# m = measurement.Measurement(...)


IMAGE_EXTENSION = ".fits"
ABSORPTION_LIMIT = 5.0
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

LIVE_FIGURES = ['Figure 1','Figure 2','Figure 3','Figure 4']

MEASURE_QUANTITIES = ['Pixel sum side', 
                        'Pixel sum Top A', 
                        'Pixel sum Top B', 
                        'Pixel sum Top AB', 
                        'Counts Side LF', 
                        'Counts Side HF', 
                        'Counts Top A (abs)', 
                        'Counts Top B (abs)', 
                        #'Counts Top AB (abs)', 
                        'Counts Top A (PR)',
                        'Counts Top B (PR)'
                        ]

ANALYSIS_FUNCTIONS = [analysis_functions.get_od_pixel_sum_side,
                        analysis_functions.get_od_pixel_sum_top_A,
                        analysis_functions.get_od_pixel_sum_top_B,
                        analysis_functions.get_od_pixel_sums_top_double,
                        analysis_functions.get_atom_count_side_li_lf,
                        analysis_functions.get_atom_count_side_li_hf,
                        analysis_functions.get_atom_count_top_A_abs,
                        analysis_functions.get_atom_count_top_B_abs,
                        #analysis_functions.get_atom_counts_top_AB_abs,
                        analysis_functions.get_atom_counts_top_polrot,
                        analysis_functions.get_atom_counts_top_polrot
                        ]

TO_DENSITY = {'Counts Side LF' : analysis_functions.get_atom_density_side_li_lf, 
                'Counts Side HF' : analysis_functions.get_atom_density_side_li_hf, 
                'Counts Top A (abs)' : analysis_functions.get_atom_density_top_A_abs, 
                'Counts Top B (abs)' : analysis_functions.get_atom_density_top_B_abs, 
                #'Counts Top AB (abs)' : analysis_functions.get_atom_densities_top_abs, 
                'Counts Top A (PR)' : analysis_functions.get_atom_densities_top_polrot,
                'Counts Top B (PR)' : analysis_functions.get_atom_densities_top_polrot}

DENSITIES = {'Density Side LF' : analysis_functions.get_atom_density_side_li_lf, 
                'Density Side HF' : analysis_functions.get_atom_density_side_li_hf,
                'Density Top A (abs)' : analysis_functions.get_atom_density_top_A_abs,
                'Density Top B (abs)' : analysis_functions.get_atom_density_top_B_abs,
                #'Density Top AB (abs)' : analysis_functions.get_atom_densities_top_abs,
                'Density Top A (PR)' : analysis_functions.get_atom_densities_top_polrot,
                'Density Top B (PR)' : analysis_functions.get_atom_densities_top_polrot,
                'Densities(z) Box Exp (PR)' : analysis_functions.get_hybrid_trap_densities_along_harmonic_axis}

IMAGING_RESONANCE_TYPES = ['Top A', 'Top B', 'Top AB', 'Side HF', 'Side LF']

# TODO: zip measure_quantities and analysis functions together

IMAGING_TYPES_LIST = ['top_double', 'side_low_mag', 'side_high_mag']
MEASUREMENT_IMAGE_NAME_DICT = {'top_double': ['TopA', 'TopB'], 'side_low_mag':['Side'], 'side_high_mag':['Side']}

class BEC1_Portal():
    def __init__(self, master):
        self.master = master
        self.image_browser_frame = Frame(master)
        self.image_browser_frame.pack() 

        tabControl = ttk.Notebook(master)
        self.tab1 = ttk.Frame(tabControl)
        self.tab2 = ttk.Frame(tabControl)
        self.tab3 = ttk.Frame(tabControl)
        self.tab4 = ttk.Frame(tabControl)
  
        tabControl.add(self.tab1, text ='Image Browser')
        tabControl.add(self.tab2, text ='Live Analysis')
        tabControl.add(self.tab3, text ='Guppy Cams')
        tabControl.pack(expand = 1, fill ="both")
  
        # FIRST TAB

        # browse button
        self.browse_bttn = Button(self.tab1, text="Browse", relief="raised",  width=8, command= self.browse)
        self.browse_bttn.place(x=20,y=20)

        # refresh button
        self.refresh_bttn = Button(self.tab1, text="Refresh", relief="raised",  width=8, command= self.refresh)
        self.refresh_bttn.place(x=100,y=20)

        # scan button
        self.scan_bttn = Button(self.tab1, text="Scan", relief="raised",  width=5, command= self.scan)
        self.scan_bttn.place(x=180,y=20)

        # show new button
        self.show_new_bttn = Button(self.tab1, text="Show new", relief="raised",  width=8, command= self.show_new)
        self.show_new_bttn.place(x=240,y=20)

        # delete button
        self.delete_bttn = Button(self.tab1, text="Del", relief="raised",  width=4, command= self.delete)
        self.delete_bttn.place(x=320,y=20)

        # selected image:
        self.selected_image_label = Label(self.tab1, text="Selected image: ").place(x=20, y = 335)
        self.selected_image_entry = Entry(self.tab1, text="", width=56)
        self.selected_image_entry.place(x = 20, y = 360)

        # blank image variable
        self.img = np.zeros((1,1,1))

        # Frame type:
        self.frame_type_label = Label(self.tab1, text="Frame type: ").place(x=20, y = 390)
        self.frame_type = 'FakeOD' # FakeOD is the default
        self.frame_type_entry = Entry(self.tab1, text="frame type entry", width=16)
        self.frame_type_entry.delete(0,'end')
        self.frame_type_entry.insert(1,self.frame_type)
        self.frame_type_entry.place(x=100, y = 390)

        self.OD_bttn = Button(self.tab1, text="OD", relief="raised",  width=7, command= self.OD_select)
        self.OD_bttn.place(x=20,y=420)

        self.with_atoms_bttn = Button(self.tab1, text="WA", relief="raised",  width=7, command= self.with_atoms_select)
        self.with_atoms_bttn.place(x=90,y=420)

        self.without_atoms_bttn = Button(self.tab1, text="WOA", relief="raised",  width=7, command= self.without_atoms_select)
        self.without_atoms_bttn.place(x=160,y=420)

        self.dark_bttn = Button(self.tab1, text="Dark", relief="raised",  width=7, command= self.dark_select)
        self.dark_bttn.place(x=230,y=420)

        self.FakeOD_bttn = Button(self.tab1, text="FakeOD", relief="raised",  width=7, command= self.FakeOD_select)
        self.FakeOD_bttn.place(x=300,y=420)

        # light 
        self.min_label = Label(self.tab1, text="Min: ").place(x=20, y = 460)
        self.min_entry = Entry(self.tab1, text="0", width=5)
        self.min_entry.place(x=60, y = 460)
        self.min_entry.delete(0,'end')
        self.min_entry.insert(0, "0")
        self.min_scale = float(self.min_entry.get())

        self.max_label = Label(self.tab1, text="Max: ").place(x=110, y = 460)
        self.max_entry = Entry(self.tab1, text="1.3", width=5)
        self.max_entry.place(x=150, y=460)
        self.max_entry.delete(0,'end')
        self.max_entry.insert(0, "1.3")
        self.max_scale = float(self.max_entry.get())

        # brightness:
        self.brightness_label = Label(self.tab1, text="Brightness: ").place(x=200, y = 460)
        self.brightness_entry = Entry(self.tab1, text="8", width=5)
        self.brightness_entry.place(x=275, y=460)  
        self.brightness_entry.delete(0,'end')   
        self.brightness_entry.insert(0, "8") 
        self.brightness = int(self.brightness_entry.get())  

        # light OK button
        self.light_OK_bttn = Button(self.tab1, text="OK", relief="raised",  width=4, command= self.light_OK)
        self.light_OK_bttn.place(x=320,y=457)

        # folder path
        self.folder_entry = Entry(self.tab1, text="folder name", width=56)
        self.folder_entry.place(x = 20, y = 60)

        # current folder name:
        self.folder_path = ''
        self.folder_path_old = self.folder_path
        # list of fullpaths:
        self.files_fullpath = []
        # current file name:
        self.current_file_name = ''
        self.current_file_fullpath = ''
        self.file_names = []
        self.file_names_old = []

        # code the table with file names:
        # 1/ to make table with scrollbar, need frame:
        table_frame = ttk.Frame(self.tab1, width=200)
        table_frame.place(x = 20, y = 95)
        # 2/ vertical scrollbar
        self.table_scrollbar = ttk.Scrollbar(table_frame)
        self.table_scrollbar.pack(side=RIGHT, fill=Y)
        # 3/ code for the file table:
        self.file_table = ttk.Treeview(table_frame, columns=("file_names"), yscrollcommand=self.table_scrollbar.set)
        self.file_table.pack()
        self.file_table.heading('#0', text='No.')
        self.file_table.heading('file_names', text='FITS images')
        self.file_table.column("#0", width=40)
        self.file_table.column("file_names", width = 285)
        # 4/ bind to get cell selection
        self.file_table.bind('<ButtonRelease-1>', self.selectItem)
        # 5/ configure scrollbar:
        self.table_scrollbar.config(command=self.file_table.yview)
        # 6/ configure table:
        style = ttk.Style()
        style.configure("Treeview", background='white',foreground="black",fieldbackground="black")
        style.map('Treeview', background=[('selected','#7ABBFF')])

        # code for the figure

        self.image_is_displayed = True

        self.fig = Figure(figsize=(9.5,10))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab1)
        self.canvas.get_tk_widget().place(x = 400, y = 5)
        self.ax = self.fig.add_subplot(111)
        [self.XMIN, self.XMAX] = self.ax.get_xlim()
        [self.YMIN, self.YMAX] = self.ax.get_ylim()
        self.oldSizeX = 0
        self.oldSizeY = 0
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.tab1, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.place(x = 400, y = 5)
        # reset view button:
        self.reset_view_bttn = Button(self.tab1, text="Reset view", relief="raised",  width=8, command= self.reset_view_button)
        self.reset_view_bttn.place(x=760,y=12)

        # ROI poly button
        self.ROI_poly_bttn = Button(self.tab1, text="ROI Poly", relief="raised",  width=8, command= self.ROI_poly_button)
        self.ROI_poly_bttn.place(x=840,y=12)
        self.roi = None
        self.roi_xs = None
        self.roi_ys = None
        # clear ROI poly
        self.clear_ROI_poly_bttn = Button(self.tab1, text="Clear ROI", relief="raised",  width=8, command= self.clear_ROI_poly_button)
        self.clear_ROI_poly_bttn.place(x=920,y=12)
        # load ROI poly
        self.load_ROI_poly_bttn = Button(self.tab1, text="Load ROI", relief="raised",  width=8, command= self.load_ROI_poly_button)
        self.load_ROI_poly_bttn.place(x=1000,y=12)
        self.load_ROI_poly_entry = Entry(self.tab1, text='load roi entry', width=12, bg='lightgray')
        self.load_ROI_poly_entry.place(x=1000+72,y=16)
        # save ROI poly
        self.save_ROI_poly_bttn = Button(self.tab1, text="Save ROI as", relief="raised",  width=10, command= self.save_ROI_poly_button)
        self.save_ROI_poly_bttn.place(x=1170,y=12)
        self.save_ROI_poly_entry = Entry(self.tab1, text='save roi entry', width=12, bg = 'lightgray')
        self.save_ROI_poly_entry.place(x=1170+85,y=16)
        self.save_ROI_poly_entry.delete(0,'end')
        self.save_ROI_poly_entry.insert(1,'roi_drawn')

        # self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # code for params table:
        self.params_table = ttk.Treeview(self.tab1, columns=("param_names"))
        self.params_table.place(x=20, y = 500)
        self.params_table.heading('#0', text='Params')
        self.params_table.heading('param_names', text='Value')
        self.params_table.column("#0", width=150)
        self.params_table.column("param_names", width = 175)

        # metadata variables:
        self.metadata_variables = ["id", "TOF", "ImagFreq0", "ImagFreq1", "ImagFreq2", "SideGreenEvap", "RF12_Time",
        "LFImgFreq","ShakingCycles","BoxShakeFreq", "BoxShakeAmp", "Evap2 End"]
        self.metadata_values = [None]*len(self.metadata_variables)
        self.params_for_selected_file = dict()

        # add params to table:
        self.param_label = Label(self.tab1, text="Add parameter: ")
        self.param_label.place(x=20, y=738)
        self.param_entry = Entry(self.tab1, text="new param", width=28)
        self.param_entry.place(x=120, y=740)  
        self.param_entry.delete(0,'end')   
        self.param_entry.insert(0, "") 

        # add param button:
        self.param_add_bttn = Button(self.tab1, text="Add", relief="raised",  width=4, command= self.add_param)
        self.param_add_bttn.place(x=308,y=736)

        # image saver:
        
        self.line4 = Label(self.tab1, text='-----------------------------------------------------------------')
        self.line4.place(x=20, y = 738+25)

        # ---------------------------------

        # image saver functions
        self.image_saver_label = Label(self.tab1, text="Image Saver: ", font=('TkDefaultFont', 10, 'bold'))
        self.image_saver_label.place(x=20, y = 780)

        self.run_bttn = Button(self.tab1, text="Do it", relief="raised",  width=16, command= self.run_button)
        self.run_bttn.place(x=20,y=790+20)
        self.run_bttn["state"] = DISABLED

        self.go_to_bttn = Button(self.tab1, text='Go to', relief="raised", width=6, command=self.go_to_button)
        self.go_to_bttn.place(x=157, y = 790+20)

        self.dryrun_bttn = Button(self.tab1, text="Dry run", relief="raised", command= self.dryrun_toggle)
        self.dryrun_bttn.place(x=223, y=790+20)
        
        self.custom_bttn = Button(self.tab1, text="Custom ", relief="raised", command= self.custom_toggle)
        self.custom_bttn.place(x=215+70, y=790+20)

        self.is_dryrun = True
        self.dryrun_state_before = NORMAL
        self.custom_state_before = DISABLED
        self.folder_name_entry_state_before = DISABLED
        self.confirm_button_state_before = DISABLED

        self.folder_name_label = Label(self.tab1, text="Folder name:" )
        self.folder_name_label.place(x=20, y=830+20)
        self.folder_name_entry = Entry(self.tab1, width=38)
        self.folder_name_entry.place(x=110, y=830+20)

        self.folder_name_entry["state"] = DISABLED
        self.folder_name = 'dryrun'
        self.acquisition_state = "STOPPED"

        self.confirm_bttn = Button(self.tab1, text="Confirm", command=self.confirm_button)
        self.confirm_bttn.place(x=240,y=860+20)
        self.confirm_bttn["state"] = DISABLED

        self.add_bttn = Button(self.tab1, text="Add", command=self.add_button)
        self.add_bttn.place(x=310,y=860+20)
        self.add_bttn["state"] = DISABLED
        
        self.image_saver_status = Entry(self.tab1, text="Status: ", width=25)
        self.image_saver_status.place(x = 70, y = 863+20)
        self.status_bar = Label(self.tab1, text="Status: ").place(x=20, y = 863+20)


        # ---------------------------------

        # Na BEC quick atom counting:
        self.Na_BEC_atom_count_label = Label(self.tab1, text="Na BEC atom counting: ", font=('TkDefaultFont', 10, 'bold'))
        self.Na_BEC_atom_count_label.place(x=1360, y = 10)

        self.BEC_diameter_label = Label(self.tab1, text="BEC diameter (px): ")
        self.BEC_diameter_label.place(x=1360, y = 40)
        self.BEC_diameter_entry = Entry(self.tab1, text="BEC diam", width=4)
        self.BEC_diameter_entry.place(x=1480, y=40)  
        self.BEC_diameter_entry.delete(0,'end')   
        self.BEC_diameter_entry.insert(0, "70")
        self.BEC_diameter = float(self.BEC_diameter_entry.get())

        self.BEC_TOF_label = Label(self.tab1, text="TOF (ms): ")
        self.BEC_TOF_label.place(x=1550, y = 40)
        self.BEC_TOF_entry = Entry(self.tab1, text="TOF", width=4)
        self.BEC_TOF_entry.place(x=1620, y=40) 
        self.BEC_TOF_entry.delete(0,'end')   
        self.BEC_TOF_entry.insert(0, "18")
        self.BEC_TOF = float(self.BEC_TOF_entry.get())

        self.ax_trap_freq_label = Label(self.tab1, text="Ax. trap freq (Hz): ")
        self.ax_trap_freq_label.place(x=1360, y = 70)
        self.ax_trap_freq_entry = Entry(self.tab1, text="ax trap", width=4)
        self.ax_trap_freq_entry.place(x=1465, y = 70)
        self.ax_trap_freq_entry.delete(0,'end')   
        self.ax_trap_freq_entry.insert(0, "12")
        self.ax_trap_freq = float(self.ax_trap_freq_entry.get())

        self.rad_trap_freq_label = Label(self.tab1, text="Rad. trap freq (Hz): ")
        self.rad_trap_freq_label.place(x=1500, y = 70)
        self.rad_trap_freq_entry = Entry(self.tab1, text='rad trap', width=4)
        self.rad_trap_freq_entry.place(x=1610, y = 70)
        self.rad_trap_freq_entry.delete(0,'end')   
        self.rad_trap_freq_entry.insert(0, "95")
        self.rad_trap_freq = float(self.rad_trap_freq_entry.get())

        self.um_per_px_label = Label(self.tab1, text="um per pix: ")
        self.um_per_px_label.place(x=1650, y = 70)
        self.um_per_px_entry = Entry(self.tab1, text='um per pix', width=4)
        self.um_per_px_entry.place(x=1725, y = 70)
        self.um_per_px_entry.delete(0,'end')   
        self.um_per_px_entry.insert(0, "5")
        self.um_per_px = float(self.um_per_px_entry.get())

        self.BEC_count_label = Label(self.tab1, text="BEC count: ")
        self.BEC_count_label.place(x=1360, y = 100)
        self.BEC_count_entry = Entry(self.tab1, text='BEC count', width=14)
        self.BEC_count_entry.place(x=1430, y = 100)
        self.BEC_count_entry.delete(0,'end')   
        self.BEC_count_entry.insert(0, "0")
        self.BEC_count = float(self.BEC_count_entry.get())

        self.BEC_DoIt_bttn = Button(self.tab1, text="Do it", relief="raised",  width=4, command= self.BEC_DoIt)
        self.BEC_DoIt_bttn.place(x=1550,y=97)

        self.line1 = Label(self.tab1, text='---------------------------------------------------------------------------------')
        self.line1.place(x=1360, y = 125)

        # Na Catch 
        self.Na_Catch_pixel_count_label = Label(self.tab1, text="Na Catch pixel counting: ", font=('TkDefaultFont', 10, 'bold'))
        self.Na_Catch_pixel_count_label.place(x=1360, y = 150)

        self.Na_Catch_background_label = Label(self.tab1, text="Background ROI ")
        self.Na_Catch_background_label.place(x=1360, y = 180)

        self.Na_Catch_background_X_range_label = Label(self.tab1, text="X range: ")
        self.Na_Catch_background_X_range_label.place(x=1480, y = 180)
        self.Na_Catch_background_X_min_entry = Entry(self.tab1, text="Na Catch X Min bkg", width=5)
        self.Na_Catch_background_X_min_entry.place(x=1535, y=180)  
        self.Na_Catch_background_X_min_entry.delete(0,'end')   
        self.Na_Catch_background_X_min_entry.insert(0, "1")
        self.Na_Catch_background_X_min = float(self.Na_Catch_background_X_min_entry.get())
        self.Na_Catch_background_X_max_entry = Entry(self.tab1, text="Na Catch X max bkg", width=5)
        self.Na_Catch_background_X_max_entry.place(x=1580, y=180)  
        self.Na_Catch_background_X_max_entry.delete(0,'end')   
        self.Na_Catch_background_X_max_entry.insert(0, "512")
        self.Na_Catch_background_X_max = float(self.Na_Catch_background_X_max_entry.get())

        self.Na_Catch_background_Y_range_label = Label(self.tab1, text="Y range: ")
        self.Na_Catch_background_Y_range_label.place(x=1630, y = 180)
        self.Na_Catch_background_Y_min_entry = Entry(self.tab1, text="Na Catch Y Min bkg", width=5)
        self.Na_Catch_background_Y_min_entry.place(x=1535+150, y=180)  
        self.Na_Catch_background_Y_min_entry.delete(0,'end')   
        self.Na_Catch_background_Y_min_entry.insert(0, "1")
        self.Na_Catch_background_Y_min = float(self.Na_Catch_background_Y_min_entry.get())
        self.Na_Catch_background_Y_max_entry = Entry(self.tab1, text="Na Catch Y max bkg", width=5)
        self.Na_Catch_background_Y_max_entry.place(x=1580+150, y=180)  
        self.Na_Catch_background_Y_max_entry.delete(0,'end')   
        self.Na_Catch_background_Y_max_entry.insert(0, "512")
        self.Na_Catch_background_Y_max = float(self.Na_Catch_background_Y_max_entry.get())

        self.Na_Catch_ROI_label = Label(self.tab1, text="Catch ROI ")
        self.Na_Catch_ROI_label.place(x=1360, y = 210)

        self.Na_Catch_ROI_X_range_label = Label(self.tab1, text="X range: ")
        self.Na_Catch_ROI_X_range_label.place(x=1480, y = 210)
        self.Na_Catch_ROI_X_min_entry = Entry(self.tab1, text="Na Catch X Min roi", width=5)
        self.Na_Catch_ROI_X_min_entry.place(x=1535, y=210)  
        self.Na_Catch_ROI_X_min_entry.delete(0,'end')   
        self.Na_Catch_ROI_X_min_entry.insert(0, "1")
        self.Na_Catch_ROI_X_min = float(self.Na_Catch_ROI_X_min_entry.get())
        self.Na_Catch_ROI_X_max_entry = Entry(self.tab1, text="Na Catch X max roi", width=5)
        self.Na_Catch_ROI_X_max_entry.place(x=1580, y=210)  
        self.Na_Catch_ROI_X_max_entry.delete(0,'end')   
        self.Na_Catch_ROI_X_max_entry.insert(0, "512")
        self.Na_Catch_ROI_X_max = float(self.Na_Catch_ROI_X_max_entry.get())

        self.Na_Catch_ROI_Y_range_label = Label(self.tab1, text="Y range: ")
        self.Na_Catch_ROI_Y_range_label.place(x=1630, y = 210)
        self.Na_Catch_ROI_Y_min_entry = Entry(self.tab1, text="Na Catch Y Min roi", width=5)
        self.Na_Catch_ROI_Y_min_entry.place(x=1535+150, y=210)  
        self.Na_Catch_ROI_Y_min_entry.delete(0,'end')   
        self.Na_Catch_ROI_Y_min_entry.insert(0, "1")
        self.Na_Catch_ROI_Y_min = float(self.Na_Catch_ROI_Y_min_entry.get())
        self.Na_Catch_ROI_Y_max_entry = Entry(self.tab1, text="Na Catch Y max roi", width=5)
        self.Na_Catch_ROI_Y_max_entry.place(x=1580+150, y=210)  
        self.Na_Catch_ROI_Y_max_entry.delete(0,'end')   
        self.Na_Catch_ROI_Y_max_entry.insert(0, "512")
        self.Na_Catch_ROI_Y_max = float(self.Na_Catch_ROI_Y_max_entry.get())

        self.Na_Catch_score_label = Label(self.tab1, text="Catch score:")
        self.Na_Catch_score_label.place(x=1360, y = 240)
        self.Na_Catch_score_entry = Entry(self.tab1, text="Na Catch score", width=14)
        self.Na_Catch_score_entry.place(x=1440, y=240)  
        self.Na_Catch_score_entry.delete(0,'end')   
        self.Na_Catch_score_entry.insert(0, "0")
        self.Na_Catch_score = float(self.Na_Catch_score_entry.get())

        self.Na_Catch_DoIt_bttn = Button(self.tab1, text="Do it", relief="raised",  width=4, command= self.Na_Catch_DoIt)
        self.Na_Catch_DoIt_bttn.place(x=1550,y=237)

        self.BackgroundROI_Crop_bttn = Button(self.tab1, text="Background ROI Crop", relief="raised", width=18, command = self.Na_Catch_BackgroundROI_Crop)
        self.BackgroundROI_Crop_bttn.place(x=1525, y=147)

        self.CatchROI_Crop_bttn = Button(self.tab1, text="Catch ROI Crop", relief="raised", width=12, command = self.Na_Catch_ROI_Crop)
        self.CatchROI_Crop_bttn.place(x=1670, y=147)

        self.line2 = Label(self.tab1, text='---------------------------------------------------------------------------------')
        self.line2.place(x=1360, y = 265)

        # Li MT LF atom counting
        self.Li_LF_atom_count_label = Label(self.tab1, text="Li LF atom counting: ", font=('TkDefaultFont', 10, 'bold'))
        self.Li_LF_atom_count_label.place(x=1360, y = 290)

        self.LiLF_ROI_Crop_bttn = Button(self.tab1, text="Li LF ROI Crop", relief="raised", width=16, command = self.LiLF_Crop)
        self.LiLF_ROI_Crop_bttn.place(x=1525, y=287)

        self.LiLF_ROI_label = Label(self.tab1, text="Li LF ROI ")
        self.LiLF_ROI_label.place(x=1360, y = 320)

        self.LiLF_X_range_label = Label(self.tab1, text="X range: ")
        self.LiLF_X_range_label.place(x=1480, y = 320)
        self.LiLF_X_min_entry = Entry(self.tab1, text="Li LF X Min", width=5)
        self.LiLF_X_min_entry.place(x=1535, y=320)  
        self.LiLF_X_min_entry.delete(0,'end')   
        self.LiLF_X_min_entry.insert(0, "1")
        self.LiLF_X_min = float(self.LiLF_X_min_entry.get())
        self.LiLF_X_max_entry = Entry(self.tab1, text="Li LF X max", width=5)
        self.LiLF_X_max_entry.place(x=1580, y=320)  
        self.LiLF_X_max_entry.delete(0,'end')   
        self.LiLF_X_max_entry.insert(0, "512")
        self.LiLF_X_max = float(self.LiLF_X_max_entry.get())

        self.LiLF_Y_range_label = Label(self.tab1, text="Y range: ")
        self.LiLF_Y_range_label.place(x=1630, y = 320)
        self.LiLF_Y_min_entry = Entry(self.tab1, text="Li LF Y Min", width=5)
        self.LiLF_Y_min_entry.place(x=1535+150, y=320)  
        self.LiLF_Y_min_entry.delete(0,'end')   
        self.LiLF_Y_min_entry.insert(0, "1")
        self.LiLF_Y_min = float(self.LiLF_Y_min_entry.get())
        self.LiLF_Y_max_entry = Entry(self.tab1, text="Li LF Y max", width=5)
        self.LiLF_Y_max_entry.place(x=1580+150, y=320)  
        self.LiLF_Y_max_entry.delete(0,'end')   
        self.LiLF_Y_max_entry.insert(0, "512")
        self.LiLF_Y_max = float(self.LiLF_Y_max_entry.get())

        self.LiLF_pixel_size_label = Label(self.tab1, text="Pixel size (um^2): ")
        self.LiLF_pixel_size_label.place(x=1360, y = 350)

        self.LiLF_pixel_size_entry = Entry(self.tab1, text="LiLF pixel size (um^2)", width=6)
        self.LiLF_pixel_size_entry.place(x=1470, y = 350)
        self.LiLF_pixel_size_entry.delete(0,'end')   
        self.LiLF_pixel_size_entry.insert(0, "27.52")

        self.LiLF_cross_section_label = Label(self.tab1, text="Cross section (um^2): ")
        self.LiLF_cross_section_label.place(x=1535, y = 350)

        self.LiLF_cross_section_entry = Entry(self.tab1, text="Cross section (um^2)", width=6)
        self.LiLF_cross_section_entry.place(x=1535+150, y = 350)
        self.LiLF_cross_section_entry.delete(0,'end')   
        self.LiLF_cross_section_entry.insert(0, "0.215")

        self.LiLF_sat_count_label = Label(self.tab1, text="Saturation Counts: ")
        self.LiLF_sat_count_label.place(x=1360, y = 380)

        self.LiLF_sat_count_entry = Entry(self.tab1, text="Saturation Counts", width=9)
        self.LiLF_sat_count_entry.place(x=1470, y = 380)
        self.LiLF_sat_count_entry.delete(0,'end')   
        self.LiLF_sat_count_entry.insert(0, "1.336e5")

        self.LiLF_atom_number_label = Label(self.tab1, text="Atom number: ")
        self.LiLF_atom_number_label.place(x=1535, y = 380)

        self.LiLF_atom_number_entry = Entry(self.tab1, text="Atom number", width=10)
        self.LiLF_atom_number_entry.place(x=1535+100, y = 380)
        self.LiLF_atom_number_entry.delete(0,'end')   
        self.LiLF_atom_number_entry.insert(0, "0")

        self.LiLF_DoIt_bttn = Button(self.tab1, text="Do it", relief="raised",  width=4, command= self.LiLF_DoIt)
        self.LiLF_DoIt_bttn.place(x=1535+180, y=377)

        self.line3 = Label(self.tab1, text='---------------------------------------------------------------------------------')
        self.line3.place(x=1360, y = 405)

        # imaging resonance processing
        self.imaging_resonance_processing_label = Label(self.tab1, text="Imaging resonance processing: ", font=('TkDefaultFont', 10, 'bold'))
        self.imaging_resonance_processing_label.place(x=1360, y = 430)

        self.browse_res_bttn = Button(self.tab1, text="Browse", relief="raised",  width=8, command= self.browse_res_button)
        self.browse_res_bttn.place(x=1360,y=460)
        self.image_processing_folder_path = ''

        self.res_image_folder_entry = Entry(self.tab1, text="Resonance imaging folder name", width=53)
        self.res_image_folder_entry.place(x = 1445, y = 463)

        self.resonance_imaging_mode = 'TopAB' # set to this by default

        self.side_lf_bttn = Button(self.tab1, text="Side LF", relief="raised",  width=7, command= self.side_lf)
        self.side_lf_bttn.place(x=1360,y=495)
        self.side_lf_bttn["state"] = DISABLED

        self.side_hf_bttn = Button(self.tab1, text="Side HF", relief="raised",  width=7, command= self.side_hf)
        self.side_hf_bttn.place(x=275+1160-5,y=495)
        self.side_hf_bttn["state"] = DISABLED

        self.TopA_bttn = Button(self.tab1, text="Top A", relief="raised",  width=7, command= self.TopA)
        self.TopA_bttn.place(x=350+1160-10,y=495)
        self.TopA_bttn["state"] = DISABLED

        self.TopB_bttn = Button(self.tab1, text="Top B", relief="raised",  width=7, command= self.TopB)
        self.TopB_bttn.place(x=425+1160-15,y=495)
        self.TopB_bttn["state"] = DISABLED

        self.TopAB_bttn = Button(self.tab1, text="Top AB", relief="raised",  width=7, command= self.TopAB)
        self.TopAB_bttn.place(x=500+1160-20,y=495)
        self.TopAB_bttn["state"] = DISABLED

        self.analyze_bttn = Button(self.tab1, text="Do It", relief="raised",  width=7, command= self.analyze_button)
        self.analyze_bttn.place(x=575+1160-25,y=495)
        self.analyze_bttn["state"] = DISABLED

        self.line5 = Label(self.tab1, text='---------------------------------------------------------------------------------')
        self.line5.place(x=1360, y = 495+25)

        # rf spectroscopy
        self.rf_resonance_processing_label = Label(self.tab1, text="RF resonance processing: ", font=('TkDefaultFont', 10, 'bold'))
        self.rf_resonance_processing_label.place(x=1360, y = 540)

        self.browse_rf_bttn = Button(self.tab1, text="Browse", relief="raised",  width=8, command= self.browse_rf_button)
        self.browse_rf_bttn.place(x=1360,y=570)
        self.rf_processing_folder_path = ''

        self.rf_spect_folder_entry = Entry(self.tab1, text="RF spectroscopy folder name", width=53)
        self.rf_spect_folder_entry.place(x = 1445, y = 573)

        self.RF_direction_label = Label(self.tab1, text="RF transfer: ").place(x=1360, y=607)
        self.RF_direction = StringVar()
        self.RF_direction.set( "1 to 2, Imaging 1 then 2")
        self.RF_directions_menu = OptionMenu(self.tab1, self.RF_direction, *RF_DIRECTIONS, command = self.RF_imaging_options)
        self.RF_directions_menu.place(x = 1445, y = 600)
        self.rf_resonance_key = self.RF_direction.get()     

        self.Rabi_guess_var = StringVar()
        self.RF_center_guess_var = StringVar()
        self.Rabi_guess_label = Label(self.tab1, text= "Rabi frequency guess (kHz): ").place(x=1360, y=640)
        self.RF_center_guess_label = Label(self.tab1, text= "RF center guess (MHz): ").place(x=1360, y=670)
        self.Rabi_guess = Entry(self.tab1, textvariable = self.Rabi_guess_var, width=20).place(x=1550,y=642)
        self.RF_center_guess = Entry(self.tab1, textvariable = self.RF_center_guess_var, width=20).place(x=1550,y=672)

        self.rf_analyze_bttn = Button(self.tab1, text="Analyze", relief="raised",  width=15, command= self.rf_analyze_button)
        self.rf_analyze_bttn.place(x=1430, y=700)
        self.rf_analyze_bttn["state"] = DISABLED   

        self.rf_analyze_with_guess_bttn = Button(self.tab1, text="Analyze with guess", relief="raised",  width=15, command= self.rf_analyze_with_guess_button)
        self.rf_analyze_with_guess_bttn.place(x=1600,y=700)
        self.rf_analyze_with_guess_bttn["state"] = DISABLED

        self.line6 = Label(self.tab1, text='---------------------------------------------------------------------------------')
        self.line6.place(x=1360, y = 700+25)

        # hybrid top analysis:
        self.hybrid_top_analysis_label = Label(self.tab1, text="Hybrid Top Analysis: ", font=('TkDefaultFont', 10, 'bold'))
        self.hybrid_top_analysis_label.place(x=1360, y = 750)

        self.browse_hybrid_bttn = Button(self.tab1, text="Browse", relief="raised",  width=8, command= self.browse_hybrid_button)
        self.browse_hybrid_bttn.place(x=1360,y=750+30)
        self.hybrid_processing_folder_path = ''

        self.hybrid_folder_entry = Entry(self.tab1, text="Hybrid data folder name", width=53)
        self.hybrid_folder_entry.place(x = 1445, y = 750+30+3)

        self.hybrid_imaging_mode = 'abs' # set to this by default other option is 'polrot'

        self.abs_img_bttn = Button(self.tab1, text="Absorption", relief="raised",  width=10, command= self.abs_img)
        self.abs_img_bttn.place(x=1360,y=815)
        self.abs_img_bttn["state"] = DISABLED

        self.polrot_img_bttn = Button(self.tab1, text="Pol. rot.", relief="raised",  width=10, command= self.polrot_img)
        self.polrot_img_bttn.place(x=1470,y=815)
        self.polrot_img_bttn["state"] = DISABLED

        self.hybrid_analyze_bttn = Button(self.tab1, text="Analyze", relief="raised",  width=15, command= self.hybrid_analyze_button)
        self.hybrid_analyze_bttn.place(x=1600,y=815)
        self.hybrid_analyze_bttn["state"] = DISABLED

        # SECOND TAB: LIVE ANALYSIS
        # measurement object, initialized to None
        self.current_measurement = None

        # browse button
        self.browse_bttn_live_analysis = Button(self.tab2, text="Browse", relief="raised",  width=8, command= self.browse_live_analysis)
        self.browse_bttn_live_analysis.place(x=20,y=20)

        # refresh button
        self.refresh_bttn_live_analysis = Button(self.tab2, text="Refresh", relief="raised",  width=8, command= self.refresh_live_analysis)
        self.refresh_bttn_live_analysis.place(x=100,y=20)

        # scan button
        # self.scan_bttn_live_analysis = Button(self.tab2, text="Scan", relief="raised",  width=5, command= self.scan_live_analysis)
        # self.scan_bttn_live_analysis.place(x=180,y=20)

        # show new button
        # self.show_new_bttn_live_analysis = Button(self.tab2, text="Show new", relief="raised",  width=8, command= self.show_new_live_analysis)
        # self.show_new_bttn_live_analysis.place(x=240,y=20)

        # delete button
        self.delete_bttn_live_analysis = Button(self.tab2, text="Del", relief="raised",  width=4, command= self.delete_live_analysis)
        self.delete_bttn_live_analysis.place(x=320,y=20)

        # folder path
        self.folder_entry_live_analysis = Entry(self.tab2, text="folder name live analysis", width=56)
        self.folder_entry_live_analysis.place(x = 20, y = 60)
        # current folder name:
        self.folder_path_live_analysis = ''
        self.folder_path_old_live_analysis = self.folder_path_live_analysis
        # list of fullpaths:
        self.files_fullpath_live_analysis = []
        # current file name:
        self.current_file_name_live_analysis = ''
        self.current_file_fullpath_live_analysis = ''
        self.file_names_live_analysis = []
        self.file_names_old_live_analysis = []

        # selected image:
        self.selected_image_label_live_analysis = Label(self.tab2, text="Selected image: ").place(x=20, y = 335)
        self.selected_image_entry_live_analysis = Entry(self.tab2, text="live analysis", width=56)
        self.selected_image_entry_live_analysis.place(x = 20, y = 360)

        # code the table with file names:
        # 1/ to make table with scrollbar, need frame:
        table_frame_live_analysis = ttk.Frame(self.tab2, width=200)
        table_frame_live_analysis.place(x = 20, y = 95)
        # 2/ vertical scrollbar
        self.table_scrollbar_live_analysis = ttk.Scrollbar(table_frame_live_analysis)
        self.table_scrollbar_live_analysis.pack(side=RIGHT, fill=Y)
        # 3/ code for the file table:
        self.file_table_live_analysis = ttk.Treeview(table_frame_live_analysis, columns=("file_names"), yscrollcommand=self.table_scrollbar_live_analysis.set)
        self.file_table_live_analysis.pack()
        self.file_table_live_analysis.heading('#0', text='No.')
        self.file_table_live_analysis.heading('file_names', text='FITS images')
        self.file_table_live_analysis.column("#0", width=40)
        self.file_table_live_analysis.column("file_names", width = 285)
        # 4/ bind to get cell selection
        self.file_table_live_analysis.bind('<ButtonRelease-1>', self.selectItem_live_analysis)
        # 5/ configure scrollbar:
        self.table_scrollbar_live_analysis.config(command=self.file_table_live_analysis.yview)

        # code for params table:
        self.params_table_live_analysis = ttk.Treeview(self.tab2, columns=("param_names_live_analysis"))
        self.params_table_live_analysis.place(x=20, y = 400)
        self.params_table_live_analysis.heading('#0', text='Params')
        self.params_table_live_analysis.heading('param_names_live_analysis', text='Value')
        self.params_table_live_analysis.column("#0", width=150)
        self.params_table_live_analysis.column("param_names_live_analysis", width = 175)

        # metadata variables:
        self.metadata_variables_live_analysis = ["id", "TOF", "ImagFreq0", "ImagFreq1", "ImagFreq2", "SideGreenEvap", "RF12_Time",
        "LFImgFreq","ShakingCycles","BoxShakeFreq", "BoxShakeAmp", "Evap2 End"]
        self.metadata_values_live_analysis = [None]*len(self.metadata_variables_live_analysis)
        self.params_for_selected_file_live_analysis = dict()

        # add params to table:
        self.param_label_live_analysis = Label(self.tab2, text="Add parameter: ")
        self.param_label_live_analysis.place(x=20, y=638)
        self.param_entry_live_analysis = Entry(self.tab2, text="new param live analysis", width=28)
        self.param_entry_live_analysis.place(x=120, y=640)  
        self.param_entry_live_analysis.delete(0,'end')   
        self.param_entry_live_analysis.insert(0, "") 

        # add param button:
        self.param_add_bttn_live_analysis = Button(self.tab2, text="Add", relief="raised",  width=4, command= self.add_param_live_analysis)
        self.param_add_bttn_live_analysis.place(x=308,y=636)

        # live analysis
        self.line1_live_analysis = Label(self.tab2, text='-----------------------------------------------------------------')
        self.line1_live_analysis.place(x=20, y = 638+25)

        # image type buttons:
        self.image_type = IMAGING_TYPES_LIST[0] # set to this by default

        self.top_double_bttn = Button(self.tab2, text="Top AB", relief="raised",  width=8, command= self.top_double)
        self.top_double_bttn.place(x=20,y=712)
        self.top_double_bttn["state"] = DISABLED

        self.side_lm_bttn = Button(self.tab2, text="Side LM", relief="raised",  width=8, command= self.side_low_mag)
        self.side_lm_bttn.place(x=95,y=712)
        self.side_lm_bttn["state"] = DISABLED

        self.side_hm_bttn = Button(self.tab2, text="Side HM", relief="raised",  width=8, command= self.side_high_mag)
        self.side_hm_bttn.place(x=170,y=712)
        self.side_hm_bttn["state"] = DISABLED

        # plotting variables status:
        self.plotting_variables_entry_live_analysis = Entry(self.tab2, text="plotting variables", width=37)
        self.plotting_variables_entry_live_analysis.place(x=120, y=712-30)  
        self.plotting_variables_entry_live_analysis.delete(0,'end')   
        self.plotting_variables_entry_live_analysis.insert(0, "") 

        # figure options
        self.chosen_figure_live_analysis = StringVar()
        self.chosen_figure_live_analysis.set(LIVE_FIGURES[0])
        self.chosen_figure_live_analysis_menu = OptionMenu(self.tab2, self.chosen_figure_live_analysis, *LIVE_FIGURES, command = self.choose_figure_live_analysis)
        self.chosen_figure_live_analysis_menu.place(x=245, y=709)
        self.current_figure_live_analysis = self.chosen_figure_live_analysis.get() 

        # live analysis label
        self.live_analysis_label = Label(self.tab2, text="Live Analysis: ", font=('TkDefaultFont', 10, 'bold'))
        self.live_analysis_label.place(x=20, y = 680)

        # choose what to plot against what
        self.plot_quantity_label_live_analysis = Label(self.tab2, text="Plot quantity: ")
        self.plot_quantity_label_live_analysis.place(x=20, y=752)

        self.plotting_quantity_live_analysis = StringVar()
        self.plotting_quantity_live_analysis.set(MEASURE_QUANTITIES[0])
        self.plotting_quantity_live_analysis_menu = OptionMenu(self.tab2, self.plotting_quantity_live_analysis, *MEASURE_QUANTITIES, command = self.choose_plotting_quantity_live_analysis)
        self.plotting_quantity_live_analysis_menu.configure(width=20)
        self.plotting_quantity_live_analysis_menu.place(x = 118, y = 747)
        self.current_plotting_quantity_live_analysis = self.plotting_quantity_live_analysis.get() 

        self.vs_variable_live_analysis = Label(self.tab2, text="vs variable: ")
        self.vs_variable_live_analysis.place(x=20, y=789)

        self.vs_variable_entry_live_analysis = Entry(self.tab2, text="vs variable", width=28)
        self.vs_variable_entry_live_analysis.place(x=120, y=791)  
        self.vs_variable_entry_live_analysis.delete(0,'end')   
        self.vs_variable_entry_live_analysis.insert(0, "") 

        self.vs_quantity_label_live_analysis = Label(self.tab2, text="vs quantity: ")
        self.vs_quantity_label_live_analysis.place(x=20, y=825)

        self.vs_quantity_live_analysis = StringVar()
        self.vs_quantity_live_analysis.set(MEASURE_QUANTITIES[0])
        self.vs_quantity_live_analysis_menu = OptionMenu(self.tab2, self.vs_quantity_live_analysis, *MEASURE_QUANTITIES, command = self.choose_vs_quantity_live_analysis)
        self.vs_quantity_live_analysis_menu.configure(width=20)
        self.vs_quantity_live_analysis_menu.place(x = 118, y = 820)
        self.current_vs_quantity_live_analysis = self.plotting_quantity_live_analysis.get() 

        # ok variable button
        self.vs_variable_ok_bttn_live_analysis = Button(self.tab2, text="OK", relief="raised",  width=4, command= self.vs_variable_ok_button_live_analysis)
        self.vs_variable_ok_bttn_live_analysis.place(x=308,y=787)

        # ok quantity button
        # self.vs_quantity_ok_bttn_live_analysis = Button(self.tab2, text="OK", relief="raised",  width=4, command= self.vs_quantity_ok_button_live_analysis)
        # self.vs_quantity_ok_bttn_live_analysis.place(x=308,y=822+40)

        # option to plot density (last image to come in):
        self.plot_density_live_analysis_label = Label(self.tab2, text="Plot density: ")
        self.plot_density_live_analysis_label.place(x=20, y = 864)

        self.plot_density_live_analysis = StringVar()
        self.plot_density_live_analysis.set(list(DENSITIES.keys())[0])
        self.plot_density_live_analysis_menu = OptionMenu(self.tab2, self.plot_density_live_analysis, *list(DENSITIES.keys()), command = self.choose_plot_density)
        self.plot_density_live_analysis_menu.configure(width=24)
        self.plot_density_live_analysis_menu.place(x = 117, y = 860)
        self.current_density_to_plot = self.plot_density_live_analysis.get() 

        self.figure_plotting_info = [None]*len(LIVE_FIGURES)

        # ANALYZE LIVE BUTTON:
        self.analyze_live_bttn = Button(self.tab2, text="START ANALYSIS", relief="raised",  width=21, command= self.analyze_live_button)
        self.analyze_live_bttn.place(x=20,y=865+45+40)
        self.analyze_live_bttn.config(fg='green')
        self.analyze_live_bttn["state"] = DISABLED

        # STOP ANALYZE BUTTON:
        self.stop_analyze_live_bttn = Button(self.tab2, text="END ANALYSIS", relief="raised",  width=21, command= self.stop_analyze_live_button)
        self.stop_analyze_live_bttn.place(x=189,y=865+45+40)
        self.stop_analyze_live_bttn.config(fg='black')
        self.stop_analyze_live_bttn["state"] = NORMAL

        # reset analysis
        self.reset_fields_analysis_live_bttn = Button(self.tab2, text="Reset fields", relief="raised",  width=18, command= self.reset_fields_analysis_live_button)
        self.reset_fields_analysis_live_bttn.place(x=210,y=865+40)
        self.reset_fields_analysis_live_bttn["state"] = NORMAL

        # confirm ROI and norm box 
        self.confirm_roi_and_norm_box_bttn = Button(self.tab2, text="Confirm ROI and Norm Box", relief="raised", width=24, command = self.confirm_roi_and_norm_box)
        self.confirm_roi_and_norm_box_bttn.place(x=20,y=865+40)
        self.confirm_roi_and_norm_box_bttn["state"] = DISABLED

        # code for the figure
        self.fig_live_analysis = Figure(figsize=(10,10))
        self.canvas_live_analysis = FigureCanvasTkAgg(self.fig_live_analysis, master=self.tab2)
        self.canvas_live_analysis.get_tk_widget().place(x = 400, y = 5)

        self.ax1_live_analysis = self.fig_live_analysis.add_subplot(221)
        self.ax1_live_analysis.set_xlabel('X')
        self.ax1_live_analysis.set_ylabel('Y')
        self.ax1_live_analysis.set_title('Axes 1')

        self.ax2_live_analysis = self.fig_live_analysis.add_subplot(222)
        self.ax2_live_analysis.set_xlabel('X')
        self.ax2_live_analysis.set_ylabel('Y')
        self.ax2_live_analysis.set_title('Axes 2')

        self.ax3_live_analysis = self.fig_live_analysis.add_subplot(223)
        self.ax3_live_analysis.set_xlabel('X')
        self.ax3_live_analysis.set_ylabel('Y')
        self.ax3_live_analysis.set_title('Axes 3')

        self.ax4_live_analysis = self.fig_live_analysis.add_subplot(224)
        self.ax4_live_analysis.set_xlabel('X')
        self.ax4_live_analysis.set_ylabel('Y')
        self.ax4_live_analysis.set_title('Axes 4')

        self.ax_list = [self.ax1_live_analysis, self.ax2_live_analysis, self.ax3_live_analysis, self.ax4_live_analysis]

        # navigation toolbar
        self.toolbar_live_analysis = NavigationToolbar2Tk(self.canvas_live_analysis, self.tab2, pack_toolbar=False)
        self.toolbar_live_analysis.update()
        self.toolbar_live_analysis.place(x = 400, y = 5)

        # code for the image preview
        self.image_viewer_live_analysis = Figure(figsize=(4.75,4.75))
        self.canvas_image_viewer_live_analysis = FigureCanvasTkAgg(self.image_viewer_live_analysis, master=self.tab2)
        self.canvas_image_viewer_live_analysis.get_tk_widget().place(x = 1420, y = 5)

        self.ax_image_viewer_live_analysis = self.image_viewer_live_analysis.add_subplot(111)
        self.ax_image_viewer_live_analysis.set_title('Image viewer')
        [self.XMIN_live_analysis, self.XMAX_live_analysis] = self.ax_image_viewer_live_analysis.get_xlim()
        [self.YMIN_live_analysis, self.YMAX_live_analysis] = self.ax_image_viewer_live_analysis.get_ylim()
        self.oldSizeX_live_analysis = 0
        self.oldSizeY_live_analysis = 0

        # form norm box and roi
        self.XMIN_analyze = self.XMIN_live_analysis
        self.XMAX_analyze = self.XMAX_live_analysis
        self.YMIN_analyze = self.YMIN_live_analysis
        self.YMAX_analyze = self.YMAX_live_analysis
        self.roi_rect = None
        self.norm_box_rect = None

        # blank image variable:
        self.img_live_analysis = np.zeros((1,1,1))

        # ROI selection
        self.ROI_Crop_bttn_live_analysis = Button(self.tab2, text="ROI Crop", relief="raised", width=16, command = self.live_analysis_ROI_Crop)
        self.ROI_Crop_bttn_live_analysis.place(x=1360+60, y = 320+187)

        self.X_range_label_live_analysis = Label(self.tab2, text="X range: ")
        self.X_range_label_live_analysis.place(x=1480+80, y = 320+190)
        self.X_min_entry_live_analysis = Entry(self.tab2, text="X Min", width=6)
        self.X_min_entry_live_analysis.place(x=1535+80, y=320+190)  
        self.X_min_entry_live_analysis.delete(0,'end')   
        self.X_min_entry_live_analysis.insert(0, "1")
        self.X_min_live_analysis = float(self.X_min_entry_live_analysis.get())
        self.X_max_entry_live_analysis = Entry(self.tab2, text="X max", width=6)
        self.X_max_entry_live_analysis.place(x=1580+80+5, y=320+190)  
        self.X_max_entry_live_analysis.delete(0,'end')   
        self.X_max_entry_live_analysis.insert(0, "512")
        self.X_max_live_analysis = float(self.X_max_entry_live_analysis.get())

        self.Y_range_label_live_analysis = Label(self.tab2, text="Y range: ")
        self.Y_range_label_live_analysis.place(x=1630+80, y = 320+190)
        self.Y_min_entry_live_analysis = Entry(self.tab2, text="Y Min", width=6)
        self.Y_min_entry_live_analysis.place(x=1535+150+80, y=320+190)  
        self.Y_min_entry_live_analysis.delete(0,'end')   
        self.Y_min_entry_live_analysis.insert(0, "1")
        self.Y_min_live_analysis = float(self.Y_min_entry_live_analysis.get())
        self.Y_max_entry_live_analysis = Entry(self.tab2, text="Y max", width=6)
        self.Y_max_entry_live_analysis.place(x=1580+150+80+5, y=320+190)  
        self.Y_max_entry_live_analysis.delete(0,'end')   
        self.Y_max_entry_live_analysis.insert(0, "512")
        self.Y_max_live_analysis = float(self.Y_max_entry_live_analysis.get())


        # norm box selection
        self.norm_box_Crop_bttn_live_analysis = Button(self.tab2, text="Norm box Crop", relief="raised", width=16, command = self.live_analysis_norm_box_Crop)
        self.norm_box_Crop_bttn_live_analysis.place(x=1360+60, y = 320+187+35)

        self.norm_box_X_range_label_live_analysis = Label(self.tab2, text="X range: ")
        self.norm_box_X_range_label_live_analysis.place(x=1480+80, y = 320+190+35)
        self.norm_box_X_min_entry_live_analysis = Entry(self.tab2, text="nb X Min", width=6)
        self.norm_box_X_min_entry_live_analysis.place(x=1535+80, y=320+190+35)  
        self.norm_box_X_min_entry_live_analysis.delete(0,'end')   
        self.norm_box_X_min_entry_live_analysis.insert(0, "1")
        self.norm_box_X_min_live_analysis = float(self.norm_box_X_min_entry_live_analysis.get())
        self.norm_box_X_max_entry_live_analysis = Entry(self.tab2, text="nb X max", width=6)
        self.norm_box_X_max_entry_live_analysis.place(x=1580+80+5, y=320+190+35)  
        self.norm_box_X_max_entry_live_analysis.delete(0,'end')   
        self.norm_box_X_max_entry_live_analysis.insert(0, "512")
        self.norm_box_X_max_live_analysis = float(self.norm_box_X_max_entry_live_analysis.get())

        self.norm_box_Y_range_label_live_analysis = Label(self.tab2, text="Y range: ")
        self.norm_box_Y_range_label_live_analysis.place(x=1630+80, y = 320+190+35)
        self.norm_box_Y_min_entry_live_analysis = Entry(self.tab2, text="nb Y Min", width=6)
        self.norm_box_Y_min_entry_live_analysis.place(x=1535+150+80, y=320+190+35)  
        self.norm_box_Y_min_entry_live_analysis.delete(0,'end')   
        self.norm_box_Y_min_entry_live_analysis.insert(0, "1")
        self.norm_box_Y_min_live_analysis = float(self.norm_box_Y_min_entry_live_analysis.get())
        self.norm_box_Y_max_entry_live_analysis = Entry(self.tab2, text="nb Y max", width=6)
        self.norm_box_Y_max_entry_live_analysis.place(x=1580+150+80+5, y=320+190+35)  
        self.norm_box_Y_max_entry_live_analysis.delete(0,'end')   
        self.norm_box_Y_max_entry_live_analysis.insert(0, "512")
        self.norm_box_Y_max_live_analysis = float(self.norm_box_Y_max_entry_live_analysis.get())

        # line for fitting section:
        self.line2_live_analysis = Label(self.tab2, text='----------------------------------------------------------------------------------------------')
        self.line2_live_analysis.place(x=1420, y = 575)

        # fitting label:
        self.live_analysis_label = Label(self.tab2, text="Data Fitting: ", font=('TkDefaultFont', 10, 'bold'))
        self.live_analysis_label.place(x = 1420, y = 595)

        # which figure to curve fit:
        self.data_fit_figure = StringVar()
        self.data_fit_figure.set(LIVE_FIGURES[0])
        self.data_fit_figure_menu = OptionMenu(self.tab2, self.data_fit_figure, *LIVE_FIGURES, command = self.choose_figure_for_data_fit)
        self.data_fit_figure_menu.place(x = 1520, y = 591)

        # imaging resonance fit:
        self.imaging_resonance_fit_type_label = Label(self.tab2, text="Imaging resonance fit: ")
        self.imaging_resonance_fit_type_label.place(x=1420, y = 633)

        # imaging resonance fit menu:
        self.imaging_resonance_fit_type = StringVar()
        self.imaging_resonance_fit_type.set(IMAGING_RESONANCE_TYPES[0])
        self.imaging_resonance_fit_type_menu = OptionMenu(self.tab2, self.imaging_resonance_fit_type, *IMAGING_RESONANCE_TYPES, command = self.choose_imaging_resonance_type)
        self.imaging_resonance_fit_type_menu.configure(width=12)
        self.imaging_resonance_fit_type_menu.place(x = 1560, y = 627)

        # do it button for imaging resonance fit:
        self.imaging_resonance_fit_do_it_bttn = Button(self.tab2, text="Do It", relief="raised",  width=7, command= self.imaging_resonance_fit_do_it_button)
        self.imaging_resonance_fit_do_it_bttn.place(x=1700,y=629)



        ##############################################################
        # THIRD TAB: GUPPY CAMS
        # browse button
        self.browse_bttn_guppy = Button(self.tab3, text="Browse", relief="raised",  width=8, command= self.browse_guppy)
        self.browse_bttn_guppy.place(x=20,y=20)

        # refresh button
        self.refresh_bttn_guppy = Button(self.tab3, text="Refresh", relief="raised",  width=8, command= self.refresh_guppy)
        self.refresh_bttn_guppy.place(x=100,y=20)

        # scan button
        self.scan_bttn_guppy = Button(self.tab3, text="Scan", relief="raised",  width=5, command= self.scan_guppy)
        self.scan_bttn_guppy.place(x=180,y=20)

        # show new button
        # self.show_new_bttn_guppy = Button(self.tab3, text="Show new", relief="raised",  width=8, command= self.show_new_guppy)
        # self.show_new_bttn_guppy.place(x=240,y=20)

        # delete button
        self.delete_bttn_guppy = Button(self.tab3, text="Del", relief="raised",  width=4, command= self.delete_guppy)
        self.delete_bttn_guppy.place(x=320,y=20)

        # selected image:
        self.selected_image_label_guppy = Label(self.tab3, text="Selected image: ").place(x=20, y = 335)
        self.selected_image_entry_guppy = Entry(self.tab3, text="", width=56)
        self.selected_image_entry_guppy.place(x = 20, y = 360)

        # Frame type:
        self.frame_type_label_guppy = Label(self.tab3, text="Frame type: ").place(x=20, y = 390)
        self.frame_type_guppy = 'FakeOD' # FakeOD is the default
        self.frame_type_entry_guppy = Entry(self.tab3, text="frame type entry", width=16)
        self.frame_type_entry_guppy.delete(0,'end')
        self.frame_type_entry_guppy.insert(1,self.frame_type_guppy)
        self.frame_type_entry_guppy.place(x=100, y = 390)
        self.OD_bttn_guppy = Button(self.tab3, text="OD", relief="raised",  width=7, command= self.OD_select_guppy)
        self.OD_bttn_guppy.place(x=20,y=420)
        self.with_atoms_bttn_guppy = Button(self.tab3, text="WA", relief="raised",  width=7, command= self.with_atoms_select_guppy)
        self.with_atoms_bttn_guppy.place(x=90,y=420)
        self.without_atoms_bttn_guppy = Button(self.tab3, text="WOA", relief="raised",  width=7, command= self.without_atoms_select_guppy)
        self.without_atoms_bttn_guppy.place(x=160,y=420)
        self.dark_bttn_guppy = Button(self.tab3, text="Dark", relief="raised",  width=7, command= self.dark_select_guppy)
        self.dark_bttn_guppy.place(x=230,y=420)
        self.FakeOD_bttn_guppy = Button(self.tab3, text="FakeOD", relief="raised",  width=7, command= self.FakeOD_select_guppy)
        self.FakeOD_bttn_guppy.place(x=300,y=420)

        # light 
        self.min_label_guppy = Label(self.tab3, text="Min: ").place(x=20, y = 460)
        self.min_entry_guppy = Entry(self.tab3, text="0", width=5)
        self.min_entry_guppy.place(x=60, y = 460)
        self.min_entry_guppy.delete(0,'end')
        self.min_entry_guppy.insert(0, "0")
        self.min_scale_guppy = float(self.min_entry_guppy.get())
        self.max_label_guppy = Label(self.tab3, text="Max: ").place(x=110, y = 460)
        self.max_entry_guppy = Entry(self.tab3, text="1.3", width=5)
        self.max_entry_guppy.place(x=150, y=460)
        self.max_entry_guppy.delete(0,'end')
        self.max_entry_guppy.insert(0, "1.3")
        self.max_scale_guppy = float(self.max_entry_guppy.get())
        # brightness:
        self.brightness_label_guppy = Label(self.tab3, text="Brightness: ").place(x=200, y = 460)
        self.brightness_entry_guppy = Entry(self.tab3, text="8", width=5)
        self.brightness_entry_guppy.place(x=275, y=460)  
        self.brightness_entry_guppy.delete(0,'end')   
        self.brightness_entry_guppy.insert(0, "8") 
        self.brightness_guppy = int(self.brightness_entry_guppy.get())  
        # light OK button
        self.light_OK_bttn_guppy = Button(self.tab3, text="OK", relief="raised",  width=4, command= self.light_OK_guppy)
        self.light_OK_bttn_guppy.place(x=320,y=457)
        # folder path
        self.folder_entry_guppy = Entry(self.tab3, text="folder name", width=56)
        self.folder_entry_guppy.place(x = 20, y = 60)
        # current folder name:
        self.folder_path_guppy = ''
        self.folder_path_old_guppy = self.folder_path_guppy
        # list of fullpaths:
        self.files_fullpath_guppy = []
        # current file name:
        self.current_file_name_guppy = ''
        self.current_file_fullpath_guppy = ''
        self.file_names_guppy = []
        self.file_names_old_guppy = []

        # code the table with file names:
        # 1/ to make table with scrollbar, need frame:
        table_frame_guppy = ttk.Frame(self.tab3, width=200)
        table_frame_guppy.place(x = 20, y = 95)
        # 2/ vertical scrollbar
        self.table_scrollbar_guppy = ttk.Scrollbar(table_frame_guppy)
        self.table_scrollbar_guppy.pack(side=RIGHT, fill=Y)
        # 3/ code for the file table:
        self.table_guppy = ttk.Treeview(table_frame_guppy, columns=("file_names"), yscrollcommand=self.table_scrollbar_guppy.set)
        self.table_guppy.pack()
        self.table_guppy.heading('#0', text='No.')
        self.table_guppy.heading('file_names', text='FITS images')
        self.table_guppy.column("#0", width=40)
        self.table_guppy.column("file_names", width = 285)
        # 4/ bind to get cell selection
        self.table_guppy.bind('<ButtonRelease-1>', self.selectItem_guppy)
        # 5/ configure scrollbar:
        self.table_scrollbar_guppy.config(command=self.table_guppy.yview)

        # code for the figure
        self.fig_guppy = Figure(figsize=(9.5,10))
        self.canvas_guppy = FigureCanvasTkAgg(self.fig_guppy, master=self.tab3)
        self.canvas_guppy.get_tk_widget().place(x = 400, y = 5)
        self.ax_guppy = self.fig_guppy.add_subplot(111)
        [self.XMIN_guppy, self.XMAX_guppy] = self.ax_guppy.get_xlim()
        [self.YMIN_guppy, self.YMAX_guppy] = self.ax_guppy.get_ylim()
        self.oldSizeX_guppy = 0
        self.oldSizeY_guppy = 0
        self.toolbar_guppy = NavigationToolbar2Tk(self.canvas_guppy, self.tab3, pack_toolbar=False)
        self.toolbar_guppy.update()
        self.toolbar_guppy.place(x = 400, y = 5)
        # reset view button:
        self.reset_view_bttn_guppy = Button(self.tab3, text="Reset view", relief="raised",  width=8, command= self.reset_view_button_guppy)
        self.reset_view_bttn_guppy.place(x=760,y=12)
        # ROI poly button
        self.ROI_poly_bttn_guppy = Button(self.tab3, text="ROI Poly", relief="raised",  width=8, command= self.ROI_poly_button_guppy)
        self.ROI_poly_bttn_guppy.place(x=840,y=12)
        self.roi_guppy = None
        self.roi_xs_guppy = None
        self.roi_ys_guppy = None
        # clear ROI poly
        self.clear_ROI_poly_bttn_guppy = Button(self.tab3, text="Clear ROI", relief="raised",  width=8, command= self.clear_ROI_poly_button_guppy)
        self.clear_ROI_poly_bttn_guppy.place(x=920,y=12)
        # load ROI poly
        self.load_ROI_poly_bttn_guppy = Button(self.tab3, text="Load ROI", relief="raised",  width=8, command= self.load_ROI_poly_button_guppy)
        self.load_ROI_poly_bttn_guppy.place(x=1000,y=12)
        self.load_ROI_poly_entry_guppy = Entry(self.tab3, text='load roi entry', width=12, bg='lightgray')
        self.load_ROI_poly_entry_guppy.place(x=1000+72,y=16)
        # save ROI poly
        self.save_ROI_poly_bttn_guppy = Button(self.tab3, text="Save ROI as", relief="raised",  width=10, command= self.save_ROI_poly_button_guppy)
        self.save_ROI_poly_bttn_guppy.place(x=1170,y=12)
        self.save_ROI_poly_entry_guppy = Entry(self.tab3, text='save roi entry', width=12, bg = 'lightgray')
        self.save_ROI_poly_entry_guppy.place(x=1170+85,y=16)
        self.save_ROI_poly_entry_guppy.delete(0,'end')
        self.save_ROI_poly_entry_guppy.insert(1,'roi_drawn')

        # code for camera table:
        self.camera_table_guppy = ttk.Treeview(self.tab3, columns=("cam_names"))
        self.camera_table_guppy.place(x=20, y = 500)
        self.camera_table_guppy.heading('#0', text='Cameras')
        self.camera_table_guppy.heading('cam_names', text='ID')
        self.camera_table_guppy.column("#0", width=150)
        self.camera_table_guppy.column("cam_names", width = 175)
        # 4/ bind to get cell selection
        self.camera_table_guppy.bind('<ButtonRelease-1>', self.selectCamera_guppy)

        # refresh camera button:
        self.refresh_camera_bttn_guppy = Button(self.tab3, text="Refresh cameras", relief="raised",  width=14, command= self.refresh_camera_button_guppy)
        self.refresh_camera_bttn_guppy.place(x=20,y=740)
        self.cam_list = []
        self.cam_ids = []
        self.cam_names = []
        self.selected_cam = None 
        self.selected_cam_id = None
        self.cam = None

        # select camera button:
        self.select_camera_bttn_guppy = Button(self.tab3, text="Select camera", relief="raised",  width=14, command= self.select_camera_button_guppy)
        self.select_camera_bttn_guppy.place(x=150,y=740)

        # selected camera:
        self.selected_camera_label_guppy = Label(self.tab3, text="Selected camera: ").place(x=20, y = 775)
        self.selected_camera_entry_guppy = Entry(self.tab3, text="", width=56)
        self.selected_camera_entry_guppy.place(x = 20, y = 805)

        # PREVIEW button:
        self.preview_bttn_guppy = Button(self.tab3, text="Preview", relief="raised",  width=8, command= self.preview_button_guppy)
        self.preview_bttn_guppy.place(x=20,y=835) 

        # ACQUIRE ONCE button:
        self.acquire_once_bttn_guppy = Button(self.tab3, text="Acquire Once", relief="raised",  width=12, command= self.acquire_once_button_guppy)
        self.acquire_once_bttn_guppy.place(x=97,y=835) 
        ## for preview video
        self.queue = SimpleQueue() # queue for video frames
        self.after_id = None
        self.is_streaming = None

        # ACQUIRE CONTINUOUSLY button:
        self.acquire_cont_bttn_guppy = Button(self.tab3, text="Acquire Cont.", relief="raised",  width=12, command= self.acquire_cont_button_guppy)
        self.acquire_cont_bttn_guppy.place(x=200,y=835) 

        # Abort button:
        self.abort_bttn_guppy = Button(self.tab3, text="Abort", relief="raised",  width=6, command= self.abort_button_guppy)
        self.abort_bttn_guppy.place(x=302,y=835) 

        # exposure 
        self.exposure_label_guppy = Label(self.tab3, text="Exposure: ").place(x=20, y = 875)
        self.exposure_entry_guppy = Entry(self.tab3, text="", width=18)
        self.exposure_entry_guppy.place(x = 20+70, y = 878)
        self.exposure_ok_bttn = Button(self.tab3, text="OK", relief="raised",  width=3, command= self.exposure_ok_button)
        self.exposure_ok_bttn.place(x=220,y=875)

        # frame for showing video
        self.lblVideo = tk.Label(self.tab3, image = tk.PhotoImage(), width = 500, height = 375, bg = 'black')
        self.lblVideo.place(x=1380, y = 20)

    #######################################################################
    ##### FIRST TAB FUNCTIONS: BROWSER ####################################
    #######################################################################
 
    def browse(self):
        self.folder_path = filedialog.askdirectory()
        self.refresh()

        if self.folder_path:
            if self.scan_bttn.config('relief')[-1] == 'sunken':
                t = Thread (target = self.scan_act)
                t.start()

    def refresh(self):
        if self.folder_path: # if path is not empty
            self.folder_entry.delete(0,'end')
            self.folder_entry.insert(0, self.folder_path)
            # list all files with .fits extension:
            self.file_names = []
            self.files_fullpath = glob.glob(self.folder_path + '/*.fits')
            for f in self.files_fullpath:
                name = f.split(self.folder_path)
                self.file_names.append(str(name[1]).replace('\\',"")) # make list of file names
            if self.file_names != self.file_names_old: # only act if file_names has changed
                # first clear table:
                self.file_table.delete(*self.file_table.get_children())
                # then repopulate:
                for i in range(len(self.file_names)):
                    id = str(len(self.file_names)-i)               
                    # then repopulate
                    self.file_table.insert("","end",text = id, values = str(self.file_names[len(self.file_names)-i-1]))
                self.file_names_old = self.file_names
            # udpate backup folder path
            self.folder_path_old = self.folder_path
        else:
            # if folder path is empty then revert to old folder path
            self.folder_path = self.folder_path_old

    def scan(self):
        if self.folder_path:
            if self.scan_bttn.config('relief')[-1] == 'sunken':
                self.scan_bttn.config(text='Scan')
                self.scan_bttn.config(relief="raised")
                self.scan_bttn.config(fg='black') 
                # if sunken then raise button and stop scan:
            else:
                self.scan_bttn.config(relief="sunken")  
                self.scan_bttn.config(text='Scan')
                self.scan_bttn.config(fg='silver')
                # if raised then sunken and start scan:
                t = Thread (target = self.scan_act)
                t.start()

    def scan_act(self):
            while True:
                if self.scan_bttn.config('relief')[-1] == 'sunken':
                    # if show new button is pressed then show new image:
                    if self.show_new_bttn.config('relief')[-1] == 'sunken':
                        # print('Scanning and showing new...')
                        # take last element of new file list
                        # compare file name
                        # if different then display, else do nothing
                        if self.folder_path: # if path is not empty
                            self.folder_entry.delete(0,'end')
                            self.folder_entry.insert(0, self.folder_path)
                            # list all files with .fits extension:
                            self.file_names_new = []
                            self.files_fullpath_new = glob.glob(self.folder_path + '/*.fits')

                            if len(self.files_fullpath_new) > 0:
                                for f in self.files_fullpath_new:
                                    name = f.split(self.folder_path)
                                    self.file_names_new.append(str(name[1]).replace('\\',"")) # make list of file names
                                if self.file_names_new != self.file_names: # if file_names has changed:
                                    # first clear table:
                                    self.file_table.delete(*self.file_table.get_children())
                                    # then repopulate:
                                    for i in range(len(self.file_names_new)):
                                        id = str(len(self.file_names_new)-i)               
                                        # then repopulate
                                        self.file_table.insert("","end",text = id, values = str(self.file_names_new[len(self.file_names_new)-i-1]))

                                    if len(self.file_names) > 0:
                                        if self.file_names_new[-1] != self.file_names[-1]: # display last image if last image different from previous last image
                                            # show new image:
                                            self.current_file_name = self.file_names_new[-1]
                                            # make fullpath of selected file
                                            self.current_file_fullpath = self.folder_path + '/' + self.current_file_name
                                            # update selected image textbox:
                                            self.selected_image_entry.delete(0,'end')
                                            self.selected_image_entry.insert(0,self.current_file_name)
                                            # now display image:
                                            if self.image_is_displayed: 
                                                self.image_is_displayed = False
                                                self.display_image()
                                            print(self.current_file_name)
                                            # next, show metadata:
                                            
                                            
                                            # # acquire run id
                                            # run_id = self.current_file_name.split('_')[0] 
                                            # # load run params from json file
                                            # run_parameters_path = self.folder_path + "/run_params_dump.json"
                                            # with open(run_parameters_path, 'r') as json_file:
                                            #     run_parameters_dict = json.load(json_file)   
                                            # self.params_for_selected_file = run_parameters_dict[run_id] # all params

                                            # for i in range(len(self.metadata_variables)):
                                            #     self.metadata_values[i] = str(self.params_for_selected_file[self.metadata_variables[i]])
                                            # # first clear metadata table:
                                            # self.params_table.delete(*self.params_table.get_children())
                                            # # then repopulate it
                                            # for i in range(len(self.metadata_variables)):
                                            #     param = str(self.metadata_variables[i])
                                            #     value = str(self.metadata_values[i])    
                                            #     # then repopulate
                                            #     self.params_table.insert("","end",text = param, values = value)


                                    #else: # if there is no file_names yet, then just display the last of file_names_new
                                self.file_names = self.file_names_new
                                self.files_fullpath = self.files_fullpath_new                 

                    else:
                        # print('Scanning but not showing new...')
                        self.refresh()
                        time.sleep(0.5)
                    time.sleep(1) # 1 second rep rate should be good since sequences are much longer
                else:
                    break 
        
    def show_new(self):
        if self.folder_path:
            if self.show_new_bttn.config('relief')[-1] == 'sunken':
                self.show_new_bttn.config(text='Show new')
                self.show_new_bttn.config(relief="raised")
                self.show_new_bttn.config(fg='black') 
            else:
                self.show_new_bttn.config(relief="sunken")  
                self.show_new_bttn.config(text='Show new')
                self.show_new_bttn.config(fg='silver')

    def delete(self):
        if self.current_file_name: # if there's a currently a file being selected then do something
            #print(self.current_file_fullpath)
            os.remove(self.current_file_fullpath)
            self.refresh()

    def OD_select(self):
        self.frame_type = 'OD'
        if self.current_file_fullpath:
            self.display_image()

        self.frame_type_entry.delete(0,'end')
        self.frame_type_entry.insert(1,self.frame_type)
        self.frame_type_entry.place(x=100, y = 390)
        
    def with_atoms_select(self):
        self.frame_type = 'With atoms'
        if self.current_file_fullpath:
            self.display_image()
        
        self.frame_type_entry.delete(0,'end')
        self.frame_type_entry.insert(1,self.frame_type)
        self.frame_type_entry.place(x=100, y = 390)

    def without_atoms_select(self):
        self.frame_type = 'Without atoms'
        if self.current_file_fullpath:
            self.display_image()
        
        self.frame_type_entry.delete(0,'end')
        self.frame_type_entry.insert(1,self.frame_type)
        self.frame_type_entry.place(x=100, y = 390)

    def dark_select(self):
        self.frame_type = 'Dark'
        if self.current_file_fullpath:
            self.display_image()
        
        self.frame_type_entry.delete(0,'end')
        self.frame_type_entry.insert(1,self.frame_type)
        self.frame_type_entry.place(x=100, y = 390)

    def FakeOD_select(self):
        self.frame_type = 'FakeOD'
        if self.current_file_fullpath:
            self.display_image()
        
        self.frame_type_entry.delete(0,'end')
        self.frame_type_entry.insert(1,self.frame_type)
        self.frame_type_entry.place(x=100, y = 390)

    def selectItem(self, event):
        curItem = self.file_table.focus()
        curItem = self.file_table.item(curItem)
        self.current_file_name = curItem['values'][0]
        # make fullpath of selected file
        self.current_file_fullpath = self.folder_path + '/' + self.current_file_name
        # update selected image textbox:
        self.selected_image_entry.delete(0,'end')
        self.selected_image_entry.insert(0,self.current_file_name)
        # now display image:
        self.display_image()
        # next, show metadata:
        # acquire run id
        run_id = self.current_file_name.split('_')[0] 
        # load run params from json file
        run_parameters_path = self.folder_path + "/run_params_dump.json"
        with open(run_parameters_path, 'r') as json_file:
            run_parameters_dict = json.load(json_file)   
        self.params_for_selected_file = run_parameters_dict[run_id] # all params

        for i in range(len(self.metadata_variables)):
            self.metadata_values[i] = str(self.params_for_selected_file[self.metadata_variables[i]])
        # first clear metadata table:
        self.params_table.delete(*self.params_table.get_children())
        # then repopulate it
        for i in range(len(self.metadata_variables)):
            param = str(self.metadata_variables[i])
            value = str(self.metadata_values[i])    
            # then repopulate
            self.params_table.insert("","end",text = param, values = value)

    def light_OK(self):
        self.min_scale = float(self.min_entry.get())
        self.max_scale = float(self.max_entry.get())
        self.brightness = int(self.brightness_entry.get())
        
        if self.current_file_fullpath:
            self.display_image()

    def add_param(self):
        new_param = str(self.param_entry.get())
        # check if exists in data structure for selected file and not in metadata_variables already
        if (new_param in self.params_for_selected_file) and not(new_param in self.metadata_variables):
            self.metadata_variables.append(new_param)

        # update table:
        self.metadata_values.append(str(self.params_for_selected_file[self.metadata_variables[-1]]))
        # first clear metadata table:
        self.params_table.delete(*self.params_table.get_children())
        # then repopulate it
        for i in range(len(self.metadata_variables)):
            param = str(self.metadata_variables[i])
            value = str(self.metadata_values[i])    
            # then repopulate
            self.params_table.insert("","end",text = param, values = value)

    def BEC_DoIt(self):
        # get parameters first:
        self.BEC_diameter = float(self.BEC_diameter_entry.get())
        self.BEC_TOF = float(self.BEC_TOF_entry.get())
        self.ax_trap_freq = float(self.ax_trap_freq_entry.get())
        self.rad_trap_freq = float(self.rad_trap_freq_entry.get())
        self.um_per_px = float(self.um_per_px_entry.get())
        r = self.BEC_diameter/2.0
        tof = self.BEC_TOF/1000.0 # units in seconds
        ax = self.ax_trap_freq
        rad = self.rad_trap_freq
        umpx = self.um_per_px
        hbar = 1.054e-34
        m = 23*(1.67e-27)
        omega = (2*np.pi*rad*2*np.pi*rad*2*np.pi*ax)**(1/3)
        a = 85*(0.529e-10)
        # calculate BEC atom count:
        self.BEC_count = ((m/2*(2*np.pi*rad)**2/(1 + (2*np.pi*rad*tof)**2))*(umpx*10**(-6)*r)**2)**(5/2)/(15*hbar**2*m**(1/2)*omega**3*a/2**(5/2))
        # display this on BEC count entry:
        self.BEC_count_entry.delete(0,'end')   
        self.BEC_count_entry.insert(0, str('{:.2e}'.format(self.BEC_count)))

    def Na_Catch_DoIt(self):
        
        # acquire lims for background
        x_min_bg = self.Na_Catch_background_X_min
        x_max_bg = self.Na_Catch_background_X_max
        y_min_bg = self.Na_Catch_background_Y_min
        y_max_bg = self.Na_Catch_background_Y_max

        # acquire lims for roi
        x_min_roi = self.Na_Catch_ROI_X_min
        x_max_roi = self.Na_Catch_ROI_X_max
        y_min_roi = self.Na_Catch_ROI_Y_min
        y_max_roi = self.Na_Catch_ROI_Y_max

        bg_area = (y_max_bg - y_min_bg)*(x_max_bg - x_min_bg)
        roi_area = (y_max_roi - y_min_roi)*(x_max_roi - x_min_roi)

        od_roi = (-np.log(safe_subtract(self.img[0,:,:], self.img[2,:,:])/safe_subtract(self.img[1,:,:], self.img[2,:,:])))
        od_roi = np.nan_to_num(od_roi)
        od_roi = np.clip(od_roi, 0, ABSORPTION_LIMIT)
        od_roi_cropped = od_roi[x_min_roi:x_max_roi, y_min_roi:y_max_roi] # just OD, but cropped

        od_bg = (-np.log(safe_subtract(self.img[0,:,:], self.img[2,:,:])/safe_subtract(self.img[1,:,:], self.img[2,:,:])))
        od_bg = np.nan_to_num(od_bg)
        od_bg = np.clip(od_bg, 0, ABSORPTION_LIMIT)
        od_bg_cropped = od_bg[x_min_bg:x_max_bg, y_min_bg:y_max_bg] # just OD, but cropped

        # integrate
        count_od = sum(sum(od_roi_cropped))
        count_bg = sum(sum(od_bg_cropped))

        # convert to bg corresponding to roi area:
        count_bg = int(count_bg*(roi_area/bg_area))
        # then calculate catch score
        self.Na_Catch_score = count_od - count_bg
        # display this on catch score entry:
        self.Na_Catch_score_entry.delete(0,'end')   
        self.Na_Catch_score_entry.insert(0, str('{:.2e}'.format(self.Na_Catch_score)))        

    def Na_Catch_BackgroundROI_Crop(self):
        def line_select_callback(eclick, erelease):
            'eclick and erelease are the press and release events'
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata

            self.Na_Catch_background_X_min = int(min(x1,x2))
            self.Na_Catch_background_X_max = int(max(x1,x2))
            self.Na_Catch_background_Y_min = int(min(y1,y2))
            self.Na_Catch_background_Y_max = int(max(y1,y2))

            self.Na_Catch_background_X_min_entry.delete(0,'end')   
            self.Na_Catch_background_X_min_entry.insert(0, str(self.Na_Catch_background_X_min))
            self.Na_Catch_background_X_max_entry.delete(0,'end')   
            self.Na_Catch_background_X_max_entry.insert(0, str(self.Na_Catch_background_X_max))
            self.Na_Catch_background_Y_min_entry.delete(0,'end')   
            self.Na_Catch_background_Y_min_entry.insert(0, str(self.Na_Catch_background_Y_min))
            self.Na_Catch_background_Y_max_entry.delete(0,'end')   
            self.Na_Catch_background_Y_max_entry.insert(0, str(self.Na_Catch_background_Y_max))

            # redraw image once done so that user has to click the crop bttn again to crop
            self.display_image()

        toggle_selector.RS = RectangleSelector(self.ax, line_select_callback,
        drawtype='box', useblit=True,
        button=[1,3], # don't use middle button
        minspanx=5, minspany=5,
        spancoords='pixels')
        plt.connect('key_press_event', toggle_selector)
        

    def Na_Catch_ROI_Crop(self):
        def line_select_callback(eclick, erelease):
            'eclick and erelease are the press and release events'
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata

            self.Na_Catch_ROI_X_min = int(min(x1,x2))
            self.Na_Catch_ROI_X_max = int(max(x1,x2))
            self.Na_Catch_ROI_Y_min = int(min(y1,y2))
            self.Na_Catch_ROI_Y_max = int(max(y1,y2))

            self.Na_Catch_ROI_X_min_entry.delete(0,'end')   
            self.Na_Catch_ROI_X_min_entry.insert(0, str(self.Na_Catch_ROI_X_min))
            self.Na_Catch_ROI_X_max_entry.delete(0,'end')   
            self.Na_Catch_ROI_X_max_entry.insert(0, str(self.Na_Catch_ROI_X_max))
            self.Na_Catch_ROI_Y_min_entry.delete(0,'end')   
            self.Na_Catch_ROI_Y_min_entry.insert(0, str(self.Na_Catch_ROI_Y_min))
            self.Na_Catch_ROI_Y_max_entry.delete(0,'end')   
            self.Na_Catch_ROI_Y_max_entry.insert(0, str(self.Na_Catch_ROI_Y_max))

            # redraw image once done so that user has to clip the crop bttn again to crop
            self.display_image()

        toggle_selector.RS = RectangleSelector(self.ax, line_select_callback,
        drawtype='box', useblit=True,
        button=[1,3], # don't use middle button
        minspanx=5, minspany=5,
        spancoords='pixels')
        plt.connect('key_press_event', toggle_selector)

    def LiLF_Crop(self):
        def line_select_callback(eclick, erelease):
            'eclick and erelease are the press and release events'
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata

            self.LiLF_X_min = int(min(x1,x2))
            self.LiLF_X_max = int(max(x1,x2))
            self.LiLF_Y_min = int(min(y1,y2))
            self.LiLF_Y_max = int(max(y1,y2))

            self.LiLF_X_min_entry.delete(0,'end')   
            self.LiLF_X_min_entry.insert(0, str(self.LiLF_X_min))
            self.LiLF_X_max_entry.delete(0,'end')   
            self.LiLF_X_max_entry.insert(0, str(self.LiLF_X_max))
            self.LiLF_Y_min_entry.delete(0,'end')   
            self.LiLF_Y_min_entry.insert(0, str(self.LiLF_Y_min))
            self.LiLF_Y_max_entry.delete(0,'end')   
            self.LiLF_Y_max_entry.insert(0, str(self.LiLF_Y_max))

            # redraw image once done so that user has to clip the crop bttn again to crop
            self.display_image()

        toggle_selector.RS = RectangleSelector(self.ax, line_select_callback,
        drawtype='box', useblit=True,
        button=[1,3], # don't use middle button
        minspanx=5, minspany=5,
        spancoords='pixels')
        plt.connect('key_press_event', toggle_selector)

    def LiLF_DoIt(self):
        # acquire lims:
        x_min = self.LiLF_X_min
        x_max = self.LiLF_X_max
        y_min = self.LiLF_Y_min
        y_max = self.LiLF_Y_max

        # params
        pixelsize = float(self.LiLF_pixel_size_entry.get())
        sigma = float(self.LiLF_cross_section_entry.get())
        Nsat = float(self.LiLF_sat_count_entry.get())

        od = (-np.log(safe_subtract(self.img[0,:,:], self.img[2,:,:])/safe_subtract(self.img[1,:,:], self.img[2,:,:])))
        ic =  safe_subtract(self.img[1,:,:], self.img[0,:,:])/Nsat

        # now clean od and ic:
        od = np.nan_to_num(od)
        # fix clipping
        od = np.clip(od, 0, ABSORPTION_LIMIT)

        od_cropped = od[x_min:x_max, y_min:y_max] # just OD, but cropped
        ic_cropped = ic[x_min:x_max, y_min:y_max]
        atomnumber_map = (ic_cropped+od_cropped)*pixelsize/sigma
        Li_atomnumber = sum(sum(atomnumber_map))
        self.LiLF_atom_number_entry.delete(0,'end')   
        self.LiLF_atom_number_entry.insert(0, str('{:.2e}'.format(Li_atomnumber)))

    def reset_view_button(self):
        # first stop scan and stop showing new:
        self.scan_bttn.config(relief="raised")
        self.scan_bttn.config(fg='black')
        self.show_new_bttn.config(relief="raised")
        self.show_new_bttn.config(fg='black')

        # then re draw canvas
        if self.img.any():
            # get dims of image
            dims = self.img[0,:,:].shape 
            x_limit = dims[1]
            y_limit = dims[0]

            # draw blank
            plt.close(self.fig)
            self.fig.clf()
            self.ax.cla()
            self.ax = self.fig.add_subplot(111)
            self.fig.subplots_adjust(left=0.05, bottom=0.04, right=0.98, top=0.94, wspace=0, hspace=0)
            self.canvas.draw_idle()
            time.sleep(0.5)

            # draw new
            self.ax.invert_yaxis()
            self.ax.imshow(self.frame, cmap='gray', vmin=0, vmax=2**15).set_clim(self.min_scale, self.max_scale)
            self.ax.set_xlim([0, x_limit])
            self.ax.set_ylim([0, y_limit])
            self.canvas.draw_idle()

    def ROI_poly_button(self):
        # first clear all rois:
        self.clear_ROI_poly_button()
        # now generate new one:
        self.roi = RoiPoly(fig = self.fig, ax = self.ax, color='r')
        # stop scan and show new:
        self.scan_bttn.config(relief="raised")
        self.scan_bttn.config(fg='black')
        self.show_new_bttn.config(relief="raised")
        self.show_new_bttn.config(fg='black')

    def clear_ROI_poly_button(self):
        self.roi  = None 
        self.display_roi()
        self.display_image()

    def load_ROI_poly_button(self):
        roi_load_filename = filedialog.askopenfilename()
        if roi_load_filename:
            file = open(roi_load_filename, 'rb')
            self.roi = pickle.load(file)
            file.close()
            self.load_ROI_poly_entry.delete(0,'end')
            self.load_ROI_poly_entry.insert(1,os.path.basename(roi_load_filename))

    def save_ROI_poly_button(self):
        if self.folder_path and self.roi:
            roi_save_file_name = self.save_ROI_poly_entry.get()
            name = self.folder_path+ "/" + roi_save_file_name
            fileObj = open(name, 'wb')
            pickle.dump(self.roi, fileObj)
            fileObj.close()

    def display_image(self):
        fits_image = fits.open(self.current_file_fullpath)
        # fits_image.info() # display fits image info
        self.img = fits_image[0].data
        fits_image.close()

        # get dims of image
        dims = self.img[0,:,:].shape 
        x_limit = dims[1]
        y_limit = dims[0]
        # get dims of current axes:
        [self.XMIN, self.XMAX] = self.ax.get_xlim()
        [self.YMIN, self.YMAX] = self.ax.get_ylim()

        # first close
        self.ax.clear()
        self.fig.clf()
        plt.close(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.invert_yaxis()
        time.sleep(0.5)
        print('Displaying image...')

        # then show image:
        frame_type = self.frame_type
        if frame_type == 'OD':
            self.frame = (-np.log(safe_subtract(self.img[0,:,:], self.img[2,:,:])/safe_subtract(self.img[1,:,:], self.img[2,:,:])))
            # clean image: using nan_to_num
            self.frame = np.nan_to_num(self.frame, nan=ABSORPTION_LIMIT)
            # fix clipping
            self.frame = np.clip(self.frame, 0, ABSORPTION_LIMIT)
            self.ax.imshow(self.frame, cmap='gray', vmin=0, vmax=2**15).set_clim(self.min_scale, self.max_scale)
            
            # zoom/pan perspective
            if (self.oldSizeX == x_limit) and (self.oldSizeY == y_limit):
                self.ax.set_xlim([self.XMIN, self.XMAX])
                self.ax.set_ylim([self.YMIN, self.YMAX])
            else:
                self.ax.set_xlim([0, x_limit])
                self.ax.set_ylim([0, y_limit])
            self.oldSizeX = x_limit
            self.oldSizeY = y_limit
            # end of zoom/pan perspective
            self.fig.subplots_adjust(left=0.05, bottom=0.04, right=0.98, top=0.94, wspace=0, hspace=0)
            self.canvas.draw_idle()
        else:
            if frame_type == 'FakeOD':
                self.frame = (safe_subtract(self.img[0,:,:], self.img[2,:,:])/safe_subtract(self.img[1,:,:], self.img[2,:,:]))
                # clean image: using nan_to_num
                self.frame = np.nan_to_num(self.frame)
                # fix clipping
                self.frame = np.clip(self.frame, 0, ABSORPTION_LIMIT)
                self.ax.imshow(self.frame, cmap='gray', vmin=0, vmax=2**15).set_clim(self.min_scale, self.max_scale)

                # zoom/pan perspective
                if (self.oldSizeX == x_limit) and (self.oldSizeY == y_limit):
                    self.ax.set_xlim([self.XMIN, self.XMAX])
                    self.ax.set_ylim([self.YMIN, self.YMAX])
                else:
                    self.ax.set_xlim([0, x_limit])
                    self.ax.set_ylim([0, y_limit])
                self.oldSizeX = x_limit
                self.oldSizeY = y_limit
                # end of zoom/pan perspective
                self.fig.subplots_adjust(left=0.05, bottom=0.04, right=0.98, top=0.94, wspace=0, hspace=0)
                self.canvas.draw_idle()
            else:
                if frame_type == 'With atoms':
                    self.frame = self.img[0,:,:]
                    # clean image: using nan_to_num
                    self.frame = np.nan_to_num(self.frame)
                    self.ax.imshow(self.frame, cmap='gray', vmin=0, vmax=2**self.brightness)  # need to adjust gray scale/colormap here with BRIGHTNESS variable
                    # zoom/pan perspective
                    if (self.oldSizeX == x_limit) and (self.oldSizeY == y_limit):
                        self.ax.set_xlim([self.XMIN, self.XMAX])
                        self.ax.set_ylim([self.YMIN, self.YMAX])
                    else:
                        self.ax.set_xlim([0, x_limit])
                        self.ax.set_ylim([0, y_limit])
                    self.oldSizeX = x_limit
                    self.oldSizeY = y_limit
                    # end of zoom/pan perspective
                    self.fig.subplots_adjust(left=0.05, bottom=0.04, right=0.98, top=0.94, wspace=0, hspace=0)
                    self.canvas.draw_idle()

                elif frame_type == 'Without atoms':
                    self.frame = self.img[1,:,:]
                    # clean image: using nan_to_num
                    self.frame = np.nan_to_num(self.frame)
                    self.ax.imshow(self.frame, cmap='gray', vmin=0, vmax=2**self.brightness)  # need to adjust gray scale/colormap here with BRIGHTNESS variable
                    # zoom/pan perspective
                    if (self.oldSizeX == x_limit) and (self.oldSizeY == y_limit):
                        self.ax.set_xlim([self.XMIN, self.XMAX])
                        self.ax.set_ylim([self.YMIN, self.YMAX])
                    else:
                        self.ax.set_xlim([0, x_limit])
                        self.ax.set_ylim([0, y_limit])
                    self.oldSizeX = x_limit
                    self.oldSizeY = y_limit
                    # end of zoom/pan perspective
                    self.fig.subplots_adjust(left=0.05, bottom=0.04, right=0.98, top=0.94, wspace=0, hspace=0)
                    self.canvas.draw_idle()

                elif frame_type == 'Dark':
                    self.frame = self.img[2,:,:]
                    # clean image: using nan_to_num
                    self.frame = np.nan_to_num(self.frame)
                    self.ax.imshow(self.frame, cmap='gray', vmin=0, vmax=2**self.brightness)  # need to adjust gray scale/colormap here with BRIGHTNESS variable
                    # zoom/pan perspective
                    if (self.oldSizeX == x_limit) and (self.oldSizeY == y_limit):
                        self.ax.set_xlim([self.XMIN, self.XMAX])
                        self.ax.set_ylim([self.YMIN, self.YMAX])
                    else:
                        self.ax.set_xlim([0, x_limit])
                        self.ax.set_ylim([0, y_limit])
                    self.oldSizeX = x_limit
                    self.oldSizeY = y_limit
                    # end of zoom/pan perspective
                    self.fig.subplots_adjust(left=0.05, bottom=0.04, right=0.98, top=0.94, wspace=0, hspace=0)
                    self.canvas.draw_idle()

                else:
                    self.frame = (-np.log(safe_subtract(self.img[0,:,:], self.img[2,:,:])/safe_subtract(self.img[1,:,:], self.img[2,:,:])))
                    # clean image: using nan_to_num
                    self.frame = np.nan_to_num(self.frame)
                    self.ax.imshow(self.frame, cmap='gray', vmin=0, vmax=2**15).set_clim(self.min_scale, self.max_scale)
                    # zoom/pan perspective
                    if (self.oldSizeX == x_limit) and (self.oldSizeY == y_limit):
                        self.ax.set_xlim([self.XMIN, self.XMAX])
                        self.ax.set_ylim([self.YMIN, self.YMAX])
                    else:
                        self.ax.set_xlim([0, x_limit])
                        self.ax.set_ylim([0, y_limit])
                    self.oldSizeX = x_limit
                    self.oldSizeY = y_limit
                    # end of zoom/pan perspective
                    self.fig.subplots_adjust(left=0.05, bottom=0.04, right=0.98, top=0.94, wspace=0, hspace=0)
                    self.canvas.draw_idle()

        # now display roi if there is one:
        self.display_roi()
        # change display status to True to allow the next shot in queue
        self.image_is_displayed = True
    
    def display_roi(self):
        if self.roi:
            #coords = list(zip(self.roi.x, self.roi.y))
            #print(coords)
            self.roi_xs = self.roi.x
            self.roi_ys = self.roi.y
            self.roi_xs.append(self.roi_xs[0])
            self.roi_ys.append(self.roi_ys[0])
            self.ax.plot(self.roi_xs, self.roi_ys, color = 'r')
            self.canvas.draw_idle()

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
                    # t = Thread (target = self.acquire)
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
                # t = Thread (target = self.acquire)
                t = Thread (target = self.acquire)
                t.start()

    def acquire_test(self):
        while True:
            print('fake acquiring...')
            time.sleep(5)
            if self.acquisition_state == "STOPPED":  
                break
            

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

    def go_to_button(self):
        if self.folder_name:
            camera_saving_folder_pathname, saving_location_root_pathname, image_specification_list = saver.load_config()
            user_entered_name = self.folder_name
            is_dryrun = user_entered_name == "dryrun"
            self.folder_path = saver.initialize_savefolder_portal(saving_location_root_pathname, user_entered_name, is_dryrun)
            
            # now basically hit browse() and set self.folder_path to this if folder exists:
            if os.path.isdir(self.folder_path):
                self.refresh()
                if self.scan_bttn.config('relief')[-1] == 'sunken':
                    t = Thread (target = self.scan_act)
                    t.start()

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
            self.folder_name = 'dryrun'
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

    # IMAGING RESONANCE FUNCTIONS:
    def browse_res_button(self):
        self.image_processing_folder_path = filedialog.askdirectory()
        if self.image_processing_folder_path:
            self.res_image_folder_entry.delete(0,'end')
            self.res_image_folder_entry.insert(0, self.image_processing_folder_path)
            # print(self.image_processing_folder_path)
            self.enable_resonance_imaging_mode_buttons()

    def enable_resonance_imaging_mode_buttons(self):
        # enable buttons:
        self.side_lf_bttn["state"] = NORMAL
        self.side_hf_bttn["state"] = NORMAL
        self.TopA_bttn["state"] = NORMAL
        self.TopB_bttn["state"] = NORMAL
        self.TopAB_bttn["state"] = NORMAL
        self.analyze_bttn["state"] = DISABLED

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
    
    # rf resonance processing:
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

    # hybrid top analysis
    def browse_hybrid_button(self):
        self.hybrid_processing_folder_path = filedialog.askdirectory()
        if self.hybrid_processing_folder_path:
            self.hybrid_folder_entry.delete(0,'end')
            self.hybrid_folder_entry.insert(0, self.hybrid_processing_folder_path)
            self.abs_img_bttn["state"] = NORMAL
            self.polrot_img_bttn["state"] = NORMAL

    def hybrid_analyze_button(self):  
        hybrid_top_processing.main_after_inputs(self.hybrid_processing_folder_path, self.hybrid_imaging_mode)        

    def abs_img(self):
        if self.abs_img_bttn.config('relief')[-1] == 'sunken':
            self.abs_img_bttn.config(relief="raised")
            self.abs_img_bttn.config(fg='black')
            
            self.abs_img_bttn["state"] = NORMAL
            self.polrot_img_bttn["state"] = NORMAL
            self.hybrid_analyze_bttn["state"] = DISABLED   
        else:
            self.abs_img_bttn.config(relief="sunken")  
            self.abs_img_bttn.config(fg='red')
            self.hybrid_imaging_mode = 'abs'
            # enable buttons:
            self.polrot_img_bttn["state"] = DISABLED
            self.hybrid_analyze_bttn["state"] = NORMAL

    def polrot_img(self):
        if self.polrot_img_bttn.config('relief')[-1] == 'sunken':
            self.polrot_img_bttn.config(relief="raised")
            self.polrot_img_bttn.config(fg='black')
            
            self.polrot_img_bttn["state"] = NORMAL
            self.abs_img_bttn["state"] = NORMAL
            self.hybrid_analyze_bttn["state"] = DISABLED   
        else:
            self.polrot_img_bttn.config(relief="sunken")  
            self.polrot_img_bttn.config(fg='red')
            self.hybrid_imaging_mode = 'polrot'
            # enable buttons:
            self.abs_img_bttn["state"] = DISABLED
            self.hybrid_analyze_bttn["state"] = NORMAL

    #######################################################################
    ##### SECOND TAB FUNCTIONS: LIVE ANALYSIS #############################
    #######################################################################
    
    def browse_live_analysis(self):
        self.folder_path_live_analysis = filedialog.askdirectory()
        self.refresh_live_analysis()
        
        if self.folder_path_live_analysis:
            self.enable_image_type_buttons()

    def refresh_live_analysis(self):
        if self.folder_path_live_analysis: # if path is not empty
            self.folder_entry_live_analysis.delete(0,'end')
            self.folder_entry_live_analysis.insert(0, self.folder_path_live_analysis)
            # list all files with .fits extension:
            self.file_names_live_analysis = []
            self.files_fullpath_live_analysis = glob.glob(self.folder_path_live_analysis + '/*.fits')
            for f in self.files_fullpath_live_analysis:
                name = f.split(self.folder_path_live_analysis)
                self.file_names_live_analysis.append(str(name[1]).replace('\\',"")) # make list of file names
            if self.file_names_live_analysis != self.file_names_old_live_analysis: # only act if file_names has changed
                # first clear table:
                self.file_table_live_analysis.delete(*self.file_table_live_analysis.get_children())
                # then repopulate:
                for i in range(len(self.file_names_live_analysis)):
                    id = str(len(self.file_names_live_analysis)-i)               
                    # then repopulate
                    self.file_table_live_analysis.insert("","end",text = id, values = str(self.file_names_live_analysis[len(self.file_names_live_analysis)-i-1]))
                self.file_names_old_live_analysis = self.file_names_live_analysis
            # udpate backup folder path
            self.folder_path_old_live_analysis = self.folder_path_live_analysis
        else:
            # if folder path is empty then revert to old folder path
            self.folder_path_live_analysis = self.folder_path_old_live_analysis

    def delete_live_analysis(self):
        if self.current_file_name_live_analysis: # if there's a currently a file being selected then do something
            os.remove(self.current_file_fullpath_live_analysis)
            self.refresh_live_analysis()
    
    def display_image_live_analysis(self):
        # this is the lighter version of the full display_image method
        fits_image = fits.open(self.current_file_fullpath_live_analysis)
        # fits_image.info() # display fits image info
        self.img_live_analysis = fits_image[0].data
        fits_image.close()

        # get dims of image
        dims = self.img_live_analysis[0,:,:].shape 
        x_limit = dims[1]
        y_limit = dims[0]
        # get dims of current axes:
        [self.XMIN_live_analysis, self.XMAX_live_analysis] = self.ax_image_viewer_live_analysis.get_xlim()
        [self.YMIN_live_analysis, self.YMAX_live_analysis] = self.ax_image_viewer_live_analysis.get_ylim()

        # first close
        self.ax_image_viewer_live_analysis.cla()
        self.image_viewer_live_analysis.clf()
        plt.close(self.fig_live_analysis)
        self.ax_image_viewer_live_analysis = self.image_viewer_live_analysis.add_subplot(111)
        self.ax_image_viewer_live_analysis.invert_yaxis()

        # show images only in FakeOD. This is only for ROI selection and image checking... nothing fancy here
        self.frame_live_analysis = (safe_subtract(self.img_live_analysis[0,:,:], self.img_live_analysis[2,:,:])/safe_subtract(self.img_live_analysis[1,:,:], self.img_live_analysis[2,:,:]))
        # clean image: using nan_to_num
        self.frame_live_analysis = np.nan_to_num(self.frame_live_analysis)
        # fix clipping
        self.frame_live_analysis = np.clip(self.frame_live_analysis, 0, ABSORPTION_LIMIT)
        min_scale = 0
        max_scale = 1.3
        self.ax_image_viewer_live_analysis.imshow(self.frame_live_analysis, cmap='gray', vmin=0, vmax=2**15).set_clim(min_scale, max_scale)

        # zoom/pan perspective
        if (self.oldSizeX_live_analysis == x_limit) and (self.oldSizeY_live_analysis == y_limit):
            self.ax_image_viewer_live_analysis.set_xlim([self.XMIN_live_analysis, self.XMAX_live_analysis])
            self.ax_image_viewer_live_analysis.set_ylim([self.YMIN_live_analysis, self.YMAX_live_analysis])
        else:
            self.ax_image_viewer_live_analysis.set_xlim([0, x_limit])
            self.ax_image_viewer_live_analysis.set_ylim([0, y_limit])
        self.oldSizeX_live_analysis = x_limit
        self.oldSizeY_live_analysis = y_limit
        # end of zoom/pan perspective
        # reset title
        self.ax_image_viewer_live_analysis.set_title('Image viewer')
        # self.image_viewer_live_analysis.subplots_adjust(left=0.05, bottom=0.04, right=0.98, top=0.94, wspace=0, hspace=0)
        self.canvas_image_viewer_live_analysis.draw_idle()


    def selectItem_live_analysis(self, event):
        curItem = self.file_table_live_analysis.focus()
        curItem = self.file_table_live_analysis.item(curItem)
        self.current_file_name_live_analysis = curItem['values'][0]
        # make fullpath of selected file
        self.current_file_fullpath_live_analysis = self.folder_path_live_analysis + '/' + self.current_file_name_live_analysis
        # update selected image textbox:
        self.selected_image_entry_live_analysis.delete(0,'end')
        self.selected_image_entry_live_analysis.insert(0,self.current_file_name_live_analysis)

        self.confirm_roi_and_norm_box_bttn["state"] = NORMAL
        
        # next, show image in image viewer...
        self.display_image_live_analysis()

        # next, show metadata:
        # acquire run id
        run_id = self.current_file_name_live_analysis.split('_')[0] 
        # load run params from json file
        run_parameters_path = self.folder_path_live_analysis + "/run_params_dump.json"
        with open(run_parameters_path, 'r') as json_file:
            run_parameters_dict = json.load(json_file)   
        self.params_for_selected_file_live_analysis = run_parameters_dict[run_id] # all params

        for i in range(len(self.metadata_variables_live_analysis)):
            self.metadata_values_live_analysis[i] = str(self.params_for_selected_file_live_analysis[self.metadata_variables_live_analysis[i]])
        # first clear metadata table:
        self.params_table_live_analysis.delete(*self.params_table_live_analysis.get_children())
        # then repopulate it
        for i in range(len(self.metadata_variables_live_analysis)):
            param = str(self.metadata_variables_live_analysis[i])
            value = str(self.metadata_values_live_analysis[i])    
            # then repopulate
            self.params_table_live_analysis.insert("","end",text = param, values = value)

    def add_param_live_analysis(self):
        new_param = str(self.param_entry_live_analysis.get())
        # check if exists in data structure for selected file and not in metadata_variables already
        if (new_param in self.params_for_selected_file_live_analysis) and not(new_param in self.metadata_variables_live_analysis):
            self.metadata_variables_live_analysis.append(new_param)

        # update table:
        self.metadata_values_live_analysis.append(str(self.params_for_selected_file_live_analysis[self.metadata_variables_live_analysis[-1]]))
        # first clear metadata table:
        self.params_table_live_analysis.delete(*self.params_table_live_analysis.get_children())
        # then repopulate it
        for i in range(len(self.metadata_variables_live_analysis)):
            param = str(self.metadata_variables_live_analysis[i])
            value = str(self.metadata_values_live_analysis[i])    
            # then repopulate
            self.params_table_live_analysis.insert("","end",text = param, values = value)

    def choose_figure_live_analysis(self, event):
        self.current_figure_live_analysis = self.chosen_figure_live_analysis.get()
        # clear "vs variable entry":
        self.vs_variable_entry_live_analysis.delete(0,'end')   
        self.vs_variable_entry_live_analysis.insert(0, "") 

        # update plotting variables status box:
        fig = self.current_figure_live_analysis # should be of the form 'Figure X'
        index = int(fig.split(' ')[-1]) - 1
        
        if self.figure_plotting_info[index]:
            x_var = self.figure_plotting_info[index][0]
            y_var = self.figure_plotting_info[index][1]
            self.plotting_variables_entry_live_analysis.delete(0,'end')   
            self.plotting_variables_entry_live_analysis.insert(0, 'Fig ' + str(index+1) + ': ' +  y_var + ' vs. ' + x_var) 
        else:
            self.plotting_variables_entry_live_analysis.delete(0,'end')   
            self.plotting_variables_entry_live_analysis.insert(0, "") 

        # then update variable boxes:
        # change X variable to...
        # change Y variable to...

    def choose_plotting_quantity_live_analysis(self, event):
        self.current_plotting_quantity_live_analysis = self.plotting_quantity_live_analysis.get()

    def choose_vs_quantity_live_analysis(self, event):
        self.current_vs_quantity_live_analysis = self.vs_quantity_live_analysis.get()

        x_var = self.vs_quantity_live_analysis.get()
        y_var = self.current_plotting_quantity_live_analysis
        fig = self.current_figure_live_analysis # should be of the form 'Figure X'
        index = int(fig.split(' ')[-1]) - 1

        self.figure_plotting_info[index] = [x_var, y_var]
        print(self.figure_plotting_info)
        # update plotting variables status box:
        self.plotting_variables_entry_live_analysis.delete(0,'end')   
        self.plotting_variables_entry_live_analysis.insert(0, 'Fig ' + str(index+1) + ': ' +  y_var + ' vs. ' + x_var) 

        # next update titles and axis labels only for x vs. y data:
        for ax in self.ax_list:
            idx = self.ax_list.index(ax)
            if self.figure_plotting_info[idx] and len(self.figure_plotting_info[idx]) == 2:
                xlabel = self.figure_plotting_info[idx][0]
                ylabel = self.figure_plotting_info[idx][1]
                title  = self.figure_plotting_info[idx][1] + ' vs ' + self.figure_plotting_info[idx][0]
                ax.set_xlabel(xlabel)
                ax.set_ylabel(ylabel)
                ax.set_title(title)
                self.canvas_live_analysis.draw_idle()

    def vs_variable_ok_button_live_analysis(self):
        x_var = self.vs_variable_entry_live_analysis.get()
        y_var = self.current_plotting_quantity_live_analysis
        fig = self.current_figure_live_analysis # should be of the form 'Figure X'
        index = int(fig.split(' ')[-1]) - 1

        # check if exists in data structure for selected file then execute
        if x_var in self.params_for_selected_file_live_analysis:
            # syntax is list of [x,y]
            self.figure_plotting_info[index] = [x_var, y_var]
            print(self.figure_plotting_info)
            # update plotting variables status box:
            self.plotting_variables_entry_live_analysis.delete(0,'end')   
            self.plotting_variables_entry_live_analysis.insert(0, 'Fig ' + str(index+1) + ': ' +  y_var + ' vs. ' + x_var) 

            # next update titles and axis labels
            for ax in self.ax_list:
                idx = self.ax_list.index(ax)
                if self.figure_plotting_info[idx] and len(self.figure_plotting_info[idx]) == 2:
                    xlabel = self.figure_plotting_info[idx][0]
                    ylabel = self.figure_plotting_info[idx][1]
                    title  = self.figure_plotting_info[idx][1] + ' vs ' + self.figure_plotting_info[idx][0]
                    ax.set_xlabel(xlabel)
                    ax.set_ylabel(ylabel)
                    ax.set_title(title)
                    self.canvas_live_analysis.draw_idle()        

    def live_analysis_ROI_Crop(self):
        def line_select_callback(eclick, erelease):
            'eclick and erelease are the press and release events'
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata

            self.X_min_live_analysis = int(min(x1,x2))
            self.X_max_live_analysis = int(max(x1,x2))
            self.Y_min_live_analysis = int(min(y1,y2))
            self.Y_max_live_analysis = int(max(y1,y2))

            self.X_min_entry_live_analysis.delete(0,'end')   
            self.X_min_entry_live_analysis.insert(0, str(self.X_min_live_analysis))
            self.X_max_entry_live_analysis.delete(0,'end')   
            self.X_max_entry_live_analysis.insert(0, str(self.X_max_live_analysis))
            self.Y_min_entry_live_analysis.delete(0,'end')   
            self.Y_min_entry_live_analysis.insert(0, str(self.Y_min_live_analysis))
            self.Y_max_entry_live_analysis.delete(0,'end')   
            self.Y_max_entry_live_analysis.insert(0, str(self.Y_max_live_analysis))

            # redraw image once done so that user has to clip the crop bttn again to crop
            self.display_image_live_analysis()

        toggle_selector.RS = RectangleSelector(self.ax_image_viewer_live_analysis, line_select_callback,
        drawtype='box', useblit=True,
        button=[1,3], # don't use middle button
        minspanx=5, minspany=5,
        spancoords='pixels')
        plt.connect('key_press_event', toggle_selector)

    def live_analysis_norm_box_Crop(self):
        def line_select_callback(eclick, erelease):
            'eclick and erelease are the press and release events'
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata

            self.norm_box_X_min_live_analysis = int(min(x1,x2))
            self.norm_box_X_max_live_analysis = int(max(x1,x2))
            self.norm_box_Y_min_live_analysis = int(min(y1,y2))
            self.norm_box_Y_max_live_analysis = int(max(y1,y2))

            self.norm_box_X_min_entry_live_analysis.delete(0,'end')   
            self.norm_box_X_min_entry_live_analysis.insert(0, str(self.norm_box_X_min_live_analysis))
            self.norm_box_X_max_entry_live_analysis.delete(0,'end')   
            self.norm_box_X_max_entry_live_analysis.insert(0, str(self.norm_box_X_max_live_analysis))
            self.norm_box_Y_min_entry_live_analysis.delete(0,'end')   
            self.norm_box_Y_min_entry_live_analysis.insert(0, str(self.norm_box_Y_min_live_analysis))
            self.norm_box_Y_max_entry_live_analysis.delete(0,'end')   
            self.norm_box_Y_max_entry_live_analysis.insert(0, str(self.norm_box_Y_max_live_analysis))

            # redraw image once done so that user has to clip the crop bttn again to crop
            self.display_image_live_analysis()

        toggle_selector.RS = RectangleSelector(self.ax_image_viewer_live_analysis, line_select_callback,
        drawtype='box', useblit=True,
        button=[1,3], # don't use middle button
        minspanx=5, minspany=5,
        spancoords='pixels')
        plt.connect('key_press_event', toggle_selector)


    def analyze_live_button(self):
        if self.analyze_live_bttn.config('relief')[-1] == 'sunken': # if RUNNING: this initiates PAUSE
            if self.current_measurement: # if there exists a current measurement:
                self.analyze_live_bttn.config(text='CONTINUE ANALYSIS')
                self.analyze_live_bttn.config(relief="raised") # this halts the analysis
                self.analyze_live_bttn.config(fg='red')
                self.confirm_roi_and_norm_box_bttn["state"] = DISABLED
            
            # enable selected buttons:
            self.vs_variable_ok_bttn_live_analysis["state"] = NORMAL
            self.plotting_quantity_live_analysis_menu["state"] = NORMAL
            self.vs_quantity_live_analysis_menu["state"] = NORMAL
            self.plot_density_live_analysis_menu["state"] = NORMAL
            self.vs_variable_entry_live_analysis["state"] = NORMAL

        else: # if not running... then either start new analysis or continue current analysis:

            if self.folder_path_live_analysis: # check if folder path is not empty
                
                # first, disable all other buttons:
                self.top_double_bttn["state"] = DISABLED
                self.side_lm_bttn["state"] = DISABLED
                self.side_hm_bttn["state"] = DISABLED
                self.confirm_roi_and_norm_box_bttn["state"] = DISABLED
                self.vs_variable_ok_bttn_live_analysis["state"] = DISABLED
                self.plotting_quantity_live_analysis_menu["state"] = DISABLED
                self.vs_quantity_live_analysis_menu["state"] = DISABLED
                self.vs_variable_entry_live_analysis["state"] = DISABLED
                self.plot_density_live_analysis_menu["state"] = DISABLED
                self.reset_fields_analysis_live_bttn["state"] = DISABLED

                # disable browse, refresh, and del buttons too:
                self.browse_bttn_live_analysis["state"] = DISABLED
                self.refresh_bttn_live_analysis["state"] = DISABLED
                self.delete_bttn_live_analysis["state"] = DISABLED

                # extract quantities to be measured by analysis:
                self.quantities_to_be_measured = []
                for plot in self.figure_plotting_info:
                    if plot != None and len(plot) == 2: # if this element is not None and of form [x,y], then wire it to a known add_to_live_analyses function
                        if plot[0] in MEASURE_QUANTITIES:
                            self.quantities_to_be_measured.append(plot[0])
                        if plot[1] in MEASURE_QUANTITIES:
                            self.quantities_to_be_measured.append(plot[1])
                    if plot != None and len(plot) == 1: # if this element is not None and of form [image] then same thing...
                        if plot[0] in list(DENSITIES.keys()):
                            self.quantities_to_be_measured.append(plot[0])

                self.quantities_to_be_measured = list(set(self.quantities_to_be_measured))

                print('Quantities to be measured:' )
                print(self.quantities_to_be_measured)

                if (self.current_measurement == None) and (self.analyze_live_bttn["text"] == 'START ANALYSIS'): # if there's no measurement ie can start analysis, then start analysis
                    # create measurement object
                    self.current_measurement = measurement.Measurement(measurement_directory_path = self.folder_path_live_analysis, 
                                                                        hold_images_in_memory = False, 
                                                                        imaging_type = self.image_type,
                                                                        run_parameters_verbose = True, 
                                                                        is_live = True)
                    # next, set ROI and norm box:
                    #Initialize norm box & roi
                    self.current_measurement.set_ROI(box_coordinates = [self.roi_X_min, 
                                                                        self.roi_Y_min, 
                                                                        self.roi_X_max, 
                                                                        self.roi_Y_max])

                    self.current_measurement.set_norm_box(box_coordinates = [self.norm_box_X_min, 
                                                                                self.norm_box_Y_min, 
                                                                                self.norm_box_X_max, 
                                                                                self.norm_box_Y_max])
                    
                if self.quantities_to_be_measured:
                    # change button state to PAUSE
                    self.analyze_live_bttn.config(text='PAUSE')
                    self.analyze_live_bttn.config(relief="sunken")
                    self.analyze_live_bttn.config(fg='red')
                    self.analyze_live_bttn["state"] = NORMAL
                    self.stop_analyze_live_bttn["state"] = NORMAL
                    # change END ANALYSIS button to red
                    self.stop_analyze_live_bttn.config(fg='red')

                    # list of added density analysis functions:
                    added_density_analysis_fns = []

                    # now add quantities to be measured to live analysis:
                    for q in self.quantities_to_be_measured:
                        if q in MEASURE_QUANTITIES:
                            index_q = MEASURE_QUANTITIES.index(q)
                            # see if q requires density calculation: no if doing pixel sum
                            if 'Pixel' in q:
                                self.current_measurement.add_to_live_analyses(ANALYSIS_FUNCTIONS[index_q], q, fun_kwargs = None, run_filter = None)
                            else: # use q as key in TO_DENSITY dict to retrieve appropriate analysis function
                                # two cases: polrot and non-polrot
                                if 'PR' not in q:
                                    # get density
                                    self.current_measurement.add_to_live_analyses(TO_DENSITY[q], q+'density')
                                    # gt counts from density
                                    self.current_measurement.add_to_live_analyses(ANALYSIS_FUNCTIONS[index_q], q, fun_kwargs = {'stored_density_name': q + 'density'})    
                                    added_density_analysis_fns.append(TO_DENSITY[q].__name__)
                                else: # if polrot densities have to be extracted:
                                    if analysis_functions.get_atom_densities_top_polrot.__name__ not in added_density_analysis_fns:
                                        # get polrot density
                                        self.current_measurement.add_to_live_analyses(analysis_functions.get_atom_densities_top_polrot, ('Density Top A (PR)', 'Density Top B (PR)')) 
                                        # get counts from polrot density
                                        self.current_measurement.add_to_live_analyses(analysis_functions.get_atom_counts_top_polrot, ('Counts Top A (PR)', 'Counts Top B (PR)'), 
                                                                                    fun_kwargs = {'first_stored_density_name': 'Density Top A (PR)', 'second_stored_density_name': 'Density Top B (PR)'})    
                                        added_density_analysis_fns.append(analysis_functions.get_atom_densities_top_polrot.__name__)

                        elif q in list(DENSITIES.keys()):
                            index_q = list(DENSITIES.keys()).index(q)
                            if DENSITIES[q].__name__ not in added_density_analysis_fns: 
                                if 'PR' not in q:
                                    self.current_measurement.add_to_live_analyses(DENSITIES[q], q)
                                    added_density_analysis_fns.append(DENSITIES[q].__name__)
                                else:
                                    if 'Box Exp' in q:
                                        self.current_measurement.add_to_live_analyses(analysis_functions.get_hybrid_trap_densities_along_harmonic_axis, 
                                                                                        ('positions_first', 'densities_first', 'positions_second', 'densities_second'))
                                        added_density_analysis_fns.append(analysis_functions.get_hybrid_trap_densities_along_harmonic_axis.__name__)
                                    else:
                                        self.current_measurement.add_to_live_analyses(analysis_functions.get_atom_densities_top_polrot, ('Density Top A (PR)', 'Density Top B (PR)'))
                                        added_density_analysis_fns.append(analysis_functions.get_atom_densities_top_polrot.__name__)

                    
                    print('Added density analysis functions:' )
                    print(added_density_analysis_fns)

                    # BEGIN LIVE ANALYSIS
                    if self.current_measurement:
                        # initialize tracker object:
                        self.tracker_fig_1 = None
                        self.tracker_fig_2 = None
                        self.tracker_fig_3 = None
                        self.tracker_fig_4 = None
                        self.tracker_list = [self.tracker_fig_1, self.tracker_fig_2, self.tracker_fig_3, self.tracker_fig_4]

                        # complete refresh of axes:
                        # close figure and reopen:
                        self.fig_live_analysis.clf()
                        self.canvas_live_analysis.draw_idle()

                        self.ax1_live_analysis = self.fig_live_analysis.add_subplot(221)
                        self.ax1_live_analysis.set_xlabel('X')
                        self.ax1_live_analysis.set_ylabel('Y')
                        self.ax1_live_analysis.set_title('Axes 1')

                        self.ax2_live_analysis = self.fig_live_analysis.add_subplot(222)
                        self.ax2_live_analysis.set_xlabel('X')
                        self.ax2_live_analysis.set_ylabel('Y')
                        self.ax2_live_analysis.set_title('Axes 2')

                        self.ax3_live_analysis = self.fig_live_analysis.add_subplot(223)
                        self.ax3_live_analysis.set_xlabel('X')
                        self.ax3_live_analysis.set_ylabel('Y')
                        self.ax3_live_analysis.set_title('Axes 3')

                        self.ax4_live_analysis = self.fig_live_analysis.add_subplot(224)
                        self.ax4_live_analysis.set_xlabel('X')
                        self.ax4_live_analysis.set_ylabel('Y')
                        self.ax4_live_analysis.set_title('Axes 4')

                        self.ax_list = [self.ax1_live_analysis, self.ax2_live_analysis, self.ax3_live_analysis, self.ax4_live_analysis]
                        self.canvas_live_analysis.draw_idle()

                        # begin live analysis thread:
                        t = Thread (target = self.live_analysis_act)
                        t.start()                  

    def live_analysis_act(self):
        loop_counter = 0
        while self.analyze_live_bttn.config('relief')[-1] == 'sunken' and self.current_measurement:
            #Refresh the parameters json
            if loop_counter % 10 == 0:
                parameters_json_pathname = os.path.join(self.current_measurement.measurement_directory_path, "run_params_dump.json")
                satyendra_loading_functions.force_refresh_file(parameters_json_pathname)
            # udpate measurement
            self.current_measurement.update(update_runs = True, update_badshots = True, update_analyses = True, overwrite_existing_analysis = False, 
                override_existing_badshots = False, ignore_badshots = True, catch_errors = True, print_progress = True)           

            # now print out data for each plot:
            for f in range(len(LIVE_FIGURES)): 
                if self.figure_plotting_info[f] and len(self.figure_plotting_info[f]) == 2:                    
                    # two cases: non-PR counts and PR counts: have to treat counts PR a little differently since PR_densities return both A and B
                    x_var_name = self.figure_plotting_info[f][0]
                    y_var_name = self.figure_plotting_info[f][1]

                    # now sort out plotting data:
                    if not (x_var_name in MEASURE_QUANTITIES) and y_var_name in MEASURE_QUANTITIES:
                        x_data, y_data = self.current_measurement.get_parameter_analysis_value_pair_from_runs(x_var_name, y_var_name)
                    elif x_var_name in MEASURE_QUANTITIES and not y_var_name in MEASURE_QUANTITIES:
                        y_data, x_data = self.current_measurement.get_parameter_analysis_value_pair_from_runs(y_var_name, x_var_name)
                    elif x_var_name in MEASURE_QUANTITIES and y_var_name in MEASURE_QUANTITIES: 
                        def no_err_run_filter(my_measurement, my_run):
                            return (my_run.analysis_results[x_var_name] != measurement.Measurement.ANALYSIS_ERROR_INDICATOR_STRING and 
                                    my_run.analysis_results[y_var_name] != measurement.Measurement.ANALYSIS_ERROR_INDICATOR_STRING)
                        x_data = self.current_measurement.get_analysis_value_from_runs(x_var_name, run_filter = no_err_run_filter) 
                        y_data = self.current_measurement.get_analysis_value_from_runs(y_var_name, run_filter = no_err_run_filter) 
                    else:
                        x_data = self.current_measurement.get_parameter_value_from_runs(x_var_name) 
                        y_data = self.current_measurement.get_parameter_value_from_runs(y_var_name)
                    # now plot stuff:
                    # clear axis first:
                    self.ax_list[f].cla()
                    # redraw titles and labels:
                    xlabel = self.figure_plotting_info[f][0]
                    ylabel = self.figure_plotting_info[f][1]
                    title  = self.figure_plotting_info[f][1] + ' vs ' + self.figure_plotting_info[f][0]
                    self.ax_list[f].set_xlabel(xlabel)
                    self.ax_list[f].set_ylabel(ylabel)
                    self.ax_list[f].set_title(title)

                    # before drawing, check if both x_data and y_data are 1D and of the same size
                    if (y_data.ndim == 1) and (x_data.ndim == 1) and (len(x_data) == len(y_data)):
                        self.ax_list[f].scatter(x_data[0:len(x_data)-1], y_data[0:len(y_data)-1], marker='x')
                        self.ax_list[f].scatter(x_data[-1], y_data[-1], marker = 'o', color='black')
                    else:
                        # do something else
                        print('incompatible data!')
                    self.canvas_live_analysis.draw_idle()

                elif self.figure_plotting_info[f] and len(self.figure_plotting_info[f]) == 1: 
                    # two cases: plotting [image] or plot [density (z) vs z from box exp shots]
                    q = self.figure_plotting_info[f][0] # this is a one-element list, so there's nothing in self.figure_plotting_info[1] doesn't exist
                    if q == 'Densities(z) Box Exp (PR)':
                        data = self.current_measurement.get_analysis_value_from_runs(q)
                        print(data.shape)
                        # clear axis first:
                        self.ax_list[f].cla()
                        xlabel = 'Z'
                        ylabel = 'Density along z'
                        title = self.figure_plotting_info[f][0]
                        self.ax_list[f].set_xlabel(xlabel)
                        self.ax_list[f].set_ylabel(ylabel)
                        self.ax_list[f].set_title(title)

                    else:
                        img = self.current_measurement.get_analysis_value_from_runs(q)
                        print(img.shape)

                        # clear axis first:
                        self.ax_list[f].cla()
                        # redraw titles and labels:
                        xlabel = 'X'
                        ylabel = 'Y'
                        title  = self.figure_plotting_info[f][0]
                        self.ax_list[f].set_xlabel(xlabel)
                        self.ax_list[f].set_ylabel(ylabel)
                        self.ax_list[f].set_title(title)

                        # plot the last image in img[]:
                        self.ax_list[f].imshow(img[-1])
                        #### code for setting up scrolling through shots
                        self.tracker_list[f] = IndexTracker(self.ax_list[f], img, title)
                        self.fig_live_analysis.canvas.mpl_connect('scroll_event', self.tracker_list[f].on_scroll)

                    # re-draw canvas
                    self.canvas_live_analysis.draw_idle()                        

            self.refresh_live_analysis()
            loop_counter += 1
            time.sleep(0.5)

    def top_double(self):
        if self.top_double_bttn.config('relief')[-1] == 'sunken':
            self.top_double_bttn.config(relief="raised")
            self.top_double_bttn.config(fg='black')
            self.enable_image_type_buttons()
        else:
            self.top_double_bttn.config(relief="sunken")  
            self.top_double_bttn.config(fg='red')
            self.image_type = 'top_double'
            # enable buttons:
            self.side_lm_bttn["state"] = DISABLED
            self.side_hm_bttn["state"] = DISABLED

    def side_low_mag(self):
        if self.side_lm_bttn.config('relief')[-1] == 'sunken':
            self.side_lm_bttn.config(relief="raised")
            self.side_lm_bttn.config(fg='black')
            self.enable_image_type_buttons()
        else:
            self.side_lm_bttn.config(relief="sunken")  
            self.side_lm_bttn.config(fg='red')
            self.image_type = 'side_low_mag'
            # enable buttons:
            self.top_double_bttn["state"] = DISABLED
            self.side_hm_bttn["state"] = DISABLED

    def side_high_mag(self):
        if self.side_hm_bttn.config('relief')[-1] == 'sunken':
            self.side_hm_bttn.config(relief="raised")
            self.side_hm_bttn.config(fg='black')
            self.enable_image_type_buttons()
        else:
            self.side_hm_bttn.config(relief="sunken")  
            self.side_hm_bttn.config(fg='red')
            self.image_type = 'side_high_mag'
            # enable buttons:
            self.top_double_bttn["state"] = DISABLED
            self.side_lm_bttn["state"] = DISABLED

    def enable_image_type_buttons(self):
        # enable buttons:
        self.top_double_bttn["state"] = NORMAL
        self.side_lm_bttn["state"] = NORMAL
        self.side_hm_bttn["state"] = NORMAL
        self.analyze_live_bttn["state"] = DISABLED

    def confirm_roi_and_norm_box(self):
        
        if self.folder_path_live_analysis and self.current_file_fullpath_live_analysis:
            # display roi and norm box on image
            # ...

            # then set ROI and Norm Box to be passed to analyze_live method:
            self.roi_X_min = self.X_min_live_analysis
            self.roi_X_max = self.X_max_live_analysis
            self.roi_Y_min = self.Y_min_live_analysis
            self.roi_Y_max = self.Y_max_live_analysis

            self.roi_rect = None
            self.norm_box_rect = None

            self.roi_rect = mpatches.Rectangle((self.roi_X_min, self.roi_Y_min), 
                                        width  = abs(self.roi_X_max - self.roi_X_min), 
                                        height = abs(self.roi_Y_max - self.roi_Y_min),
                                        alpha  = 0.1,
                                        facecolor = 'red')

            self.norm_box_X_min = self.norm_box_X_min_live_analysis
            self.norm_box_X_max = self.norm_box_X_max_live_analysis
            self.norm_box_Y_min = self.norm_box_Y_min_live_analysis
            self.norm_box_Y_max = self.norm_box_Y_max_live_analysis

            self.norm_box_rect = mpatches.Rectangle((self.norm_box_X_min, self.norm_box_Y_min), 
                                        width  = abs(self.norm_box_X_max - self.norm_box_X_min), 
                                        height = abs(self.norm_box_Y_max - self.norm_box_Y_min),
                                        alpha  = 0.1,
                                        facecolor = 'green')

            # draw these on image viewer:
            self.ax_image_viewer_live_analysis.add_patch(self.roi_rect)
            self.ax_image_viewer_live_analysis.add_patch(self.norm_box_rect)
            self.canvas_image_viewer_live_analysis.draw_idle()

            # only now enable analyze live button
            self.analyze_live_bttn["state"] = NORMAL

    def reset_fields_analysis_live_button(self):
        if self.current_file_fullpath_live_analysis:
            # reset image type buttons:
            self.top_double_bttn.config(relief="raised")
            self.top_double_bttn.config(fg='black')
            self.side_lm_bttn.config(relief="raised")
            self.side_lm_bttn.config(fg='black')
            self.side_hm_bttn.config(relief="raised")
            self.side_hm_bttn.config(fg='black')
            self.enable_image_type_buttons()

            # reset plotting variables:
            self.figure_plotting_info = [None]*len(LIVE_FIGURES)

            # clear entry next to figure option:
            self.plotting_variables_entry_live_analysis.delete(0,'end')   
            self.plotting_variables_entry_live_analysis.insert(0, '')

            # clear "vs variable entry":
            self.vs_variable_entry_live_analysis.delete(0,'end')   
            self.vs_variable_entry_live_analysis.insert(0, "") 

            # disable analyze_live button:
            self.analyze_live_bttn["state"] = DISABLED

            # re-show image in image viewer to clear any ROIs:
            self.display_image_live_analysis()

            # clear figures too:
            for ax in self.ax_list:
                ax.cla()
            self.canvas_live_analysis.draw_idle()

    def stop_analyze_live_button(self):
        # reset measurement object
        self.current_measurement = None 
        # reset all fields without clearing the figures
        self.top_double_bttn.config(relief="raised")
        self.top_double_bttn.config(fg='black')
        self.side_lm_bttn.config(relief="raised")
        self.side_lm_bttn.config(fg='black')
        self.side_hm_bttn.config(relief="raised")
        self.side_hm_bttn.config(fg='black')
        self.enable_image_type_buttons()
        # reset plotting variables:
        self.figure_plotting_info = [None]*len(LIVE_FIGURES)
        # clear entry next to figure option:
        self.plotting_variables_entry_live_analysis.delete(0,'end')   
        self.plotting_variables_entry_live_analysis.insert(0, '')
        # clear "vs variable entry":
        self.vs_variable_entry_live_analysis.delete(0,'end')   
        self.vs_variable_entry_live_analysis.insert(0, "") 
        # disable analyze_live button:
        self.analyze_live_bttn["state"] = DISABLED
        # re-show image in image viewer to clear any ROIs:
        self.display_image_live_analysis()  

        # reset analysis button to its original state   
        self.analyze_live_bttn.config(text='START ANALYSIS')
        self.analyze_live_bttn.config(relief="raised") # this halts the analysis
        self.analyze_live_bttn.config(fg='green')
        self.analyze_live_bttn["state"] = DISABLED

        # halt measurement and re-enable buttons:
        self.top_double_bttn["state"] = NORMAL
        self.side_lm_bttn["state"] = NORMAL
        self.side_hm_bttn["state"] = NORMAL
        self.confirm_roi_and_norm_box_bttn["state"] = NORMAL
        self.vs_variable_ok_bttn_live_analysis["state"] = NORMAL
        self.plotting_quantity_live_analysis_menu["state"] = NORMAL
        self.vs_quantity_live_analysis_menu["state"] = NORMAL
        self.vs_variable_entry_live_analysis["state"] = NORMAL
        self.plot_density_live_analysis_menu["state"] = NORMAL
        self.reset_fields_analysis_live_bttn["state"] = NORMAL
        self.stop_analyze_live_bttn["state"] = NORMAL
        self.stop_analyze_live_bttn.config(fg='black')

        # reset browse, refresh, and del buttons:
        self.browse_bttn_live_analysis["state"] = NORMAL
        self.refresh_bttn_live_analysis["state"] = NORMAL
        self.delete_bttn_live_analysis["state"] = NORMAL

        # dump analysis:
        # create file name for analysis:
        

    
        # add code here for saving analysis


    def choose_figure_for_data_fit(self, event):
        print(self.data_fit_figure.get())

    def choose_imaging_resonance_type(self, event):
        print(self.imaging_resonance_fit_type.get())

    def imaging_resonance_fit_do_it_button(self):
        return 0

    def choose_plot_density(self, event):
        self.current_density_to_plot = self.plot_density_live_analysis.get() 

        fig = self.current_figure_live_analysis # should be of the form 'Figure X'
        index = int(fig.split(' ')[-1]) - 1

        self.figure_plotting_info[index] = [self.current_density_to_plot] 
        print(self.figure_plotting_info)
        # update plotting variables status box:
        self.plotting_variables_entry_live_analysis.delete(0,'end')   
        self.plotting_variables_entry_live_analysis.insert(0, 'Fig ' + str(index+1) + ': ' +  self.current_density_to_plot) 

        # next update titles and axis labels
        for ax in self.ax_list:
            idx = self.ax_list.index(ax)
            if self.figure_plotting_info[idx]:
                if len(self.figure_plotting_info[idx]) == 2: # if have x vs. y situation
                    xlabel = self.figure_plotting_info[idx][0]
                    ylabel = self.figure_plotting_info[idx][1]
                    title  = ylabel + ' vs ' + xlabel
                    ax.set_xlabel(xlabel)
                    ax.set_ylabel(ylabel)
                    ax.set_title(title)
                elif len(self.figure_plotting_info[idx]) == 1: # if plotting image:
                    title  = self.figure_plotting_info[idx][0]
                    ax.set_xlabel('X')
                    ax.set_ylabel('Y')
                    ax.set_title(title)
                else:
                    print('incompatible data!!!')
                self.canvas_live_analysis.draw_idle()

    #######################################################################
    ##### THIRD TAB FUNCTIONS: GUPPY CAMS #################################
    #######################################################################

    def selectItem_guppy(self):
        return 0

    def browse_guppy(self):
        self.folder_path_guppy = filedialog.askdirectory()
        self.refresh_guppy()

        if self.folder_path_guppy:
            if self.scan_bttn_guppy.config('relief')[-1] == 'sunken':
                t = Thread (target = self.scan_act_guppy)
                t.start()

    def refresh_guppy(self):
        return 0

    def scan_guppy(self):
        return 0

    def scan_act_guppy(self):
        return 0

    def show_new_guppy(self):
        return 0

    def delete_guppy(self):
        return 0

    def OD_select_guppy(self):
        return 0

    def with_atoms_select_guppy(self):
        return 0

    def without_atoms_select_guppy(self):
        return 0

    def dark_select_guppy(self):
        return 0

    def FakeOD_select_guppy(self):
        return 0

    def light_OK_guppy(self):
        return 0

    def reset_view_button_guppy(self):
        return 0

    def ROI_poly_button_guppy(self):
        return 0

    def clear_ROI_poly_button_guppy(self):
        return 0

    def load_ROI_poly_button_guppy(self):
        return 0

    def save_ROI_poly_button_guppy(self):
        return 0

    def refresh_camera_button_guppy(self):
        self.cam_names = []
        self.cam_list = []
        self.cam_ids = []
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras()
            self.cam_list = cams
            print('Cameras found: {}'.format(len(cams)))
            for cam in cams:
                print_camera(cam)
                self.cam_ids.append(cam.get_id())
                if cam.get_id() == 'DEV_000F31F42DE1':
                    self.cam_names.append('CAM 1')
                elif cam.get_id() == 'DEV_0xA4701120A9E93':
                    self.cam_names.append('Top Green')
                elif cam.get_id() == 'DEV_0xA4701120B0AE4':
                    self.cam_names.append('Side Green')
                elif cam.get_id() == 'DEV_0xA4701120B0AE8':
                    self.cam_names.append('MOT')
                else:
                    self.cam_names.append('UNKNOWN CAM')

        # now populate the camera table:
        if self.cam_names: # only act if file_names has changed
            # first clear table:
            self.camera_table_guppy.delete(*self.camera_table_guppy.get_children())
            # then repopulate:
            for i in range(len(self.cam_names)):              
                # then repopulate
                self.camera_table_guppy.insert("","end",text = self.cam_names[i], values = self.cam_ids[i])

    def selectCamera_guppy(self, event):
        curItem = self.camera_table_guppy.focus()
        curItem = self.camera_table_guppy.item(curItem)
        self.selected_cam_id = curItem['values'][0]
        
    def select_camera_button_guppy(self):
        # update selected image textbox:
        self.selected_camera_entry_guppy.delete(0,'end')
        self.selected_camera_entry_guppy.insert(0,self.selected_cam_id)
        cam_index = self.cam_ids.index(self.selected_cam_id)
        self.selected_cam = self.cam_list[cam_index]
        print_camera(self.selected_cam)

        with Vimba.get_instance() as vimba:
            try:
                self.cam = vimba.get_camera_by_id(self.selected_cam_id)
                # print features now
                print('Print all features of camera \'{}\':'.format(self.cam.get_id()))
                with self.cam:
                    for feature in self.cam.get_all_features():
                        print_feature(feature)
                    exposure_time = self.cam.ExposureTime
                    exposure_time.set(1500)
                    print('Exposure Time: ' + str(exposure_time.get()))

            except VimbaCameraError:
                abort('Failed to access Camera \'{}\'. Abort.'.format(self.selected_cam_id))


    def preview_button_guppy(self):      
        if self.preview_bttn_guppy.config('relief')[-1] == 'sunken':
            self.preview_bttn_guppy.config(text='Preview')
            self.preview_bttn_guppy.config(relief="raised")
            self.preview_bttn_guppy.config(fg='black') 
            # if is streaming then stop:
            self.is_streaming = False
            if self.after_id:
                self.lblVideo.after_cancel(self.after_id) # cancel the showing task
                self.after_id = None
            
        else:
            self.preview_bttn_guppy.config(relief="sunken")  
            self.preview_bttn_guppy.config(text='STOP')
            self.preview_bttn_guppy.config(fg='red')
            # if raised then sunken and start scan:
            self.show_streaming()
            threading.Thread(target=self.camera_streaming, args=(self.queue,), daemon=True).start()
    
    def show_streaming(self):
        if not self.queue.empty():
            image = self.queue.get()
            self.lblVideo.config(image=image)
            self.lblVideo.image = image
        self.after_id = self.lblVideo.after(20, self.show_streaming)

    def camera_streaming(self, queue):
        self.is_streaming = True
        print("streaming started")
        with Vimba.get_instance() as vimba:
            with self.cam:
                while self.is_streaming:
                    frame = self.cam.get_frame()
                    frame = frame.as_opencv_image()
                    im = Image.fromarray(frame[:,:,0].astype(np.uint8))
                    img = ImageTk.PhotoImage(im)
                    self.queue.put(img) # put the capture image into queue
        print("streaming stopped")

    def acquire_once_button_guppy(self):
        if self.cam:
            with Vimba.get_instance() as vimba:
                with self.cam:
                    frame = self.cam.get_frame()
                    frame.convert_pixel_format(PixelFormat.Mono8)
                    frame_name = self.folder_path_guppy + '/frame.jpg' 
                    cv2.imwrite(frame_name, frame.as_opencv_image())

                    print(type(frame))

    def acquire_cont_button_guppy(self):
        return 0

    def abort_button_guppy(self):
        return 0

    def exposure_ok_button(self):
        if self.selected_cam_id:
            print(int(self.exposure_entry_guppy.get()))

            with Vimba.get_instance() as vimba:
                try:
                    self.cam = vimba.get_camera_by_id(self.selected_cam_id)
                    with self.cam:
                        exposure_time = self.cam.ExposureTime
                        exposure_time.set(int(self.exposure_entry_guppy.get()))
                        print('Exposure Time: ' + str(exposure_time.get()))

                except VimbaCameraError:
                    print('Camera error')

#######################################################################
##### HELPER FUNCTIONS and CLASSES ####################################
#######################################################################           

def toggle_selector(event):
            print (' Key pressed.')
            if event.key in ['Q', 'q'] and toggle_selector.RS.active:
                print (' RectangleSelector deactivated.')
                toggle_selector.RS.set_active(False)
            if event.key in ['A', 'a'] and not toggle_selector.RS.active:
                print (' RectangleSelector activated.')
                toggle_selector.RS.set_active(True)

'''
Credit: Eric A. Wolf, BEC1@MIT, 2022. 

Convenience function for safely subtracting two arrays of unsigned type.
Minimum cast: A numpy dtype which represents the ‘minimal datatype’ to which the
minuend and subtrahend must be cast. For unsigned type, np.byte is the default,
enforcing a signed type without data loss.
Please note: if the differences returned by safe_subtract are later manipulated,
it may be necessary to use a ‘larger’ minimum cast for safety. np.byte only guarantees
that no overflows are obtained when two unsigned integers are subtracted.
'''
def safe_subtract(x, y, minimum_cast = np.byte):
    newtype = np.result_type(x, y, minimum_cast)
    return x.astype(newtype) - y.astype(newtype)

#### code for free hand tool... taken from github.com/jdoepfert/roipoly.py/blob/master/roipoly/roipoly.py
#### why not install package? Because code is cursed... some methods don't work properly

class RoiPoly:
    def __init__(self, fig=None, ax=None, color='b',
                 roicolor=None, show_fig=True, close_fig=True):
        """
        Parameters
        ----------
        fig: matplotlib figure
            Figure on which to create the ROI
        ax: matplotlib axes
            Axes on which to draw the ROI
        color: str
           Color of the ROI
        roicolor: str
            deprecated, use `color` instead
        show_fig: bool
            Display the figure upon initializing a RoiPoly object
        close_fig: bool
            Close the figure after finishing ROI drawing
        """

        if roicolor is not None:
            color = roicolor

        if fig is None:
            fig = plt.gcf()
        if ax is None:
            ax = plt.gca()

        self.start_point = []
        self.end_point = []
        self.previous_point = []
        self.x = []
        self.y = []
        self.line = None
        self.completed = False  # Has ROI drawing completed?
        self.color = color
        self.fig = fig
        self.ax = ax
        self.close_figure = close_fig

        # Mouse event callbacks
        self.__cid1 = self.fig.canvas.mpl_connect(
            'motion_notify_event', self.__motion_notify_callback)
        self.__cid2 = self.fig.canvas.mpl_connect(
            'button_press_event', self.__button_press_callback)

        if show_fig:
            self.show_figure()

    @staticmethod
    def show_figure():
        if sys.flags.interactive:
            plt.show(block=False)
        else:
            plt.show(block=True)

    def __motion_notify_callback(self, event):
        if event.inaxes == self.ax:
            x, y = event.xdata, event.ydata
            if ((event.button is None or event.button == 1) and
                    self.line is not None):
                # Move line around
                x_data = [self.previous_point[0], x]
                y_data = [self.previous_point[1], y]
                logger.debug("draw line x: {} y: {}".format(x_data, y_data))
                self.line.set_data(x_data, y_data)
                self.fig.canvas.draw()

    def __button_press_callback(self, event):
        if event.inaxes == self.ax:
            x, y = event.xdata, event.ydata
            ax = event.inaxes
            if event.button == 1 and not event.dblclick:
                logger.debug("Received single left mouse button click")
                if self.line is None:  # If there is no line, create a line
                    self.line = plt.Line2D([x, x], [y, y],
                                           marker='.', color=self.color)
                    self.start_point = [x, y]
                    self.previous_point = self.start_point
                    self.x = [x]
                    self.y = [y]

                    ax.add_line(self.line)
                    self.fig.canvas.draw()
                    # Add a segment
                else:
                    # If there is a line, create a segment
                    x_data = [self.previous_point[0], x]
                    y_data = [self.previous_point[1], y]
                    logger.debug(
                        "draw line x: {} y: {}".format(x_data, y_data))
                    self.line = plt.Line2D(x_data, y_data,
                                           marker='.', color=self.color)
                    self.previous_point = [x, y]
                    self.x.append(x)
                    self.y.append(y)

                    event.inaxes.add_line(self.line)
                    self.fig.canvas.draw()

            elif (((event.button == 1 and event.dblclick) or
                   (event.button == 3 and not event.dblclick)) and
                  self.line is not None):
                # Close the loop and disconnect
                logger.debug("Received single right mouse button click or "
                             "double left click")
                self.fig.canvas.mpl_disconnect(self.__cid1)
                self.fig.canvas.mpl_disconnect(self.__cid2)

                self.line.set_data([self.previous_point[0],
                                    self.start_point[0]],
                                   [self.previous_point[1],
                                    self.start_point[1]])
                ax.add_line(self.line)
                self.fig.canvas.draw()
                self.line = None
                self.completed = True

                if not sys.flags.interactive and self.close_figure:
                    #  Figure has to be closed so that code can continue
                    plt.close(self.fig)

class IndexTracker:
    def __init__(self, ax, data, title):
        self.index = 0
        self.data = data
        self.ax = ax
        self.im = ax.imshow(self.data[self.index, :, :])
        self.title = title
        self.update()

    def on_scroll(self, event):
        # print(event.button, event.step)
        increment = 1 if event.button == 'up' else -1
        max_index = self.data.shape[0] - 1
        self.index = np.clip(self.index + increment, 0, max_index)
        self.update()

    def update(self):
        self.im.set_data(self.data[self.index,:, :])
        # self.ax.set_title(
        #     f'Use scroll wheel to navigate\nindex {self.index}')
        max_index = self.data.shape[0] 
        self.ax.set_title(self.title + ' ' + str(self.index+1) + '/' + str(max_index))
        self.im.axes.figure.canvas.draw_idle()

#####################################################################
#####################################################################
#####################################################################
#####################################################################
#####################################################################



#####################################################################
#####################################################################
######## GUPPY CAM METHODS ################################
#####################################################################
#####################################################################

def print_camera(cam):
    print('/// Camera Name   : {}'.format(cam.get_name()))
    print('/// Model Name    : {}'.format(cam.get_model()))
    print('/// Camera ID     : {}'.format(cam.get_id()))
    print('/// Serial Number : {}'.format(cam.get_serial()))
    print('/// Interface ID  : {}\n'.format(cam.get_interface_id()))


def print_feature(feature):
    try:
        value = feature.get()
    except (AttributeError, VimbaFeatureError):
        value = None

    print('/// Feature name   : {}'.format(feature.get_name()))
    print('/// Display name   : {}'.format(feature.get_display_name()))
    print('/// Tooltip        : {}'.format(feature.get_tooltip()))
    print('/// Description    : {}'.format(feature.get_description()))
    print('/// SFNC Namespace : {}'.format(feature.get_sfnc_namespace()))
    print('/// Unit           : {}'.format(feature.get_unit()))
    print('/// Value          : {}\n'.format(str(value)))

def frame_handler(cam, frame):
    if frame.get_status() == FrameStatus.Complete:
        print('Frame(ID: {}) has been received.'.format(frame.get_id()), flush=True)

    cam.queue_frame(frame)

#####################################################################
#####################################################################
#####################################################################
#####################################################################
#####################################################################
#####################################################################


def main():
    ## for image browser
    root = Tk()
    root.title('BEC1 Image Browser')
    root.geometry("1920x1080")
    BEC1_exp_portal = BEC1_Portal(root)
    root.mainloop()

    return 

if __name__ == "__main__":
	main()