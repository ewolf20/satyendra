from collections import deque

import numpy as np
from vimba import Vimba, PixelFormat


from . import camera_interface
from satyendra.code import loading_functions



"""
A thin wrapper around vimba's Camera object, designed to respect its intended use 
in a context manager while at the same time allowing one to wrap "implementation detail" 
functionality into a more user-friendly interface.
"""

class GuppyCamera(camera_interface.Camera):

    """
    Initialization method. 

    Parameters:

    cam_id: (str) The id of the camera, as provided by vimba. Running the static method get_available_camera_ids returns a list of available ids.
    """
    def __init__(self, cam_id):
        self.cam_id = cam_id
        self._load_camera()


    def _load_camera(self):
        #Dark magic to handle the guppy camera's weird context management requirements...
        def camera_generator_func():
            with Vimba.get_instance() as vimba:
                cams = vimba.get_all_cameras()
                matching_id_cams = [cam for cam in cams if cam.get_id() == self.cam_id]
                with matching_id_cams[0] as cam:
                    yield cam
        self._cam_generator = camera_generator_func()
        self.cam = next(self._cam_generator)

    def __enter__(self):
        return self 
    
    def __exit__(self, exc_type, exc_val, exc_trace):
        self.close()


    def close(self):
        if self.is_video_running():
            self.stop_video() 
        self._cam_generator.close()

    def get_frame(self, timeout_ms = 2000):
        frame = self.cam.get_frame(timeout_ms = timeout_ms) 
        frame_array = frame.as_numpy_ndarray()
        #Squeeze out length-1 color channels for monochrome cameras...
        squeezed_frame_array = np.squeeze(frame_array)
        return frame.as_numpy_ndarray()
        
        
    def start_video(self, buffer_length = 10):
        self._streaming_buffer_deque = deque(maxlen = buffer_length)
        def frame_handler(cam, frame):
            self._streaming_buffer_deque.append(frame)
            cam.queue_frame(frame)
        self.cam.start_streaming(frame_handler)

    def stop_video(self):
        self.cam.stop_streaming()
        self._streaming_buffer_deque.clear()

    def is_video_running(self):
        return self.cam.is_streaming()


    def get_video_frame(self, recency = "oldest"):
        try:
            if recency == "oldest":
                frame = self._streaming_buffer_deque.popleft() 
            elif recency == "newest":
                frame = self._streaming_buffer_deque.pop() 
            else:
                raise ValueError("Recency flag not recognized") 
        except IndexError:
            return None
        frame_array = frame.as_numpy_ndarray()
        squeezed_frame_array = np.squeeze(frame_array)
        return squeezed_frame_array
    

    #TODO: try to make this thread-safe!
    def flush_video_buffer(self):
        if not self.is_video_running():
            raise RuntimeError("Video mode is not running.")
        self._streaming_buffer_deque.clear()

    def get_video_buffer_num_available_frames(self):
        if not self.is_video_running():
            raise RuntimeError("Video mode is not running.")
        return len(self._streaming_buffer_deque)

    _supported_writeable_properties = ["DeviceLinkThroughputLimit", "ExposureTime", "ExposureAuto", "Height", "Gain", "GainAuto", "GainRaw", "PixelFormat",
                                    "TriggerActivation", "TriggerDelay",
                                       "TriggerMode", "TriggerSelector", "TriggerSource", "Width"]

    _supported_writeable_property_values = {"DeviceLinkThroughputLimit":(int, "bytes per second"), "ExposureTime":(int, "in microseconds"), "ExposureAuto":(str, "'On' or 'Off'"),
                                             "Gain":(float, "in dB, increment 0.1"), "GainAuto":(str, "'On' or 'Off'"), "GainRaw":(int, "8 to 48, increment 1"), "Height":(int, 'pix'), 
                                            "PixelFormat":(str, "'Mono8', 'Mono12' etc. for monochrome cameras"),
                                            "TriggerActivation":(str, "'RisingEdge' or 'FallingEdge'"), "TriggerDelay":(float, "Exposure start delay after trigger, us"), 
                                            "TriggerMode":(str, "'On' or 'Off'"), "TriggerSelector":(str, "'ExposureStart' or other value"), 
                                            "TriggerSource":(str, "'InputLines' or other value"), "Width":(int, 'pix')}
    
    _supported_read_only_properties = ["BinningHorizontal", "BinningVertical", "ExposureTimeIncrement", "WidthMax", "HeightMax", "DeviceID"]


    #Wildcard getters which do not obey the standard syntax 
    
    @staticmethod 
    def _exposure_increment_wildcard_getter(cam):
        exposure_time = cam.ExposureTime
        return exposure_time.get_increment()

    @staticmethod 
    def _pixel_format_wildcard_getter(cam):
        return str(cam.get_pixel_format())


    _getter_wildcards = {"ExposureTimeIncrement":_exposure_increment_wildcard_getter, "PixelFormat":_pixel_format_wildcard_getter}

    #Wildcard setters which do not obey the standard syntax

    @staticmethod 
    def _pixel_format_wildcard_setter(cam, value):
        cam.set_pixel_format(getattr(PixelFormat, value))




    _setter_wildcards = {"PixelFormat":_pixel_format_wildcard_setter}


    def set_property(self, key, value):
        if not key in GuppyCamera._supported_writeable_properties:
            if key in GuppyCamera._supported_read_only_properties:
                raise RuntimeError("Property name {0} is read-only.".format(key))
            else:
                raise RuntimeError("Property name {0} is unsupported.".format(key))
        if not key in GuppyCamera._setter_wildcards:
            attribute = getattr(self.cam, key)
            attribute.set(value)
        else:
            setter_method = GuppyCamera._setter_wildcards[key] 
            setter_method(self.cam, value) 
        

    def get_property(self, key):
        if not (key in GuppyCamera._supported_writeable_properties or key in GuppyCamera._supported_read_only_properties):
            raise ValueError("""Property name {0} is unsupported. A list of property names is available as my_wrapper.writeable_properties and 
                             my_wrapper.read_only_properties.""".format(key))
        if not key in GuppyCamera._getter_wildcards:
            attribute = getattr(self.cam, key)
            attribute_val = attribute.get()
            return attribute_val
        else:
            getter_method = GuppyCamera._getter_wildcards[key] 
            return getter_method(self.cam)



    @property
    def writeable_properties(self):
        return GuppyCamera._supported_writeable_properties
    

    @property 
    def writeable_property_values(self):
        return GuppyCamera._supported__writeable_property_values
    
    @property 
    def read_only_properties(self):
        return GuppyCamera._supported_read_only_properties
    
    
    #Convenience method for getting available camera ids...
    @staticmethod 
    def get_available_camera_ids():
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras() 
            ids_list = [cam.get_id() for cam in cams] 
            return ids_list