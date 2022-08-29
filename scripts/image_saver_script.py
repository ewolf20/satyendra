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
    camera_saving_folder_pathname, saving_location_root_pathname = load_config()
    savefolder_pathname = None 
    while not savefolder_pathname:
        user_entered_name = prompt_for_savefolder_input() 
        savefolder_pathname = initialize_savefolder(saving_location_root_pathname, user_entered_name)
    is_dryrun = user_entered_name == "dryrun"
    if is_dryrun:
        print("Running as a dry run. WARNING: All images will be deleted on termination.\n")
    image_specification_list = prompt_for_image_type_input()
    print("Initializing watchdog...\n")
    my_watchdog = ImageWatchdog(camera_saving_folder_pathname, savefolder_pathname, image_specification_list, image_extension = IMAGE_EXTENSION)
    print("Running! Interrupt with Ctrl+C at your leisure.\n") 
    try:
        while True:
            image_saved = my_watchdog.label_images_with_run_ids()
            if(image_saved):
                print("Saved something at: ") 
                print(datetime.datetime.now().strftime("%H-%M-%S"))
    except KeyboardInterrupt:
        print("Trying to save the last images...") 
        my_watchdog.label_images_with_run_ids() 
        print("Success!") 
    finally:
        if(is_dryrun):
            nuke_savefolder(savefolder_pathname)


def nuke_savefolder(savefolder_pathname):
    for root, dirs, files in os.walk(savefolder_pathname):
        for filename in files:
            file_path = os.path.join(root, filename) 
            os.remove(file_path)


def load_config():
    import satyendra.configs as c
    with pkg_resources.path(c, "image_saver_config_local.json") as json_config_path:
        with open(json_config_path) as json_config_file:
            config_dict = json.load(json_config_file)
            camera_saving_folder_pathname = config_dict["camera_saving_folder_pathname"]
            saving_location_root_pathname = config_dict["saving_location_root_pathname"]
    return (camera_saving_folder_pathname, saving_location_root_pathname)

def prompt_for_savefolder_input():
    input_is_ok = False 
    while not input_is_ok:
        print("""Please enter the measurement folder name. Using the name 'dryrun' will initialize a dry run - images will be saved, but 
        deleted when the program terminates.\n""")
        print("Please don't use weird characters.")
        user_entered_name = input()
        print("Is the folder name " + user_entered_name + " ok?\n") 
        print("Type 'y' (without quotes) for yes, or anything else for no.\n") 
        ok_response = input() 
        input_is_ok = ok_response == 'y' 
    return user_entered_name


def prompt_for_image_type_input():
    SUPPORT_LIST = ["side", "top"]
    input_is_ok = False 
    while not input_is_ok:
        print("Please enter the type of imaging. Supported imaging types as of now are: \n") 
        for image_type in SUPPORT_LIST:
            print(image_type + "\n")
        user_input = input() 
        input_is_ok = user_input in SUPPORT_LIST
    if(user_input == "side"):
        return ["Side"] 
    elif(user_input == "top"):
        return ["TopA", "TopB"] 


def initialize_savefolder(saving_location_root_pathname, user_save_label):
    current_datetime = datetime.datetime.now() 
    current_year = current_datetime.strftime("%Y")
    current_year_month = current_datetime.strftime("%Y-%m")
    current_year_month_day = current_datetime.strftime("%Y-%m-%d")
    savefolder_pathname = os.path.join(saving_location_root_pathname, current_year, current_year_month, current_year_month_day, user_save_label)
    if(os.path.isdir(savefolder_pathname)):
        print("Folder already exists. Type 'y' (no quotes) to use it anyway, or anything else to retry.\n")
        user_response = input()
        if not user_response == 'y':
            savefolder_pathname = None
    return savefolder_pathname 

if __name__ == "__main__":
    main() 