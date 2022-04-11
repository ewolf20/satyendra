import datetime 
import os 
import time 

from astropy.io import fits
import numpy as np
from PIL import Image, UnidentifiedImageError

from satyendra.code import utility_functions



DATETIME_FORMAT_STRING = "%Y-%m-%d--%H-%M-%S"

SUPPORTED_FRAME_FILETYPES = ["tiff8", "tiff16"]

class ImageWatchdog():

    """
    Initialization method. 

    Parameters:


    image_specification_dict: A dictionary specifying the way in which the watchdog tries to group images together. 
        Syntax is {image1Name:[frameA1Name, frameB1name, frameC1name, ...], image2Name:[frameA2name, frameB2name, ...], ...}
        Image names specify the name of the image to be formed from frames (e.g. 'TopState1'), while frame names specify the name of frames within an image 
        (e.g. 'PWA', picture with atoms). Watchdog will look for frames with the naming convention imageName_frameName, and aggregate them into a single image 
        with name run_ID_Timestamp_ImageName. The order of the frames will be that specified in the list. 
    watchfolder: A path string to the folder to watch for incoming frames from the cameras.
    savefolder: A path string to the folder in which to save the grouped-up .fits images. Within it will be subfolders for images without run_IDs
        and lost camera frames. 
    delete_lost_frames: A boolean which specifies what happens when not all frames for a run are found. If true, they are discarded. If false, they are 
        saved in a lost_frames folder. Default True. 
    lost_frame_patience: A float giving the time, in seconds, which watchdog is willing to wait between getting the first frame of a run and the last. 
        If this time is exceeded, it assumes that a frame has been lost and gives up on the run.
    breadboard_mismatch_tolerance: A float giving the time difference, in seconds, which watchdog is willing to accept between the timestamp on
        the breadboard_df and the local time when the last frame in a run appears. 
    frame_type: A string identifying the type of file which encodes the frames. Default is "tiff8"

    Remark: No separator should be at the end of directory pathnames.
    
    """
    def __init__(self, image_specification_dict, watchfolder_path, savefolder_path, 
                delete_lost_frames = True, lost_frame_patience = 10.0, breadboard_mismatch_tolerance = 5.0, frame_file_type = "tiff8"):
        self.image_specification_dict = image_specification_dict 
        self.total_frames_per_run = 0 
        for key in image_specification_dict:
            self.total_frames_per_run += len(image_specification_dict[key]) 
        self.watchfolder_path = watchfolder_path
        self.savefolder_path = savefolder_path
        if(not os.path.isdir(self.savefolder_path)):
            os.mkdir(self.savefolder_path)
        self.no_id_folder_path = os.path.join(savefolder_path, "no_id")
        if(not os.path.isdir(self.no_id_folder_path)):
            os.mkdir(self.no_id_folder_path)
        self.delete_lost_frames = delete_lost_frames
        if(not delete_lost_frames):
            self.lost_frame_path = os.path.join(savefolder_path, "lost_frames")
            if(not os.path.isdir(self.lost_frame_path)):
                os.mkdir(self.lost_frame_path) 
        self.lost_frame_patience = lost_frame_patience 
        self.breadboard_mismatch_tolerance = breadboard_mismatch_tolerance
        self.bc = utility_functions.load_breadboard_client()
        if(not frame_file_type in SUPPORTED_FRAME_FILETYPES):
            warning_string = "Specified frame filetype is not supported. Supported filetypes include:"
            for file_type in SUPPORTED_FRAME_FILETYPES:
                warning_string += " " + file_type
            raise ValueError(warning_string)
        self.frame_file_type = frame_file_type


        

    
    """
    Saves a run into the no_ids_folder, to be subsequently sorted.
    
    Parameters:
    
    Image dict: A dict {imagename1: (frame1, frame2, ...), imagename2: (frame1, frame2, ...)} 
        containing images to be saved, themselves iterables containing frames as numpy arrays.
    Timestamp: The time (in datetime format) when the final frame for a run was detected; corresponds to the time the run finished."""
    
    def _save_run_in_no_id_folder(self, image_dict, timestamp):
        for image_name in image_dict:
            image = image_dict[image_name] 
            image_array_stack = np.stack(image, axis = -1)
            timestamp_string = timestamp.strftime(DATETIME_FORMAT_STRING)
            timestamped_image_name = timestamp_string + "_" + image_name
            image_save_path = os.path.join(self.no_id_folder_path, timestamped_image_name + ".fits")
            ImageWatchdog._save_as_fits(image_save_path, image_array_stack) 


    @staticmethod
    def _save_as_fits(image_save_path, image_array_stack):
        hdu = fits.PrimaryHDU(image_array_stack)
        hdu.writeto(image_save_path) 

    #TODO Right now, an inelegant kludge is responsible for making sure a given frame isn't checked every time the code loops.
    #Fix this.
    #BUG: Can throw a zsh bus error (seg fault) in terminal when images are being saved to the watchfolder at ultra-speed.
    #To replicate, just write a program which saves images as fast as it can. 
    """Aggregates a run worth of images from the watchfolder.
    
    Checks the watchfolder to see if there are any frames. If there are, attempts to 
    aggregate them into a run's worth of images, then moves them to the no_id_folder. 
    Discards all frames in the watchfolder if it fails to do so within the time stipulated by 
    lost_frame_patience.

    Returns: True if an image has successfully been aggregated into the watchfolder; false otherwise.
    
    Remark: Only matches frames if their names contain one of the strings imagename_framename
    corresponding to an entry in self.image_specification_dict."""

    def save_labeled_frames_into_images(self, sleep_time = 0.1):
        frame_filenames_list = self._get_frame_filenames_in_watchfolder() 
        if(len(frame_filenames_list) > 0):
            filename_match_list = [] 
            for expected_image_name in self.image_specification_dict:
                for expected_frame_name in self.image_specification_dict[expected_image_name]:
                    filename_match_list.append(expected_image_name + "_" + expected_frame_name) 
            try:
                found_frames_list = self._scan_watchfolder_for_frames(filename_match_list)
            except RuntimeError:
                return False 
            else:
                image_dict = self._group_labeled_frames_into_image_dict(found_frames_list)
                most_recent_frame_datetime = self._get_most_recent_frame_datetime(found_frames_list) 
                self._save_run_in_no_id_folder(image_dict, most_recent_frame_datetime)
                self._flush_watchfolder(failed = False)
                return True 
        else:
            return False

    """
    Helper function for looking for frames in the watchfolder which match a certain image name.

    Scans the watchfolder for frames which contain a substring from an array of possible names. If it finds a number of frames 
    equal to the number it expects for a single run within the time given by self.lost_frame_patience, it returns them in an array.

    Parameters:

    match_array: An array of substrings; a frame is only recognized if its name contains one of these strings. 
    """
    def _scan_watchfolder_for_frames(self, match_array = None, sleep_time = 0.1):
        start_time = time.time()
        found_frame_filenames_list = []
        counter = 0
        while(time.time() - start_time < self.lost_frame_patience and counter < self.total_frames_per_run):
            frame_filenames_list = self._get_frame_filenames_in_watchfolder() 
            for frame_filename in frame_filenames_list:
                if(frame_filename in found_frame_filenames_list):
                        continue
                for match_string in match_array:
                    if match_string in frame_filename:
                        found_frame_filenames_list.append(frame_filename)
                        break
            time.sleep(sleep_time)
            if(len(found_frame_filenames_list) == self.total_frames_per_run):
                return found_frame_filenames_list
        self._flush_watchfolder(failed = True)
        raise RuntimeError("Unable to find all of the frames for the run.")


    def _group_labeled_frames_into_image_dict(self, frame_filename_list):
        image_dict = {} 
        for expected_image_name in self.image_specification_dict:
            image_dict[expected_image_name] = []
            for expected_frame_name in self.image_specification_dict[expected_image_name]:
                for frame_filename in frame_filename_list:
                    if(expected_image_name + "_" + expected_frame_name in frame_filename):
                        frame_pathname = os.path.join(self.watchfolder_path, frame_filename)
                        frame_array = ImageWatchdog._load_frame_as_array(frame_pathname, self.frame_file_type)
                        image_dict[expected_image_name].append(frame_array)
                        break 
                else:
                    raise RuntimeError("One of the frames does not have a filename matching the image specification dict.")
        return image_dict



    def _get_most_recent_frame_datetime(self, frame_filename_list):
        most_recent_datetime = datetime.datetime.fromtimestamp(0) 
        for frame_filename in frame_filename_list:
            frame_pathname = os.path.join(self.watchfolder_path, frame_filename)
            frame_timestamp = os.path.getmtime(frame_pathname)
            frame_datetime = datetime.datetime.fromtimestamp(frame_timestamp) 
            if(frame_datetime > most_recent_datetime):
                most_recent_datetime = frame_datetime 
        return most_recent_datetime

    """
    Method for saving unlabeled but sequential frames into images.
    
    Scans the watchfolder for frames to aggregate into images as in save_labeled_frames_into_images, but 
    instead of relying on them being labeled, assumes that they are always received in a given order.
    
    order_list: An list [imagename_framename, imagename_framename2] which specifies the order in which entries {'imagename':[framename]} of the 
    image specification dict appear in the watchfolder. If not provided, the default is a depth-first
    enumeration [imagename1_framename1, imagename1_framename2, ... imagename2_framename1]."""

    def save_sequential_frames_into_images(self, order_list = None, sleep_time = 0.1):
        frame_filenames_list = self._get_frame_filenames_in_watchfolder() 
        if(len(frame_filenames_list) > 0):
            #start a timer
            start_time = time.time()
            #initialize the image dict and, if not specified, the order list
            image_dict = {}
            for expected_image_name in self.image_specification_dict:
                image_dict[expected_image_name] = []
                for expected_frame_name in self.image_specification_dict[expected_image_name]:
                    image_dict[expected_image_name].append(None)
            if not order_list:
                order_list = [] 
                for image_name in self.image_specification_dict:
                    for frame_name in self.image_specification_dict[image_name]:
                        order_list.append(image_name + "_" + frame_name) 
            #Create a list to store the frame pathnames we've already checked
            examined_frame_filenames_list = []
            most_recent_frame_datetime = datetime.datetime.fromtimestamp(0)
            counter = 0
            while(time.time() - start_time < self.lost_frame_patience and counter < self.total_frames_per_run):
                frame_filenames_list = self._get_frame_filenames_in_watchfolder() 
                for frame_filename in frame_filenames_list:
                    if(frame_filename in examined_frame_filenames_list):
                        continue
                    for expected_image_name in self.image_specification_dict:
                        for index, expected_frame_name in enumerate(self.image_specification_dict[expected_image_name]):
                            if (expected_image_name + "_" + expected_frame_name in frame_filename):
                                frame_pathname = os.path.join(self.watchfolder_path, frame_filename)
                                frame_array = ImageWatchdog._load_frame_as_array(frame_pathname, self.frame_file_type)
                                image_dict[expected_image_name][index] = frame_array
                                counter += 1
                    examined_frame_filenames_list.append(frame_filename)
                    frame_pathname = os.path.join(self.watchfolder_path, frame_filename)
                    current_frame_timestamp = os.path.getmtime(frame_pathname)
                    current_frame_datetime = datetime.datetime.fromtimestamp(current_frame_timestamp) 
                    if(current_frame_datetime > most_recent_frame_datetime):
                        most_recent_frame_datetime = current_frame_datetime
                time.sleep(sleep_time)
            if(counter == self.total_frames_per_run):
                self._save_run_in_no_id_folder(image_dict, most_recent_frame_datetime)
                self._flush_watchfolder() 
                return True 
            else:
                self._flush_watchfolder()
                return False
        else:
            return False


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
    def label_image_with_run_id(self, labelling_waiting_period = 5, mismatch_tolerance = 5):
        image_filename_list = self._get_frame_filenames_in_no_id_folder() 
        no_failures_bool = True
        cleaned_image_filename_list = [filename for filename in image_filename_list if (not 'unmatchable' in filename)] 
        for checked_image_filename in cleaned_image_filename_list: 
            checked_datetime_string = checked_image_filename.split('_', 1)[0] 
            checked_datetime = datetime.datetime.strptime(checked_datetime_string, DATETIME_FORMAT_STRING)
            checked_current_timedelta = datetime.datetime.now() - checked_datetime
            if(checked_current_timedelta.total_seconds() > labelling_waiting_period):
                target_datetime_string = checked_datetime_string
                target_datetime = checked_datetime
                break 
        else:
            return False 
        same_timestamp_image_filename_list = [filename for filename in image_filename_list if (target_datetime_string in filename)]
        try:
            run_id = utility_functions.get_run_id_from_datetime(self.bc, target_datetime,
                                                                 allowed_seconds_before = mismatch_tolerance, allowed_seconds_after = mismatch_tolerance)
        except RuntimeError as e:
                no_failures_bool = False
                for original_image_filename in same_timestamp_image_filename_list:
                    original_image_pathname = os.path.join(self.no_id_folder_path, original_image_filename)
                    unmatchable_image_filename = 'unmatchable_' + original_image_filename 
                    unmatchable_image_pathname = os.path.join(self.no_id_folder_path, unmatchable_image_filename)
                    os.rename(original_image_pathname, unmatchable_image_pathname)
        else:
            for original_image_filename in same_timestamp_image_filename_list:
                original_image_pathname = os.path.join(self.no_id_folder_path, original_image_filename)
                labeled_image_filename = str(run_id) + '_' + original_image_filename 
                labeled_image_pathname = os.path.join(self.savefolder_path, labeled_image_filename)
                os.rename(original_image_pathname, labeled_image_pathname)
        return no_failures_bool


    def _flush_watchfolder(self, failed = False):
        timestamp = datetime.datetime.today() 
        timestamp_string = timestamp.strftime(DATETIME_FORMAT_STRING)
        frame_filenames_list = self._get_frame_filenames_in_watchfolder() 
        for frame_filename in frame_filenames_list:
            frame_pathname = os.path.join(self.watchfolder_path, frame_filename)
            if(failed and not self.delete_lost_frames):
                timestamped_frame_filename = timestamp_string + "_" + frame_filename
                lost_frames_pathname = os.path.join(self.lost_frame_path, timestamped_frame_filename) 
                os.rename(frame_pathname, lost_frames_pathname)            
            else:
                os.remove(frame_pathname) 



    """
    Returns a list of the current frames in the watchfolder.

    Remark: Though this function checks that the frame exists by creating a full path to it, 
    the names returned are just file names.
    """
    def _get_frame_filenames_in_watchfolder(self):
        if(self.frame_file_type == "tiff8" or self.frame_file_type == "tiff16"):
            file_extension_string = ".tiff"
        else:
            file_extension_string = ""
        frames_list = [f for f in os.listdir(self.watchfolder_path) 
                        if (os.path.isfile(os.path.join(self.watchfolder_path, f)) 
                        and file_extension_string in f)]
        return frames_list


    def _get_frame_filenames_in_no_id_folder(self):
        file_extension_string = ".fits"
        frames_list = [f for f in os.listdir(self.no_id_folder_path) 
                        if (os.path.isfile(os.path.join(self.no_id_folder_path, f)) 
                        and file_extension_string in f)]
        return frames_list




    #TODO: Remove the retry_time kludge and actually check if the file is done writing. 
    """
    Loads a camera frame into numpy array format
    
    Given a frame image saved by a camera at location frame_filename, loads the frame as a 
    numpy array. Meant to cleanly wrap various types of frames.
    
    Parameters:
    
    frame_pathname: The path to the frame to be loaded.
    frame_type: A string specifying the type of frame to load as a numpy array. Currently, options are 
        'tiff8': An 8-bit (greyscale) tiff file. 
        'tiff16': A 16-bit (greyscale) tiff file.
    retry_time: Time to wait after a PIL.UnidentifiedImageError to try reloading the image

    Remark: An error can occur if the watchdog attempts to load an image as it is being saved; the filename 
    will be present, but the image will be unreadable by PIL. The retry_time is a workaround to avoid this. 
    """
    @staticmethod 
    def _load_frame_as_array(frame_pathname, frame_type, retry_time = 0.01):
        try:
            return ImageWatchdog._load_frame_as_array_helper(frame_pathname, frame_type)
        except UnidentifiedImageError:
            time.sleep(retry_time)
            return ImageWatchdog._load_frame_as_array_helper(frame_pathname, frame_type)


    @staticmethod 
    def _load_frame_as_array_helper(frame_pathname, frame_type):
        if(frame_type == "tiff8"):
            im = Image.open(frame_pathname) 
            return np.array(im)
        elif(frame_type == "tiff16"):
            im = Image.open(frame_pathname) 
            return np.array(im)
        else:
            raise ValueError("Frame type not supported.")


    """
    Function for bringing legacy filenames into conformance with the standard established by watchdog going forward.
    Given a folder, runs through a list of legacy filename types and recasts the filenames in the folder into the standard
    runID_datetimestring_imagetype format established in satyendra.
    
    The method assumes that the runs are in either the runID_datetimestring_imagename format, or that they are in the 
    abridged datetimestring_imagename format, from which the run ids can be extracted by querying breadboard."""
    @staticmethod 
    def clean_filenames(folder):
        filename_formats = ["%Y-%m-%d--%H-%M-%S", "%m-%d-%y_%H_%M_%S"]
        filenames_list = os.listdir(folder)
        for filename_format in filename_formats:
            filename_run_ids_list = []
            filename_datetime_strings_list = [] 
            filename_image_type_strings_list = []
            run_ids_absent = False 
            try:
                for filename in filenames_list:
                    file_path = os.path.join(folder, filename)
                    if('_' in filename_format):
                        datetime_string_split_length = len(filename_format.split('_')) 
                        split_filename_array = filename.split('_') 
                        if(len(split_filename_array == datetime_string_split_length + 2)):
                            run_id_string = split_filename_array[0] 
                            image_type_string = split_filename_array[-1]
                            datetime_string = '_'.join(split_filename_array[1:-1]) 
                        elif(len(split_filename_array == datetime_string_split_length + 1)):
                            run_id_string = ''
                            image_type_string = split_filename_array[-1] 
                            datetime_string = '_'.join(split_filename_array[:-1])
                        else:
                            raise ValueError("Unable to parse the filename")
                    else:
                        pass
                        split_filename_array = filename.split('_')
                        if(len(split_filename_array) == 3):
                            run_id_string = split_filename_array[0] 
                            datetime_string = split_filename_array[1] 
                            image_type_string = split_filename_array[2] 
                        elif(len(split_filename_array) == 2):
                            run_ids_absent = True
                            run_id_string = ''
                            datetime_string = split_filename_array[0] 
                            image_type_string = split_filename_array[1]
                        else:
                            raise ValueError("Unable to parse the filename.")
                    filename_run_ids_list.append(run_id_string)
                    filename_datetime_strings_list.append(datetime_string)
                    filename_image_type_strings_list.append(image_type_string)
                    
            except ValueError:
                continue