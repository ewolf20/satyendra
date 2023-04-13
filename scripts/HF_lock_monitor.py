# Huan Q Bui, BEC1@MIT
# Last updated: April 05, 2023
import numpy as np
import sys 
import matplotlib.pyplot as plt
import time
from scipy.signal import find_peaks
import ctypes
import pyttsx3 

PATH_TO_REPOSITORIES_FOLDER = "C:/Users/BEC1Top/Repositories"
sys.path.insert(0, PATH_TO_REPOSITORIES_FOLDER)

from satyendra.code import slack_bot
from satyendra.code.ps2000_wrapper_blockmode_utils import Picoscope