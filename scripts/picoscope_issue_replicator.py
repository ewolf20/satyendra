# Huan Q Bui, BEC1@MIT
# Last updated: 08:01 pm, Mar 30, 2023


import numpy as np
import sys 
import matplotlib.pyplot as plt
import time
from scipy.signal import find_peaks
import ctypes
import pyttsx3 


PATH_TO_REPOSITORIES_FOLDER = "C:/Users/BEC1 Top/Repositories"
sys.path.insert(0, PATH_TO_REPOSITORIES_FOLDER)

from satyendra.code import slack_bot
from satyendra.code.ps2000_wrapper_blockmode_utils import Picoscope
from picoscope_lock_monitor import initialize_scope, get_scope_traces 

LOCK_BLOCK_SIZE = 1000 
LOCK_BLOCK_DURATION = 0.005
LOCK_PRE_TRIGGER_PERCENT = 0

#Li scope config params
LI_SCOPE_DEFAULT_TRIGGER_LEVEL_MV = 2000

LI_SCOPE_ID = 0
LI_SCOPE_SERIAL = "J0247/1191" 
LI_SCOPE_CHANNEL_A_RANGE_MV = 10000
LI_SCOPE_CHANNEL_B_RANGE_MV = 5000
LI_SCOPE_TRIGGER_DIRECTION = 0
LI_SCOPE_TRIGGER_CHANNEL = "A"

LI_SCOPE_FIXED_PARAMS = [LI_SCOPE_ID, LI_SCOPE_SERIAL, LI_SCOPE_CHANNEL_A_RANGE_MV, 
                   LI_SCOPE_CHANNEL_B_RANGE_MV, 
                   LOCK_PRE_TRIGGER_PERCENT, LOCK_BLOCK_SIZE, LOCK_BLOCK_DURATION]

LI_SCOPE_TRIGGER_FIXED_PARAMS = [LI_SCOPE_TRIGGER_DIRECTION, LI_SCOPE_TRIGGER_CHANNEL]



def main():
    li_scope_trigger_level = 0 
    li_scope_trigger_params = [li_scope_trigger_level, *LI_SCOPE_TRIGGER_FIXED_PARAMS]
    li_picoscope = initialize_scope(*LI_SCOPE_FIXED_PARAMS, trigger_params = li_scope_trigger_params)
    print("Getting traces")
    traces = get_scope_traces(li_picoscope)
    print("Got traces")


if __name__ == "__main__":
    main()