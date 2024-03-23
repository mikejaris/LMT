# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 17:48:13 2024

@author: jaris
"""
import QuickBasler as qb
from MC_DAQ import MCC_DAQ
import numpy as np
import os
import matplotlib.pyplot as plt
import time
from IPython import get_ipython
var_dict = get_ipython().__dict__['user_module'].__dict__
if 'BSC201' in var_dict.keys(): #stupid issue reloading pythonnet, will fix...
    BSC201 = var_dict['BSC201']
else:
    from BSC201 import BSC201
    
# =============================================================================
# Scan parameters
# =============================================================================
DIRPATH = r'C:\Users\jaris\Documents\Mercury Images New'
degrees = np.linspace(-10,10,81)
degrees = [-1.5,1.5]
PAUSE = True # pause scan between positions until user input detected
VOLT_THRESH = 0.005 #10 mV threshold for detecting button press event
SHOW_LAST_IMG = True
IMG_DELAY = 0.5 #only takes images every 0.5 seconds


pos_to_deg = lambda pos: -8.73407e-4*pos**2 - 3.71107e-1*pos+11.1412 #polynomial fit of stage angle vs motor position (R-squared>0.999)
deg_to_pos = lambda deg: round(-2.16639e-4*deg**3 - 9.88884e-3*deg**2 -2.39362*deg +28.1949,3)

if not os.path.exists(DIRPATH): os.mkdir(DIRPATH)
filename = lambda fpath, timestamp: os.path.join(fpath,'Time elapsed - %0.1f seconds.tiff'%timestamp)

# =============================================================================
# Setup devices
# =============================================================================
mot = BSC201(DeviceType='DRV250')
# mot.home()
cam = qb.connect_cam()
daq=MCC_DAQ(CHANNELS=[0],VOLT_RANGE=1)

# =============================================================================
# Scan stage through positions and wait for user to apply voltage at each step
# Power supply voltage/current and sample image will be saved continously while the button is pressed
# =============================================================================
if SHOW_LAST_IMG: plt.figure()
for deg in degrees:
    savepath = os.path.join(DIRPATH,'Stage angle %0.2f degrees'%deg)
    if os.path.exists(savepath) and len(os.listdir(savepath))>0: raise FileExistsError('Duplicate savepath was detected in %s, please change dirpath to prevent overwriting data')
    if not os.path.exists(savepath): os.mkdir(savepath)
    
    mot.move(deg_to_pos(deg))

    v = daq.voltage()
    while v < VOLT_THRESH:
        print('\r','Motor is in position, system is ready to take data when button press is detected (current reading = %0.2f'%v, end='')
        v=daq.voltage()
    print('\n')
    
    t=[time.time()]
    v=[v]
    take_img = True
    while True:
        print('\r','Button press detected, recording data (time elapsed = %i seconds)'%(time.time()-t[0]),end='')
        if take_img:
           img=qb.get_img(cam) #200 ms?
           img_fn = filename(savepath,time.time()-t[0])
           plt.imsave(img_fn,img)
           take_img = False
        t.append(time.time())
        v.append(daq.voltage())
        if len(v)>10 and np.mean(v[-10:]) < VOLT_THRESH: break
        if t[-1]-t[0]-float(img_fn.split('d - ')[1].split('s')[0]) > IMG_DELAY: take_img=True
    
    np.save(os.path.join(savepath,'voltages'),np.vstack((t,v)))
    print('Button release detected, system has stopped recording data. %i images/data points were recorded'%len(v))

    if SHOW_LAST_IMG:
        plt.cla()
        plt.imshow(img)
        plt.title(f'Angle = {deg} degrees',fontsize=20)
        plt.pause(0.01)
        
    if PAUSE:
        input("Press any key to advance to next position")