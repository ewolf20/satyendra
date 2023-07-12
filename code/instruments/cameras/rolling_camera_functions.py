import datetime
from math import inf 
import os
import time 

from astropy.io import fits
import numpy as np
"""
Given a camera in video mode, acquire a logical grouping of frames.

In many experiments, it is necessary to logically group together a series of 
images which are acquired by a camera which is "rolling" and triggered at arbitrary 
times, potentially unknown by software. It is likewise necessary to gracefully handle missed 
triggers, avoiding situations where the logical grouping of shots becomes "shifted by one". 

This function addresses this problem. Given a camera cam which is in video mode, it scans for a set of 
frames of length num_frames, returning a tuple (frame_1, frame_2, ... frame_n) if all frames are found, 
and None otherwise. 

REMARK: This function is in general blocking while waiting for frame input, and is not suitable for cases where 
other code is to be executed in the same loop. For these cases, see acquire_rolling_frame_sequence_nonblocking. 
It is likewise not applicable to cases where the time spacing between the first and last frame in a logical sequence 
is smaller than the time spacing between the last frame in one logical sequence and the first frame in the next. 


Parameters:

cam: The camera object. It is assumed that the camera has been initialized as necessary for acquiring the logical 
grouping of frames, including being put into video mode with an appropriate buffer
and configuring the trigger as necessary.

num_frames: (int) The number of frames to be acquired. If at any point the camera has _more_ than this number of frames available in its 
video buffer, it is assumed that something has gone wrong, and the buffer is flushed.

frame_timeout: (float) The timeout for "abandoning" acquisition of a sequence of frames. If the camera has a number 
of frames greater than 0 but less than num_frames, the function will block for a time given by frame_timeout while 
waiting for the correct number of frmaes to come in. If they do not come in, the function flushes the camera buffer, 
assuming that a frame has been missed. This timeout should be set longer than the time between the first frame in the sequence 
and the last, but shorter than the time between the last frame in one logical sequence and the first frame in the next.

Returns:

frames: A tuple of the acquired frames, in the order of acquisition, or else None if the frames were not found. 
"""
def acquire_rolling_frame_sequence(cam, num_frames, frame_timeout):
    frames_available = cam.get_video_buffer_available_frames()
    if frames_available == 0:
        return None
    else:
        sequence_start_time = time.time() 
        sequence_run_time = 0.0
        while sequence_run_time <= frame_timeout:
            if frames_available == num_frames:
                frame_list = [] 
                for i in range(num_frames):
                    frame_list.append(cam.get_video_frame())
                return tuple(frame_list)
            elif frames_available > num_frames:
                cam.flush_video_buffer()
                return None 
            sequence_run_time = time.time() - sequence_start_time
        return None


"""
Acquires frames analogously to the above, but in a (more complicated) non-blocking implementation.

Parameters:

t: A float representing the time that the function began waiting for frames. When the function 
is first called, this should be passed via a time.time() call - subsequently, it should be the value 
returned by this function.

cam: Identical to acquire_rolling_frame_sequence, above. 

num_frames: Ditto. 

frame_timeout: Ditto.

Returns: A tuple (t, frames), where t is a time when the camera began waiting for frames and frames 
is the tuple of frames - or None - as described above. Note that t will be equal to inf if the camera 
is _not_ waiting for frames."""


def acquire_rolling_frame_sequence_nonblocking(t, cam, num_frames, frame_timeout):
    frames_available = cam.get_video_buffer_available_frames()
    if frames_available == 0 or frames_available > num_frames:
        frames = None 
        t = inf 
        cam.flush_video_buffer()
        return (t, frames)
    elif frames_available == num_frames:
        frames_list = [] 
        for i in range(num_frames):
            frames_list.append(cam.get_video_frame())
        frames = tuple(frames_list)
        t = inf 
        return (t, frames)
    else:
        frames = None
        current_time = time.time()
        if current_time - t > frame_timeout:
            t = inf 
            cam.flush_video_buffer()
        return (t, frames)


"""
Regroup a series of numpy-formatted frames. 

Given a list of frames - either 2D or 3D numpy arrays, depending on whether there are 
multiple exposures per frame - regroup them according to the indices in exposure_indices.

Parameters:

frames_list: An iterable of frames from a camera. Frames are assumed to be in numpy array format, 
being 2D numpy arrays if there is only one exposure per frame, and 3D arrays otherwise.

exposure_indices_list: An iterable of iterables, each of them a set of indices to group into one logical 
grouping of frames. If, for example, frames is of length 3, with each frame containing 2 exposures, then 
setting exposure_indices_list to [[1, 3, 5], [2, 4, 6]] would group the odd- and even-numbered exposures together, 
where the exposure index is incremented first within a frame, then between frames.
"""
def regroup_numpy_frames(frames, exposure_indices_list):
    first_frame = frames[0]
    if len(first_frame.shape) == 2:
        exposures = frames
    elif len(first_frame.shape) == 3:
        exposures = [] 
        for frame in frames:
            for exposure in frame:
                exposures.append(exposure)
    else:
        raise ValueError("Incorrect shape for frames.") 
    exposure_array = np.array(exposures)
    return_tuple_list = []
    for exposure_indices in exposure_indices_list:
        exposure_indices = np.array(exposure_indices)
        regrouped_exposures = exposure_array[exposure_indices] 
        regrouped_exposures_tuple = tuple(regrouped_exposures)
        return_tuple_list.append(regrouped_exposures_tuple)
    return tuple(return_tuple_list)


"""
Save frames to disk. 

Given a tuple of frames as provided by the functions above, save the data to disk at a specified path and 
in a specified format.

Parameters:

frames: A tuple of frames in numpy array format. 
path_sans_extension: A path at which to save the data.
"""
def save_frames(frames, save_path):
    frame_numpy_stack = np.stack(frames)
    save_format = save_path.split(".")[-1] 
    if save_format == "fits":
        hdu = fits.PrimaryHDU(frame_numpy_stack)
        hdu.writeto(save_path)
    else:
        raise ValueError("Unsupported saving format.")

