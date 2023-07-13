import sys 
import os

import numpy as np 
from vimba import Vimba

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

from satyendra.code import plotting_utilities, loading_functions
from satyendra.code.instruments.cameras import guppy_camera


def main():
    print("Initializing")
    camera_id, *cam_setup_params = parse_clas()
    fig, ax = plotting_utilities.initialize_live_plot()
    with guppy_camera.GuppyCamera(camera_id) as cam:
        setup_camera(cam, *cam_setup_params)
        print("Done. Use Ctrl+C to exit.")
        try:
            cam.start_video()
            while True:
                current_frame = cam.get_video_frame()
                if not current_frame is None:
                    plotting_utilities.update_live_plot_imshow(current_frame, ax = ax, vmin = 0, vmax = 255, cmap="gray")
        finally:
            cam.stop_video()


def parse_clas():
    command_line_args = sys.argv[1:]
    if len(command_line_args) == 0 or command_line_args[0] == "help":
        _help_function() 
        exit(0)
    camera_name = command_line_args[0]
    GUPPY_CONFIG_FILENAME = "guppy_camera_name_config_local.json"
    camera_config_dict_dict = loading_functions.load_config_json(GUPPY_CONFIG_FILENAME) 
    camera_config_dict = camera_config_dict_dict[camera_name] 
    camera_id = camera_config_dict["camera_id"]
    if len(command_line_args) > 1:
        exposure_time_us = float(command_line_args[1])
    else:
        exposure_time_us = camera_config_dict["default_exposure"]
    if len(command_line_args) > 2:
        exposure_auto = (command_line_args[2] == "True")
    else:
        exposure_auto = camera_config_dict["default_auto_exposure"]
    if len(command_line_args) > 3:
        image_height = int(command_line_args[3]) 
    else:
        image_height = camera_config_dict["default_image_height"] 
    if len(command_line_args) > 4:
        image_width = int(command_line_args[4])
    else:
        image_width = camera_config_dict["default_image_width"]
    return (camera_id, exposure_time_us, exposure_auto, image_height, image_width) 



def setup_camera(cam, exposure_time_us, exposure_auto, image_height, image_width):
    cam.set_auto_exposure(exposure_auto)
    cam.set_exposure_time(exposure_time_us) 
    cam.set_image_height(image_height) 
    cam.set_image_width(image_width)
    cam.set_property("TriggerMode", "Off")





def _help_function():
    print("Program name: Guppy Live Viewer Script") 
    print("Description: Convenience script for live viewing of the feed from a single guppy camera.") 
    print("CLAs:")
    print("Note: If CLAs are specified, they must be done in order. Optional values are initialized from the configuration JSON if not specified.")
    print("1: Camera name. Options are those specified in guppy_camera_config_local.json.")
    print("2: (optional) Exposure_time_us. The exposure time, in us.")
    print("3: (optional) Exposure_auto. If 'True', the camera will be set to auto exposure. Any other input gives fixed exposure.")
    print("4: (optional) Height. The image height, in pixels.")
    print("5: (optional) Width. The image width, in pixels.")


if __name__ == "__main__":
    main()