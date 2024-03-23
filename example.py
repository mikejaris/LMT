# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 23:40:51 2024

@author: jaris
"""

import LMTpy as lp
import numpy as np
from IPython import get_ipython
var_dict = get_ipython().__dict__['user_module'].__dict__

inst = lp.Instruments() if not 'inst' in var_dict.keys() else var_dict['inst']
inst.daq.VOLT_RANGE=5

exp = lp.Experiment(inst=inst,FILEPATH=r'C:\users\jaris\Documents\MercuryTesting')

# =============================================================================
# scan motor over range of position
# =============================================================================
degrees=np.arange(4,-4,-.25)
folder_name='Experiment 1'
exp.motor_scan(DEGREES=degrees,FOLDER_NAME=folder_name)


# =============================================================================
# take a measurement at a fixed position for a set duration
# =============================================================================
duration=10#seconds
data = exp.timed_measurement(duration=10)
