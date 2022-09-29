import datetime
import importlib.resources as pkg_resources
import json
import shutil
import sys 
import os 
import warnings

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

from satyendra.code.image_watchdog import ImageWatchdog

IMAGE_EXTENSION = ".fits"

def main():
    print("Welcome to the image saving script!\n")
    print("Images will be labelled with run_ids and saved in today's folder under a user-chosen name.\n") 
    camera_saving_folder_pathname, saving_location_root_pathname, image_specification_list = load_config()
    savefolder_pathname = None 
    while not savefolder_pathname:
        user_entered_name = prompt_for_savefolder_input() 
        is_dryrun = user_entered_name == "dryrun"
        savefolder_pathname = initialize_savefolder(saving_location_root_pathname, user_entered_name, is_dryrun)
    if is_dryrun:
        print("Running as a dry run. WARNING: All images will be deleted on termination.\n")
    print("Initializing watchdog...\n")
    my_watchdog = ImageWatchdog(camera_saving_folder_pathname, savefolder_pathname, image_specification_list, image_extension = IMAGE_EXTENSION)
    print("Running! Interrupt with Ctrl+C at your leisure.\n") 
    try:
        while True:
            image_saved = my_watchdog.associate_images_with_run()
            if(image_saved):
                print("Saved something at: ") 
                print(datetime.datetime.now().strftime("%H-%M-%S"))
    except KeyboardInterrupt:
        print("Trying to save the last images...") 
        my_watchdog.associate_images_with_run() 
        my_watchdog.save_run_parameters()
        print("Success!") 
    finally:
        if(is_dryrun):
            nuke_savefolder(savefolder_pathname)



def load_config():
    import satyendra.configs as c
    with pkg_resources.path(c, "image_saver_config_local.json") as json_config_path:
        with open(json_config_path) as json_config_file:
            config_dict = json.load(json_config_file)
            camera_saving_folder_pathname = config_dict["camera_saving_folder_pathname"]
            saving_location_root_pathname = config_dict["saving_location_root_pathname"]
            image_specification_label = config_dict["imaging_type_label"]
            image_specification_list = image_type_decoder(image_specification_label)
    return (camera_saving_folder_pathname, saving_location_root_pathname, image_specification_list)

def prompt_for_savefolder_input():
    input_is_ok = False 
    while not input_is_ok:
        print("""Please enter the measurement folder name. Using the name 'dryrun' will initialize a dry run - images will be saved, but 
        deleted when the program terminates.\n""")
        print("Only alphanumeric characters and _ allowed.\n")
        user_entered_name = input()
        if is_savefolder_name_forbidden(user_entered_name):
            print("Can't use that name. Pick another.\n")
            input_is_ok = False
            continue
        print("Is the folder name " + user_entered_name + " ok?\n") 
        print("Type 'y' (without quotes) for yes, or anything else for no.\n") 
        ok_response = input() 
        input_is_ok = ok_response == 'y' 
    return user_entered_name


def image_type_decoder(image_type_label):
    SUPPORT_LIST = ["side", "top"]
    if(not image_type_label in SUPPORT_LIST):
        raise ValueError("The specified imaging type is not supported.")
    if(image_type_label == "side"):
        return ["Side"] 
    elif(image_type_label == "top"):
        return ["TopA", "TopB"] 

def initialize_savefolder(saving_location_root_pathname, user_save_label, is_dryrun):
    current_datetime = datetime.datetime.now() 
    current_year = current_datetime.strftime("%Y")
    current_year_month = current_datetime.strftime("%Y-%m")
    current_year_month_day = current_datetime.strftime("%Y-%m-%d")
    savefolder_pathname = os.path.join(saving_location_root_pathname, current_year, current_year_month, current_year_month_day, user_save_label)
    if(os.path.isdir(savefolder_pathname) and not is_dryrun):
        print("Folder already exists. Type 'y' (no quotes) to use it anyway, or anything else to retry.\n")
        user_response = input()
        if not user_response == 'y':
            savefolder_pathname = None
    return savefolder_pathname 


def nuke_savefolder(savefolder_pathname):
    for root, dirs, files in os.walk(savefolder_pathname):
        for filename in files:
            file_path = os.path.join(root, filename) 
            os.remove(file_path)


#Function which checks for forbidden savefolder names: namely, those with any characters 
#besides alphanumeric ones or the _ character
def is_savefolder_name_forbidden(savefolder_name):
    is_abs_path = os.path.isabs(savefolder_name)
    has_special_characters = False 
    split_string = savefolder_name.split("_")
    for segment in split_string:
        segment_has_special_characters = (not segment.isalnum() and len(segment) > 0)
        has_special_characters = has_special_characters or segment_has_special_characters 
    return (is_abs_path or has_special_characters)



if __name__ == "__main__":
    main() 