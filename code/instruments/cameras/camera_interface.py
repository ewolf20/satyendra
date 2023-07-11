from abc import ABC, abstractmethod

"""
Abstract class for standardizing calls to cameras."""
class Camera(ABC):

    """
    Cameras should support context management, but should function normally when not called in a 
    context manager (i.e. not rely on __enter__ for setup) """
    @abstractmethod 
    def __enter__(self):
        pass 


    @abstractmethod 
    def __exit__(self, exc_type, exc_val, exc_trace):
        pass

    """
    When called, gracefully close the connection to the camera hardware."""
    @abstractmethod 
    def close(self):
        pass 

    """
    When called, set a property of the camera with name key to a value specified by val. Subclasses are free to implement separate 
    getters and setters for particularly relevant properties, but these must obey the convention that set_property_x(val) is equivalent 
    to set_property("property_x", val). """
    @abstractmethod 
    def set_property(self, key, val):
        pass 


    """
    When called, get the value of a property supported by set_property."""
    def get_property(self, key):
        pass



    """
    When accessed, provides a read-only list of available property names which could be passed as keys 
    to the set_property method."""
    @property 
    @abstractmethod 
    def writeable_properties(self):
        pass 



    """
    When accessed, provides a read-only dict {key:value_type} whose keys are the property names from available_properties 
    and whose values are user-readable identifiers of the legitimate values to be passed to that property. 
    Preferred syntax is a tuple (type, comment_str) of a python type and a short comment string, but this is not enforced."""
    @property 
    @abstractmethod 
    def writeable_property_values(self):
        pass


    """
    When accessed, provides a list of read-only property keys - that is, keys which could be passed to get_property, but 
    not to set_property, and which will typically represent immutable hardware-specific parameters, e.g. CCD array dimensions."""

    @property 
    @abstractmethod 
    def read_only_properties(self):
        pass



    """
    When called, return a frame from the camera in ndarray format, blocking until the frame is 
    available and optionally supporting a "timeout" parameter, after which None is returned. 
    
    Implementers have freedom to decide the return datatype; for monochrome cameras, an ndarray is preferred. 
    
    Occasionally, camera implementation details will dictate that a single "frame" - i.e. download from the camera - 
    contains multiple 2D detector exposures. This is e.g. often the case for fast kinetics imaging. In this case, the 
    return ndarray must be a 3D ndarray, with the first index indexing different exposures."""
    @abstractmethod 
    def get_frame(self):
        pass 


    """
    When called, put the camera into ``video mode'' - that is, continuously take frames without 
    external software calls and accumulate them in a local buffer. Implementations may decide the 
    outcome of calling this while video is already running."""
    @abstractmethod 
    def start_video(self):
        pass 

    """
    Exit video mode, as described above."""
    @abstractmethod
    def stop_video(self):
        pass

    """
    Indicates whether video mode is running. """
    @abstractmethod
    def is_video_running(self):
        pass


    """
    Flushes the video mode buffer."""
    @abstractmethod 
    def flush_video_buffer(self):
        pass

    """
    Returns the number of frames in the video buffer."""
    @abstractmethod 
    def get_video_buffer_num_available_frames():
        pass


    """
    Get a frame from the video mode buffer. Calls without kwargs should return the oldest 
    frame, popped from the buffer, but implementations may allow kwargs to override this behavior. When called with an empty buffer, 
    should return None."""
    @abstractmethod 
    def get_video_frame(self):
        pass 


