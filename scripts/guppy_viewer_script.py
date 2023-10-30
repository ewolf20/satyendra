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
    camera_id, camera_config_dict, camera_parameter_override_dict = parse_clas()
    camera_bit_depth = camera_config_dict["bit_depth"]
    pixel_max = 2**camera_bit_depth - 1
    camera_parameter_dict = camera_config_dict["acquisition_parameters"]
    fig, ax = plotting_utilities.initialize_live_plot()
    with guppy_camera.GuppyCamera(camera_id) as cam:
        setup_camera(cam, camera_parameter_dict, camera_parameter_override_dict)
        print("Done. Use Ctrl+C to exit.")
        try:
            cam.start_video()
            while True:
                current_frame = cam.get_video_frame(recency = "newest")
                if not current_frame is None:
                    print("Got frame")
                    plotting_utilities.update_live_plot_imshow(current_frame, ax = ax, vmin = 0, vmax = pixel_max, cmap="gray")
        finally:
            cam.stop_video()


def parse_clas():
    command_line_args = sys.argv[1:]
    if len(command_line_args) == 0 or command_line_args[0] == "help":
        _help_function() 
        exit(0)
    camera_name = command_line_args[0]
    GUPPY_CONFIG_FILENAME = "guppy_viewer_script_config_local.json"
    camera_config_dict_dict = loading_functions.load_config_json(GUPPY_CONFIG_FILENAME) 
    camera_config_dict = camera_config_dict_dict[camera_name]
    camera_id = camera_config_dict["camera_id"]
    camera_parameter_override_dict = {}
    if len(command_line_args) > 1:
        camera_parameter_override_dict["ExposureTime"] = float(command_line_args[1])
    if len(command_line_args) > 2:
        if command_line_args[2] == "True":
            camera_parameter_override_dict["ExposureAuto"] = "On"
        else:
            camera_parameter_override_dict["ExposureAuto"] = "Off"
    if len(command_line_args) > 3:
        camera_parameter_override_dict["Height"] = int(command_line_args[3])
    if len(command_line_args) > 4:
        camera_parameter_override_dict["Width"] = int(command_line_args[4])
    return (camera_id, camera_config_dict, camera_parameter_override_dict) 



def setup_camera(cam, camera_parameter_dict, camera_parameter_override_dict):
    for key in camera_parameter_dict:
        cam.set_property(key, camera_parameter_dict[key])
    for key in camera_parameter_override_dict:
        cam.set_property(key, camera_parameter_override_dict[key])





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