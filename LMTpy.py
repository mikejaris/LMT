import QuickBasler as qb
from MC_DAQ import MCC_DAQ
import numpy as np
import os
import matplotlib.pyplot as plt
import time
from BSC201 import BSC201
from datetime import datetime
class Instruments:
    def __init__(self,**kwargs):
        try:
            self.motor = BSC201()
            self.camera = qb.connect_cam()
            self.daq = MCC_DAQ()
        except:
            pass


class Experiment(Instruments):
    def __init__(self,**kwargs):
        for k,v in kwargs.items(): setattr(self,k,v)

        if not hasattr(self,'inst'): 
            self.inst=Instruments()
        if not hasattr(self,'FILEPATH'): setattr(self,'FILEPATH',os.path.join(os.getcwd(),datetime.now().strftime('%d%m%y')))

    @staticmethod
    def deg_to_pos(deg):
        val= round(-2.16639e-4*deg**3 - 9.88884e-3*deg**2 -2.39362*deg +28.1949,3)
        return val

    @staticmethod
    def pos_to_deg(pos):
        val = round(-8.73407e-4*pos**2 - 3.71107e-1*pos+11.1412,3) #polynomial fit of stage angle vs motor position (R-squared>0.999)
        return val

    def save_img(self, filename):
        img=qb.get_img(self.camera) #200 ms?
        plt.imsave(filename,img)
        return img
    
    def timed_measurement(self,DURATION=10,DELAY=5,IMG_DELAY=0.5,**kwargs):
        for k,v in kwargs.items(): setattr(self,k,v)
        num_imgs = int(DURATION//IMG_DELAY)
        imgs=np.zeros((num_imgs,2160,3840,4),dtype=np.uint8)
        
        dt = DELAY/10
        for i in range(10):
            print('\r','Starting measurement in %0.1f seconds' %(DELAY-i*dt),end='')
            time.sleep(dt)
        
        v=[self.daq.voltage()]
        t=[time.time()]
        imgs[0]=qb.get_img(self.camera)
        img_time=t[0]
        
        cnt=1
        while time.time()-[0]<DURATION and cnt<num_imgs:
            t.append(time.time())
            v.append(self.daq.voltage())
            
            if t[-1]-img_time>IMG_DELAY:
                imgs[cnt]=qb.get_img(self.cam)
                cnt+=1
                img_time=t[-1]
        data={'time':t,'voltage':v,'imgs':imgs}
        return data
                
            
    def motor_scan(self,DEGREES,IMG_DELAY=0.5,SHOW_LAST_IMG=True,VOLT_THRESH=0.005,
        PAUSE=True,TAKE_IMGS=True, NUM_VOLT_AVG=30,FOLDER_NAME=None,**kwargs):
        for k,v in kwargs.items(): setattr(self,k,v)

        if not os.path.exists(self.FILEPATH): os.mkdir(self.FILEPATH)
        filename = lambda fpath, timestamp: os.path.join(fpath,'Time elapsed - %0.1f seconds.tiff'%timestamp)
        if FOLDER_NAME is None: FOLDER_NAME = datetime.now().strftime('%y%m%d-%H%M%S')
        folder_path=os.path.join(self.FILEPATH,FOLDER_NAME)
        if not os.path.exists(folder_path): os.mkdir(folder_path)

        if SHOW_LAST_IMG: plt.figure()

        for deg in DEGREES:
            savepath = os.path.join(folder_path,'Stage angle %0.2f degrees'%deg)
            if os.path.exists(savepath) and len(os.listdir(savepath))>0: raise FileExistsError('Duplicate savepath was detected in %s, please change dirpath to prevent overwriting data')
            if not os.path.exists(savepath): os.mkdir(savepath)
            
            pos=self.deg_to_pos(deg)
            self.motor.move(pos)

            v = [self.daq.voltage() for i in range(NUM_VOLT_AVG)]
            t=[time.time()]*NUM_VOLT_AVG
            while np.mean(v) < VOLT_THRESH:
                print('\r','Motor is in position, system is ready to take data when button press is detected (current reading = %0.2f'%np.mean(v), end='')
                v.append(self.daq.voltage())
                v.pop(0)
                t.append(time.time())
                t.pop(0)
            print('\n\n')
            
            img_time=t[0]
            self.save_img(filename(savepath,time.time()-t[0]))
            while True:
                print('\r','Button press detected, recording data (time elapsed = %0.1f seconds)'%(time.time()-t[0]),end='')

                t.append(time.time())
                v.append(self.daq.voltage())
                
                if TAKE_IMGS and (t[-1]-t[0]-img_time)>IMG_DELAY:
                    img_fn = filename(savepath,t[-1]-t[0])
                    img=self.save_img(img_fn)
                    img_time=t[-1]
                
                if len(v)>NUM_VOLT_AVG and np.mean(v[-NUM_VOLT_AVG:]) < VOLT_THRESH: 
                    break
            
            np.save(os.path.join(savepath,'voltages'),np.vstack((t,v)))
            print('Button release detected, system has stopped recording data. %i images/data points were recorded'%len(v))

            if SHOW_LAST_IMG:
                plt.cla()
                plt.imshow(img)
                plt.title(f'Angle = {deg} degrees',fontsize=20)
                plt.pause(0.01)
                
            if PAUSE:
                input("\n\nPress any key to advance to next position")