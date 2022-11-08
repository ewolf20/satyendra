import datetime
import json
import os 
import shutil
import time 

from astropy.io import fits
import numpy as np
from PIL import Image, UnidentifiedImageError

from satyendra.code import breadboard_functions, crypto_functions



DATETIME_FORMAT_STRING = "%Y-%m-%d--%H-%M-%S"
FILENAME_DELIMITER_CHAR = '_'

SUPPORTED_FRAME_FILETYPES = ["tiff8", "tiff16"]

class ImageWatchdog():

    """
    Initialization method. 

    Parameters:


    image_specification_list: A list specifying the image names which the watchdog looks for in a run, sans file extensions and initial timestamps.

    watchfolder: A path string to the folder to watch for incoming images from the cameras.

    savefolder: A path string to the folder in which to save the grouped-up .fits images. Within it will be subfolders for images without run_IDs
        and lost camera frames. 

    breadboard_mismatch_tolerance: A float giving the time difference, in seconds, which watchdog is willing to accept between the timestamp on
        the breadboard_df and the timestamp on an image saved by the camera. 

    image_extension: The file extension of the images. Default is ".fits"

    Remark: No separator should be at the end of directory pathnames.
    
    """
    def __init__(self, watchfolder_path, savefolder_path, image_specification_list, breadboard_mismatch_tolerance = 5.0, image_extension = ".fits"):
        self.image_specification_list = image_specification_list
        self.watchfolder_path = watchfolder_path
        self.savefolder_path = savefolder_path
        if(not os.path.isdir(self.savefolder_path)):
            os.makedirs(self.savefolder_path)
        self.no_id_folder_path = os.path.join(self.savefolder_path, "no_id")
        if(not os.path.isdir(self.no_id_folder_path)):
            os.mkdir(self.no_id_folder_path)
        self.breadboard_mismatch_tolerance = breadboard_mismatch_tolerance
        self.bc = breadboard_functions.load_breadboard_client()
        self.image_extension = image_extension
        experiment_parameters_filename = os.path.join(self.savefolder_path, "experiment_parameters.json")
        with open(experiment_parameters_filename, 'w') as experiment_parameters_file:
            experiment_parameters = crypto_functions.get_plaintext_experiment_parameters()
            json.dump(experiment_parameters, experiment_parameters_file)
        self.parameters_dict = {}

    #TODO: Implement method for mass-matching if use case exists. Otherwise, takes ~5s to run
    """
    Function for matching datetimes to unlabeled runs in the watchfolder.

    Function which scans the savefolder for images which have yet to be labeled with an ID, 
    then tries to match a single set of them if unlabeled.
    
    Parameters:
    
    labelling_waiting_period: Method will not attempt to match run IDs for any images 
    whose datetimes are less than this many seconds before the present. Workaround for 
    delays in runs reaching the server.
    
    mismatch_tolerance: The tolerated difference between the time on breadboard and the timestamp of the image to associate a run id."""
    def associate_images_with_run(self, labelling_waiting_period = 5, mismatch_tolerance = 5, allow_missing_ids = True, verbose = True):
        image_filename_list = self._get_image_filenames_in_watchfolder() 
        valid_timestamps_list = []
        valid_datetimes_list = [] 
        labeled_image_bool = False
        for image_filename in image_filename_list:
            checked_datetime_string = image_filename.split(FILENAME_DELIMITER_CHAR, 1)[0] 
            checked_datetime = datetime.datetime.strptime(checked_datetime_string, DATETIME_FORMAT_STRING)
            checked_current_timedelta = datetime.datetime.now() - checked_datetime
            if(checked_current_timedelta.total_seconds() > labelling_waiting_period and not checked_datetime_string in valid_timestamps_list):
                valid_timestamps_list.append(checked_datetime_string)
                valid_datetimes_list.append(checked_datetime)
        datetime_and_run_parameters_list = breadboard_functions.get_run_parameter_dicts_from_datetimes(self.bc, valid_datetimes_list, 
                                                                            allowed_seconds_deviation = mismatch_tolerance, 
                                                                            allow_fails = allow_missing_ids, verbose = verbose)
        run_parameters_list = [f[1] for f in datetime_and_run_parameters_list]
        for run_parameters, timestamp in zip(run_parameters_list, valid_timestamps_list):
            labeled_image_bool = True
            same_timestamp_filename_list = [f for f in image_filename_list if timestamp in f]
            for same_timestamp_filename in same_timestamp_filename_list:
                original_pathname = os.path.join(self.watchfolder_path, same_timestamp_filename)
                if(not run_parameters is None):
                    run_id = run_parameters["id"]
                    labelled_filename = str(run_id) + FILENAME_DELIMITER_CHAR + same_timestamp_filename 
                    new_pathname = os.path.join(self.savefolder_path, labelled_filename)
                    self.parameters_dict[run_id] = run_parameters
                else:
                    labelled_filename = "unmatched" + FILENAME_DELIMITER_CHAR + same_timestamp_filename
                    new_pathname = os.path.join(self.no_id_folder_path, labelled_filename)
                #Use shutil instead of os.rename to allow copying across drives
                shutil.move(original_pathname, new_pathname)
        if(labeled_image_bool):
            self.save_run_parameters()
        return labeled_image_bool

    def save_run_parameters(self, parameters_filename = "run_params_dump.json"):
        parameters_pathname = os.path.join(self.savefolder_path, parameters_filename)
        SAVING_PATIENCE = 3
        counter = 0 
        while counter < SAVING_PATIENCE:
            try:
                if os.path.exists(parameters_pathname):
                    with open(parameters_pathname, 'r') as f:
                        initial_dict = json.load(f)
                else:
                    initial_dict = {}
                appended_dict = initial_dict 
                for key in self.parameters_dict:
                    appended_dict[key] = self.parameters_dict[key]
                with open(parameters_pathname, 'w') as f:
                    f.write(json.dumps(appended_dict))
                self.parameters_dict = {}
                break
            except OSError as e:
                counter += 1 
                if(counter >= SAVING_PATIENCE):
                    raise e

    """
    Returns a list of the current images in the watchfolder.

    Remark: Though this function checks that the image exists by creating a full path to it, 
    the names returned are just file names.
    """
    def _get_image_filenames_in_watchfolder(self):
        images_list = [f for f in os.listdir(self.watchfolder_path) 
                        if (os.path.isfile(os.path.join(self.watchfolder_path, f)) and self.image_extension in f)
                        and any([image_name in f for image_name in self.image_specification_list])]
        return images_list


    """
    Function for saving a run parameters json in legacy datasets for which it wasn't autosaved."""
    @staticmethod 
    def get_run_metadata(folder_path, image_extension_string = ".fits", dump_filename = "run_params_dump.json"):
        bc = breadboard_functions.load_breadboard_client()
        filenames_list = [f.split('.')[0] for f in os.listdir(folder_path) if image_extension_string in f] 
        run_ids_list = [int(f.split(FILENAME_DELIMITER_CHAR)[0]) for f in filenames_list]
        datetimes_list = [datetime.datetime.strptime(f.split(FILENAME_DELIMITER_CHAR)[1], DATETIME_FORMAT_STRING) for f in filenames_list]
        min_datetime = min(datetimes_list) 
        max_datetime = max(datetimes_list)
        #This is O(n)
        unique_run_ids_list = list(set(run_ids_list))
        sorted_unique_run_ids_list = sorted(unique_run_ids_list)
        params_dict_list = breadboard_functions.get_run_parameter_dicts_from_ids(bc, sorted_unique_run_ids_list, start_datetime = min_datetime, 
                                                                                end_datetime = max_datetime, verbose = True)
        run_parameters_dump_dict = {}
        for run_id, params_dict in zip(sorted_unique_run_ids_list, params_dict_list):
            run_parameters_dump_dict[run_id] = params_dict 
        dump_pathname = os.path.join(folder_path, dump_filename)
        with open(dump_pathname, 'w') as dump_file:
            json.dump(run_parameters_dump_dict, dump_file)
        
        

    """
    Function for bringing legacy filenames into conformance with the standard established by watchdog going forward.
    Given a folder, runs through a list of legacy filename types and recasts the filenames in the folder into the standard
    runID_datetimestring_imagetype format established in satyendra.
    
    The method assumes that the runs are in either the runID_datetimestring_imagename format, the abridged datetimestring_imagename format, 
    or the maximally abridged datetimestring format (for which the imagename can still be deduced, since we only saved side images this way).
    Note that the method _will fail_ if two different datetime string formats are mixed."""
    @staticmethod 
    def clean_filenames(folder_path, image_extension_string = '.fits', image_type_default = None, allowed_seconds_deviation = 5):
        datetime_formats = ["%Y-%m-%d--%H-%M-%S", "%m-%d-%Y_%H_%M_%S"]
        filenames_list = [f.split('.')[0] for f in os.listdir(folder_path) if image_extension_string in f]
        for datetime_format in datetime_formats:
            filename_run_id_strings_list = []
            filename_datetimes_list = [] 
            filename_image_type_strings_list = []
            run_ids_absent = False 
            try:
                for filename in filenames_list:
                    if(FILENAME_DELIMITER_CHAR in datetime_format):
                        datetime_string_split_length = len(datetime_format.split(FILENAME_DELIMITER_CHAR)) 
                        split_filename_array = filename.split(FILENAME_DELIMITER_CHAR) 
                        if(len(split_filename_array) == datetime_string_split_length + 2):
                            run_id_string = split_filename_array[0]
                            image_type_string = split_filename_array[-1]
                            datetime_string = FILENAME_DELIMITER_CHAR.join(split_filename_array[1:-1]) 
                        elif(len(split_filename_array) == datetime_string_split_length + 1):
                            run_ids_absent = True
                            run_id_string = ''
                            image_type_string = split_filename_array[-1] 
                            datetime_string = FILENAME_DELIMITER_CHAR.join(split_filename_array[:-1])
                        elif len(split_filename_array) == datetime_string_split_length:
                            if image_type_default:
                                run_ids_absent = True
                                image_type_string = image_type_default
                                run_id_string = '' 
                                datetime_string = FILENAME_DELIMITER_CHAR.join(split_filename_array)
                            else:
                                raise ValueError("Unable to determine the image type; try specifying it manually.")
                        else:
                            raise ValueError("Unable to parse the filename")
                    else:
                        split_filename_array = filename.split(FILENAME_DELIMITER_CHAR)
                        if(len(split_filename_array) == 3):
                            run_id_string = split_filename_array[0] 
                            datetime_string = split_filename_array[1] 
                            image_type_string = split_filename_array[2] 
                        elif(len(split_filename_array) == 2):
                            run_ids_absent = True
                            run_id_string = ''
                            datetime_string = split_filename_array[0] 
                            image_type_string = split_filename_array[1]
                        elif(len(split_filename_array) == 1):
                            if image_type_default:
                                run_ids_absent = True
                                image_type_string = image_type_default
                                run_id_string = '' 
                                datetime_string = split_filename_array[0]
                            else:
                                raise ValueError("Unable to determine the image type; try specifying it manually.")
                        else:
                            raise ValueError("Unable to parse the filename.")
                    filename_run_id_strings_list.append(run_id_string)
                    #Removes a space that exists in some legacy datetimes
                    datetime_string = datetime_string.replace(' ', '')
                    filename_datetime = datetime.datetime.strptime(datetime_string, datetime_format)
                    filename_datetimes_list.append(filename_datetime)
                    filename_image_type_strings_list.append(image_type_string)
            except ValueError as e:
                continue
            else:
                if run_ids_absent:
                    #GET RUN IDS
                    bc = breadboard_functions.load_breadboard_client()
                    datetime_and_run_parameters_tuple_list = breadboard_functions.get_run_parameter_dicts_from_datetimes(bc, filename_datetimes_list, 
                                                                                                            allowed_seconds_deviation = allowed_seconds_deviation)
                    filename_run_ids = [f[1]['id'] for f in datetime_and_run_parameters_tuple_list]
                    for old_filename, run_id, filename_datetime, image_type_string in zip(filenames_list, filename_run_ids, filename_datetimes_list, 
                                                                        filename_image_type_strings_list):
                        new_filename_with_extension= FILENAME_DELIMITER_CHAR.join((str(run_id), filename_datetime.strftime(DATETIME_FORMAT_STRING), image_type_string)) + image_extension_string
                        old_filename_with_extension = old_filename + image_extension_string
                        old_pathname = os.path.join(folder_path, old_filename_with_extension)
                        new_pathname = os.path.join(folder_path, new_filename_with_extension)
                        os.rename(old_pathname, new_pathname)
                else:
                    for old_filename, run_id_string, filename_datetime, image_type_string in zip(filenames_list, filename_run_id_strings_list, filename_datetimes_list,
                                                                                 filename_image_type_strings_list):
                        new_filename_with_extension = FILENAME_DELIMITER_CHAR.join((run_id_string,  filename_datetime.strftime(DATETIME_FORMAT_STRING), image_type_string)) + image_extension_string
                        old_filename_with_extension = old_filename + image_extension_string
                        old_pathname = os.path.join(folder_path, old_filename_with_extension)
                        new_pathname = os.path.join(folder_path, new_filename_with_extension)
                        os.rename(old_pathname, new_pathname)
                return True
        return False



                        
                    