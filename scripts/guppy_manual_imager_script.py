import datetime
import sys 
import os

import numpy as np 
import matplotlib.patches as patches 
import matplotlib.pyplot as plt
from vimba import Vimba

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

from BEC1_Analysis.code import image_processing_functions, measurement

from satyendra.code import plotting_utilities, loading_functions
from satyendra.code.instruments.cameras import guppy_camera


def main():
    print("Initializing")
    camera_name, camera_id, camera_config_dict, camera_parameter_override_dict = parse_clas()
    if "ROI" in camera_config_dict:
        roi_coords = camera_config_dict["ROI"]
    else:
        roi_coords = None
    camera_bit_depth = camera_config_dict["bit_depth"]
    pixel_max = 2**camera_bit_depth - 1
    camera_parameter_dict = camera_config_dict["acquisition_parameters"]
    frames_list = []
    with guppy_camera.GuppyCamera(camera_id) as cam:
        setup_camera(cam, camera_parameter_dict, camera_parameter_override_dict)
        counter = 0
        while True:
            frame = cam.get_frame()
            print("Got frame") 
            np.save("Guppy_Frame_{0:d}.npy".format(counter), frame) 
            plt.imshow(frame, vmin = 0, vmax = pixel_max, cmap = "gray")
            plt.show() 
            counter += 1
            input("Enter for next")
            # plt.imshow(frame, vmin = 0, vmax = pixel_max, cmap = "gray")
            # plt.show()
    #     print("Setup finished.")
    #     print("Step 1: Dark Shot.")
    #     input("Please block all light and press enter when ready.") 
    #     frame_dark = cam.get_frame()
    #     display_image(frame_dark, pixel_max, roi_coords)
    #     frames_list.append(frame_dark) 
    #     print("Step 2: Light shot") 
    #     input("Please allow light through, but block atoms, and press enter when ready.")
    #     frame_light = cam.get_frame() 
    #     display_image(frame_light, pixel_max, roi_coords) 
    #     frames_list.append(frame_light) 
    #     print("Step 3: Atoms shot") 
    #     input("Please allow both light and atoms, and press enter when ready.") 
    #     frame_atoms = cam.get_frame()
    #     display_image(frame_atoms, pixel_max, roi_coords)
    #     frames_list.append(frame_atoms) 
    # frames_array = np.array(frames_list) 
    # #flip the frame array to agree with convention...
    # frames_array = np.flip(frames_array)
    # without_atoms_subtracted = image_processing_functions.safe_subtract(frames_array[1], frames_array[2]) 
    # with_atoms_subtracted = image_processing_functions.safe_subtract(frames_array[0], frames_array[2])




        

def display_image(frame, pixel_max, roi_coords):
    ax = plt.gca()
    ax.imshow(frame, vmin = 0, vmax = pixel_max, cmap = "gray")
    if not roi_coords is None:
        x_min, y_min, x_max, y_max = roi_coords 
        width = x_max - x_min 
        height = y_max - y_min 
        rect = patches.Rectangle((x_min, y_min), width, height, linewidth = 1, edgecolor = 'r', facecolor = 'none') 
        ax.add_patch(rect)
    plt.show()


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
        camera_parameter_override_dict["Height"] = int(command_line_args[2])
    if len(command_line_args) > 3:
        camera_parameter_override_dict["Width"] = int(command_line_args[3])
    return (camera_name, camera_id, camera_config_dict, camera_parameter_override_dict) 



def setup_camera(cam, camera_parameter_dict, camera_parameter_override_dict):
    for key in camera_parameter_dict:
        cam.set_property(key, camera_parameter_dict[key])
    for key in camera_parameter_override_dict:
        cam.set_property(key, camera_parameter_override_dict[key])


#Convenience method that "interprets" the images according to the camera name.
def handle_image(camera_name, frame_array, roi_coords):
    frame_timestring = datetime.datetime.now().strftime(measurement.FILENAME_DATETIME_FORMAT_STRING)
    result_string = ""
    result_string += "Imaging type: {0}\n".format(camera_name) 
    result_string += "Time taken: {0}\n".format(frame_timestring) 
    result_string += "ROI coordinates: {0}\n".format(roi_coords) 
    #For the slower, the "relevant" thing to do is count atomic flux fluorescence
    if camera_name == "Slower":
        with_atom_flux = frame_array[0] 
        without_atom_flux = frame_array[1]
        background_subtracted_fluorescence = image_processing_functions.safe_subtract(with_atom_flux, without_atom_flux) 
        if not roi_coords is None:
            x_min, y_min, x_max, y_max = roi_coords 
            background_subtracted_fluorescence_ = background_subtracted_fluorescence[y_min:y_max, x_min:x_max]
        fluorescence_sum = np.sum(background_subtracted_fluorescence.astype(float))
        result_string += "Fluorescence pixel sum: {0:.4e}\n".format(fluorescence_sum)
    elif camera_name == "MOT":
        absorption_od_image = image_processing_functions.get_absorption_od_image(frame_array, ROI = roi_coords)
        if not roi_coords is None:
            x_min, y_min, x_max, y_max = roi_coords 
            absorption_od_image = absorption_od_image[y_min:y_max, x_min:x_max] 
            od_sum = np.sum(absorption_od_image)
            result_string += "OD pixel sum: {0:.4e}\n".format(od_sum) 
    else:
        pass 
    numpy_save_name = "Guppy_Image_Data_{0}_temp.npy".format(frame_timestring)
    results_save_name = "Guppy_Image_Results_{0}_temp.txt".format(frame_timestring) 
    np.save(numpy_save_name, frame_array) 
    with open(results_save_name, 'w') as f:
        f.write(result_string) 


        








def _help_function():
    print("Program name: Guppy Live Viewer Script") 
    print("Description: Convenience script for live viewing of the feed from a single guppy camera.") 
    print("CLAs:")
    print("Note: If CLAs are specified, they must be done in order. Optional values are initialized from the configuration JSON if not specified.")
    print("1: Camera name. Options are those specified in guppy_camera_config_local.json.")
    print("2: (optional) Exposure_time_us. The exposure time, in us.")
    print("3: (optional) Height. The image height, in pixels.")
    print("4: (optional) Width. The image width, in pixels.")


if __name__ == "__main__":
    main()