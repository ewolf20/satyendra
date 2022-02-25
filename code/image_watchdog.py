import sys 
import os 
import time 
import datetime 

import numpy as np

from astropy.io import fits
from utility_functions import load_breadboard_client, get_newest_run_dict


DATETIME_FORMAT_STRING = "%m-%d-%y;%H-%M-%S"

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
        self.bc = load_breadboard_client()
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
            image_array_stack = np.stack(*image, axis = -1)
            timestamp_string = timestamp.strftime(DATETIME_FORMAT_STRING)
            image_full_name = timestamp_string + "_" + image_name
            image_save_path = os.path.join(self.no_id_folder_path, image_full_name + ".fits")
            ImageWatchdog._save_as_fits(image_save_path, image_array_stack) 



    #TODO Right now, an inelegant kludge is responsible for making sure a given frame isn't checked every time the code loops.
    #Fix this.
    """Aggregates a run worth of images from the watchfolder.
    
    Checks the watchfolder to see if there are any frames. If there are, attempts to 
    aggregate them into a run's worth of images, then moves them to the no_id_folder. 
    Discards all frames in the watchfolder if it fails to do so within the time stipulated by 
    lost_frame_patience.
    
    Remark: Only matches frames if their names contain one of the strings imagename_framename
    corresponding to an entry in self.image_specification_dict."""
    def aggregate_image_dict(self, sleep_time = 0.1):
        frame_filenames_list = self._get_frame_filenames_in_watchfolder() 
        if(len(frame_filenames_list) > 0):
            #start a timer
            start_time = time.time()
            #initialize the image dict
            image_dict = {}
            for expected_image_name in self.image_specification_dict:
                image_dict[expected_image_name] = []
                for expected_frame_name in self.image_specification_dict:
                    image_dict[expected_image_name].append(None)
            #Create a list to store the frame pathnames we've already checked
            #TODO Make more elegant!
            examined_frame_filenames_list = []
            #Loop while waiting for new frames
            counter = 0
            while(time.time() - start_time < self.lost_frame_patience):
                frame_filenames_list = self.get_frame_filenames_in_watchfolder() 
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
                time.sleep(sleep_time)
            if(counter == self.total_frames_per_run):
                self._save_run_in_no_id_folder(image_dict, datetime.datetime.today())
            self._flush_watchfolder()
                

    def _flush_watchfolder(self):
        timestamp = datetime.datetime.today() 
        timestamp_string = timestamp.strftime(DATETIME_FORMAT_STRING)
        frame_filenames_list = self._get_frames_in_watchfolder() 
        for frame_filename in frame_filenames_list:
            frame_pathname = os.path.join(self.watchfolder_path, frame_filename)
            if(self.delete_lost_frames):
                os.remove(frame_pathname)
            else:
                timestamped_frame_filename = DATETIME_FORMAT_STRING + "_" + frame_filename
                lost_frames_pathname = os.path.join(self.lost_frame_path, timestamped_frame_filename) 
                os.rename(frame_pathname, lost_frames_pathname)


    """
    Returns a list of the current frames in the watchfolder.

    Remark: Though this function checks that the frame exists by creating a full path to it, 
    the names returned are just file names, 
    """
    def _get_frame_filenames_in_watchfolder(self):
        if(self.frame_file_type == "tiff8" or self.frame_file_type == "tiff16"):
            file_extension_string = ".tiff"
        else:
            file_extension_string = ""
        frames_list = [os.path.join(self.watchfolder_path, f) for f in os.listdir(self.watchfolder_path) 
                        if (os.path.isfile(os.path.join(self.watchfolder_path, f)) 
                        and file_extension_string in f)]
        return frames_list




    """
    Loads a camera frame into numpy array format
    
    Given a frame image saved by a camera at location frame_filename, loads the frame as a 
    numpy array. Meant to cleanly wrap various types of frames.
    
    Parameters:
    
    frame_pathname: The path to the frame to be loaded.
    frame_type: A string specifying the type of frame to load as a numpy array. Currently, options are 
        'tiff8': An 8-bit (greyscale) tiff file. 
        'tiff16': A 16-bit (greyscale) tiff file.
    """
    @staticmethod 
    def _load_frame_as_array(frame_pathname, frame_type):
        SUPPORTED_FRAMETYPES_STRING = " tiff8 tiff16" 
        if(frame_type == "tiff8"):
            pass 
        elif(frame_type == "tiff16"):
            pass
        else:
            raise ValueError("Frame type not supported.")





    




        