# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 11:34:46 2024

@author: jaris
"""

from QuickBasler import rgb_converter,connect_cam, get_img, pylon
import matplotlib.pyplot as plt
from TLBSC203 import BSC203

# stage = BSC203(serialNo='',MAX_POSMM=10)
camera = connect_cam()

while True:
    plt.cla()
    plt.imshow(get_img(camera))
    plt.pause(0.01)

# %timeit get_img(camera,False)
# %timeit get_img(camera,True)