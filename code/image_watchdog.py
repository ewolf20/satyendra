import sys 
import os 
import time 
import datetime 

import numpy as np

from astropy.io import fits
from utility_functions import load_breadboard_client, get_newest_run_dict


DATETIME_FORMAT_STRING = "%m-%d-%y_%H_%M_%S"



class ImageWatchdog():

    """
    Initialization method. 

    Parameters:

    watchfolder: A path string to the folder to watch for incoming frames from the cameras
    savefolder: A path string to the folder in which to save the grouped-up .fits images 
    no_id_folder: A path string to the folder in which to save images which cannot be matched to a run_id
    image_specification_dict: A dictionary specifying the way in which the watchdog tries to group images together. 
        Syntax is {image1Name:[frameA1Name, frameB1name, frameC1name, ...], image2Name:[frameA2name, frameB2name, ...], ...}
        Image names specify the name of the image to be formed from frames (e.g. 'TopState1'), while frame names specify the name of frames within an image 
        (e.g. 'PWA', picture with atoms). Watchdog will look for frames with the naming convention imageName_frameName, and aggregate them into a single image 
        with name imageName_timestamp_runID. The order of the frames will be that specified in the list. 
    lost_frame_patience: A float giving the time, in seconds, which watchdog is willing to wait between getting the first frame of a run and the last. 
        If this time is exceeded, it assumes that a frame has been lost and gives up on the run.
    breadboard_mismatch_tolerance: A float giving the time difference, in seconds, which watchdog is willing to accept between the timestamp on
        the breadboard_df and the local time when the last frame in a run appears. 
    delete_lost_frames: A boolean which specifies what happens when not all frames for a run are found. If true, they are discarded. If false, they are 
        saved in the unsorted folder
    frame_type: A string identifying the type of file which encodes the frames. Default is "tiff8"
    
    """
    def __init__(self, watchfolder_path, savefolder_path, no_id_folder_path, image_specification_dict, lost_frame_patience = 10.0,
                 breadboard_mismatch_tolerance = 5.0, delete_lost_frames = True, frame_file_type = "tiff8"):
        self.watchfolder_path = watchfolder_path 
        self.savefolder_path = savefolder_path
        self.no_id_folder_path = no_id_folder_path
        self.image_specification_dict = image_specification_dict 
        self.lost_frame_patience = lost_frame_patience 
        self.breadboard_mismatch_tolerance = breadboard_mismatch_tolerance
        self.bc = load_breadboard_client()
        self.total_frames_per_run = 0 
        for key in image_specification_dict:
            self.total_frames_per_run += len(image_specification_dict[key]) 

    
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
            image_full_name = image_name + ";" + timestamp_string
            image_save_path = self.no_id_folder_path + "/" + image_full_name + ".fits" 
            ImageWatchdog._save_as_fits(image_save_path, image_array_stack) 

    """Aggregates a run worth of images from the watchfolder.
    
    Checks the watchfolder to see if there are any frames. If there are, attempts to 
    aggregate them into a run's worth of images, then moves them to the no_id_folder. 
    Discards all frames in the watchfolder if it fails to do so within the time stipulated by 
    lost_frame_patience."""
    def aggregate_run(self, sleep_time = 0.1):
        pass





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
            raise ValueError("Specified image frame type is not supported. Supported options include: " + SUPPORTED_FRAMETYPES_STRING)





    




        