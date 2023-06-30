from abc import ABC, abstractmethod

"""
Abstract class for standardizing calls to cameras."""
class Camera(ABC):


    
    """
    When called, set a property of the camera with name key to a value specified by val. This is the preferred method of changing camera 
    properties from external code. """
    @abstractmethod 
    def set_property(self, key, val):
        pass 

    """
    When called, return a frame from the camera in numpy array format, blocking until the frame is 
    available and optionally raising an error if some timeout is exceeded."""
    @abstractmethod 
    def get_frame(self):
        pass 


    """
    When called, put the camera into ``video mode'' - that is, continuously take frames without 
    external software calls and accumulate them in a local buffer."""
    @abstractmethod 
    def start_video(self):
        pass 

    """
    Exit video mode, as described above."""
    def stop_video(self):
        pass

    """
    Get a frame from the video mode buffer. Calls without kwargs should return the most recent 
    frame, but implementations may allow kwargs to override this behavior."""
    @abstractmethod 
    def get_video_frame(self):
        pass 

    """
    When accessed, provides a read-only list of available property names which could be passed as keys 
    to the set_property method."""
    @property 
    @abstractmethod 
    def available_properties(self):
        pass 



    """
    When accessed, provides a read-only dict {key:value_type} whose keys are the property names from available_properties 
    and whose values are user-readable identifiers of the legitimate values to be passed to that property. 
    Python types should be preferred where possible - e.g. bool, int - but this is not mandatory."""
    @property 
    @abstractmethod 
    def available_property_values(self):
        pass



