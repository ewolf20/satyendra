import importlib.resources as pkg_resources
import json 
import os 
import sys 
import time 

import pylablib as pll 

LIST_OF_SDK_3_CAMERAS = ['neo']
LIST_OF_SDK_2_CAMERAS = ['ixon']

class AndorCameraWrapper():

    def __init__(self, camera_type, imaging_mode):
        self.camera_type = camera_type 
        if not (self.camera_type in LIST_OF_SDK_3_CAMERAS or self.camera_type in LIST_OF_SDK_2_CAMERAS):
            raise RuntimeError("The specified camera type " + self.camera_type + " is not supported.")
        self.is_sdk3 = self.camera_type in LIST_OF_SDK_3_CAMERAS
        self.imaging_mode = imaging_mode
        self._load_camera() 
        self._initialize_camera() 


    def __enter__(self):
        self.camera.setup_acquisition(mode = "sequence")
        return self 
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.camera.clear_acquisition()
        self.camera.close()


    def _load_camera(self):
        from pylablib.devices import Andor
        if(self.camera_type == "neo"):
            self.camera = Andor.AndorSDK3Camera()
        elif(self.camera_type == "ixon"):
            self.camera = Andor.AndorSDK2Camera() 
        else:
            raise RuntimeError("The specified camera type is not supported.") 
        while not self.camera.is_opened():
            pass


    def _initialize_camera(self):
        from .. import configs as c 
        with pkg_resources.path(c, "camera_config_information.json") as camera_config_path:
            with open(camera_config_path) as camera_config_file:
                camera_config_dict = json.load(camera_config_file)
                imaging_mode_config_dict = camera_config_dict[self.imaging_mode]
                if self.is_sdk3:
                    self._initialize_sdk3_camera_helper(imaging_mode_config_dict)
                else:
                    self._initialize_sdk2_camera_helper(imaging_mode_config_dict)


    def _initialize_sdk2_camera_helper(self, imaging_mode_config_dict):
        pass


    def _initialize_sdk3_camera_helper(self, image_mode_config_dict):
        pass

    

