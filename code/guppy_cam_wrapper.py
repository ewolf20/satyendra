from collections import deque



"""
A thin wrapper around vimba's Camera object, designed to respect its intended use 
in a context manager while at the same time allowing one to wrap "implementation detail" 
functionality into a more user-friendly interface.
"""

class GuppyCamWrapper:

    """
    Initialization method. 

    Parameters:

    cam: The vimba Camera instance used to instantiate the class
    streaming_max_frames: The number of frames stored locally when camera is in streaming mode
    """
    def __init__(self, cam, streaming_max_frames = 1):
        self.cam = cam
        self.streaming_buffer_deque = deque(maxlen = streaming_max_frames)


    def get_single_frame(self):
        frame = cam.get_frame() 
        return frame.as_numpy_ndarray()


    def set_exposure_time(self, exposure_time):
        pass
        
        
    def start_streaming(self):
        def frame_handler(cam, frame):
            self.streaming_buffer_deque.append(frame)
            cam.queue_frame(frame) 
        self.cam.start_streaming(frame_handler)


    def get_streamed_frame(self, recency = "oldest"):
        try:
            if recency == "oldest":
                frame = self.streaming_buffer_deque.popleft() 
            elif recency == "newest":
                frame = self.streaming_buffer_deque.pop() 
            else:
                raise ValueError("Recency flag not recognized") 
        except IndexError:
            return None
        return frame.as_numpy_ndarray()


    def stop_streaming(self):
        self.cam.stop_streaming()


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