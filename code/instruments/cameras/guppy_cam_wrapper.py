from collections import deque
from camera_interface import Camera



"""
A thin wrapper around vimba's Camera object, designed to respect its intended use 
in a context manager while at the same time allowing one to wrap "implementation detail" 
functionality into a more user-friendly interface.
"""

class GuppyCamWrapper(Camera):

    """
    Initialization method. 

    Parameters:

    cam: The vimba Camera instance used to instantiate the class
    streaming_max_frames: The number of frames stored locally when camera is in streaming mode
    """
    #TODO: Set self.video_running based on cam.is_streaming; should work, but somehow glitches on main PC...
    def __init__(self, cam):
        self.cam = cam
        self._video_running = self.cam.is_streaming()


    def get_frame(self):
        frame = self.cam.get_frame() 
        return frame.as_numpy_ndarray()
        
        
    def start_video(self, buffer_length = 10):
        self._streaming_buffer_deque = deque(maxlen = buffer_length)
        def frame_handler(cam, frame):
            self._streaming_buffer_deque.append(frame)
            cam.queue_frame(frame)
        self.cam.start_streaming(frame_handler)
        self._video_running = True

    def stop_video(self):
        self.cam.stop_streaming()
        self._streaming_buffer_deque.clear()
        self._video_running = False

    def is_video_running(self):
        return self._video_running


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
        return frame.as_numpy_ndarray()
    

    #TODO: try to make this thread-safe!
    def flush_video_buffer(self):
        if not self.is_video_running():
            raise RuntimeError("Video mode is not running.")
        self._streaming_buffer_deque.clear()

    def get_video_buffer_num_available_frames(self):
        if not self.is_video_running():
            raise RuntimeError("Video mode is not running.")
        return len(self._streaming_buffer_deque)

    _supported_writeable_properties = ["ExposureTime", "ExposureAuto", "Width", "Height"]

    _supported_writeable_property_values = {"ExposureTime":(int, "in microseconds"), "AutoExposure":(str, "'On' or 'Off'"), "Width":(int, 'pix'), 
                                  "Height":(int, 'pix')}
    
    _supported_read_only_properties = ["ExposureTimeIncrement", "WidthMax", "HeightMax", "DeviceID"]


    #Wildcard getters which do not obey the standard syntax 
    
    @staticmethod 
    def _exposure_increment_wildcard_getter(cam):
        exposure_time = cam.ExposureTime
        return exposure_time.get_increment()

    _getter_wildcards = {"ExposureTimeIncrement":_exposure_increment_wildcard_getter}

    _setter_wildcards = {}


    def set_property(self, key, value):
        if not key in GuppyCamWrapper._supported_settable_properties:
            if key in GuppyCamWrapper._supported_read_only_properties:
                raise RuntimeError("Property name {0} is read-only.".format(key))
            else:
                raise RuntimeError("Property name {0} is unsupported.".format(key))
        if not key in GuppyCamWrapper._setter_wildcards:
            attribute = getattr(self.cam, key)
            attribute.set(value)
        else:
            setter_method = GuppyCamWrapper._setter_wildcards[key] 
            setter_method(self.cam) 
        

    def get_property(self, key):
        if not (key in GuppyCamWrapper._supported_writeable_properties or key in GuppyCamWrapper._supported_read_only_properties):
            raise ValueError("""Property name {0} is unsupported. A list of property names is available as my_wrapper.writeable_properties and 
                             my_wrapper.read_only_properties.""".format(key))
        if not key in GuppyCamWrapper._getter_wildcards:
            attribute = getattr(self.cam, key)
            attribute_val = attribute.get()
            return attribute_val
        else:
            getter_method = GuppyCamWrapper._getter_wildcards[key] 
            return getter_method(self.cam)



    @property
    def writeable_properties(self):
        return GuppyCamWrapper._supported_writeable_properties
    

    @property 
    def writeable_property_values(self):
        return GuppyCamWrapper._supported__writeable_property_values
    
    @property 
    def read_only_properties(self):
        return GuppyCamWrapper._supported_read_only_properties
    




    #Human-readable functions, retained for convenience and backwards compatibility
    def set_exposure_time(self, exposure_time_us):
        exposure_time = self.cam.ExposureTime
        exposure_time.set(exposure_time_us)


    def get_exposure_time(self):
        exposure_time = self.cam.ExposureTime 
        return exposure_time.get()

    def set_auto_exposure(self, auto_enable):
        exposure_auto = self.cam.ExposureAuto 
        if auto_enable:
            exposure_auto.set("On")
        else:
            exposure_auto.set("Off")


    def set_image_height(self, image_height):
        height = self.cam.Height 
        height.set(image_height)

    def get_image_height(self):
        return self.cam.Height.get() 
    
    def get_image_max_height(self):
        return self.cam.HeightMax.get()

    
    def set_image_width(self, image_width):
        width = self.cam.Width 
        width.set(image_width) 

    def get_image_width(self):
        return self.cam.Width.get() 
    
    def get_image_max_width(self):
        return self.cam.WidthMax.get()

    

