# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 23:40:51 2024

@author: jaris
"""

import LMTpy as lp
import numpy as np
import matplotlib.pyplot as plt
from IPython import get_ipython
var_dict = get_ipython().__dict__['user_module'].__dict__
import pickle

# =============================================================================
# load the instruments separately, inherits "inst" from kernel if it exists
# note that if inst.close_all() was called then inst.connect_all() must be called to re-establish comms
# =============================================================================
inst = lp.Instruments() if not 'inst' in var_dict.keys() else var_dict['inst']
#inst.motor.set_velocity_params(max_velocity=1,accel=1) #Motor 

exp = lp.Experiment(inst=inst,FILEPATH=r'C:\users\SinglePixelCamera\Documents\LMT_Test')

if not exp.motor.status.IsHomed:
    print("Warning: motor is not homed, position may not be accurate")
    
# =============================================================================
# move stage position and take timed measurements
# =============================================================================
exp.jog_motor_timed(STEP_SIZE=0.5,DURATION=5,IMG_DELAY=0.5,FOLDER_NAME='Test')


# =============================================================================
# take a timed measurement at a single location and return data as dictionary
# note that all of the arguments passed into timed_measurement can also be passed into jog_motor_timed and scan_motor_timed
# =============================================================================
data = exp.timed_measurement(DURATION=20,IMG_DELAY=0.5,START_DELAY=5,SHOW_IMGS=True)


# =============================================================================
# load a pickle file
# =============================================================================
fname = 'some_file.pickle'
with open(fname,'rb') as f:
    data = pickle.load(f)