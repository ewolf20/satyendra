import importlib.resources as pkg_resources
import json 
import os 
import sys 
import time 

import pylablib as pll 

from .. import configs as c 
with pkg_resources.path(c, "camera_dll_information.json") as camera_dll_path:
    with open(camera_dll_path) as camera_dll_file:
        camera_dll_dict = json.load(camera_dll_file)
        camera_dll_path_sdk2 = camera_dll_dict["camera_dll_path_sdk2"]
        camera_dll_path_sdk3 = camera_dll_dict["camera_dll_path_sdk3"]
pll.par["devices/dlls/andor_sdk2"] = camera_dll_path_sdk2 
pll.par["devices/dlls/andor_sdk3"] = camera_dll_path_sdk3


LIST_OF_SDK_3_CAMERAS = ['neo']



class AndorCameraFrameGrabber():

    def __init__(self, camera_type, imaging_mode):
        self.camera_type = camera_type 
        self.is_sdk3 = self.camera_type in LIST_OF_SDK_3_CAMERAS
        self.imaging_mode = imaging_mode
        self._load_camera() 
        self._initialize_camera() 


    def __enter__(self):
        return self 
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.camera.close()


    def _load_camera(self):
        from .. import configs as c 
        with pkg_resources.path(c, "camera_dll_information.json") as camera_dll_path:
            with open(camera_dll_path) as camera_dll_file:
                camera_dll_dict = json.load(camera_dll_file)
                camera_dll_path_sdk2 = camera_dll_dict["camera_dll_path_sdk2"]
                camera_dll_path_sdk3 = camera_dll_dict["camera_dll_path_sdk3"]
        pll.par["devices/dlls/andor_sdk2"] = camera_dll_path_sdk2 
        pll.par["devices/dlls/andor_sdk3"] = camera_dll_path_sdk3
        from pylablib.devices import Andor
        if(self.camera_type == "neo"):
            self.camera = Andor.AndorSDK3Camera()
        elif(self.camera_type == "ixon"):
            self.camera = Andor.AndorSDK2Camera() 
        else:
            raise RuntimeError("The specified camera type is not supported.") 


    def _initialize_camera(self):
        from .. import configs as c 
        with pkg_resources.path(c, "camera_config_information.json") as camera_config_path:
            with open(camera_config_path) as camera_config_file:
                camera_config_dict = json.load(camera_config_file)
                imaging_mode_config_dict = camera_config_dict[self.imaging_mode]
                if self.is_sdk3:
                    for attribute_name in imaging_mode_config_dict:
                        self.camera.set_attribute_value(attribute_name, imaging_mode_config_dict[attribute_name]) 
                else:
                    self._initialize_sdk2_camera_helper(imaging_mode_config_dict)


    """Captures the images associated with a single run of the experiment.
    
    Attempts to capture and save a full set of images for an experiment run. Supports 
    detection of missed triggers, though not 'bad shots', and resynchronization of the experimental sequence."""
    
    def capture_run_images(self):
        pass

    """
    Helper function for initializing SDK2 cameras, which don't have a unified 
    attribute setting format."""
    def _initialize_sdk2_camera_helper(imaging_mode_config_dict):
        pass
    

