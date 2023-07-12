import datetime
import sys 
import os

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

from satyendra.code import loading_functions
from satyendra.code.instruments.cameras import rolling_camera_functions

DATETIME_FORMAT_STRING = "%Y-%m-%d--%H-%M-%S"
FILENAME_DELIMITER_CHAR = "_"

def main():
    acquisition_settings = parse_clas()
    with initialize_camera(acquisition_settings) as cam:
        savefolder_pathname = acquisition_settings["savefolder_path"]
        exposure_groupings_dict = acquisition_settings["exposure_groupings"]
        exposure_groupings_indices_list = [] 
        for key in exposure_groupings_dict: 
            exposure_groupings_indices_list.append(key) 
        exposure_grouping_names_list = list(exposure_groupings_dict)
        while True:
            frames = rolling_camera_functions.acquire_rolling_frame_sequence(cam, acquisition_settings["frames_per_sequence"],
                                                                            acquisition_settings["frame_sequence_timeout_secs"])
            acquisition_datetime = datetime.datetime.now()
            acquisition_datetime_string = acquisition_datetime.strftime(DATETIME_FORMAT_STRING)
            regrouped_exposures_list = rolling_camera_functions.regroup_numpy_frames(frames, exposure_groupings_indices_list)
            for regrouped_exposures, exposure_grouping_name in zip(regrouped_exposures_list, exposure_grouping_names_list):
                filename_sans_extension = FILENAME_DELIMITER_CHAR.join((acquisition_datetime_string, exposure_grouping_name))
                filename = filename_sans_extension + acquisition_settings["save_extension"]
                file_path = os.path.join(acquisition_settings["savefolder_path"], filename)
                rolling_camera_functions.save_frames(regrouped_exposures, file_path)
            print("Saved at: {0}".format(acquisition_datetime_string))
                

help_aliases = ["help", "Help", "HELP", "h"]

def parse_clas():
    command_line_args = sys.argv[1:]
    if len(command_line_args) == 0 or command_line_args[0] in help_aliases:
        help_function()
        exit(0) 
    acquisition_type_name = command_line_args[1] 
    IMAGE_ACQUISITION_CONFIG_FILENAME = "image_acquisition_config_local.json"
    acquisition_settings_dict = loading_functions.load_config_json(IMAGE_ACQUISITION_CONFIG_FILENAME)
    acquisition_settings = acquisition_settings_dict[acquisition_type_name]
    return acquisition_settings


def initialize_camera(acquisition_settings):
    camera_id = acquisition_settings["camera_id"]
    if acquisition_settings["camera_type"] == "guppy":
        from satyendra.code.instruments.cameras import guppy_cam_wrapper 
        cam = guppy_cam_wrapper.GuppyCamWrapper(camera_id)
    else:
        raise ValueError("Unsupported camera type")
    camera_acquisition_parameters = acquisition_settings["acquisition_parameters"]
    for key in camera_acquisition_parameters:
        cam.set_property(key, camera_acquisition_parameters[key])
    cam.start_video()
    return cam

def help_function() 
    print("Image Acquisition Script")
    print("A script for acquiring images from a free-running camera, e.g. Andor or guppy.")
    print("CLAS:")
    print("1: Acquisitions_Name (str): A name, as specified in image_acquisition_config_local, encoding the acquisition type.")


if __name__ == "__main__":
    main()