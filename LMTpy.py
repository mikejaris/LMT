import QuickBasler as qb
from MC_DAQ import MCC_DAQ
import numpy as np
import os
import matplotlib.pyplot as plt
import time
from BSC201 import BSC201
from datetime import datetime
import pickle

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
        for k,v in vars(self.inst).items():
            setattr(self,k,getattr(self.inst,k))
            
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

    def init_savepath(self,FOLDER_NAME=None):
        if not os.path.exists(self.FILEPATH): os.mkdir(self.FILEPATH)
        if FOLDER_NAME is None: FOLDER_NAME = datetime.now().strftime('%y%m%d-%H%M%S')
        folder_path=os.path.join(self.FILEPATH,FOLDER_NAME)
        if not os.path.exists(folder_path): os.mkdir(folder_path)
        return folder_path
    
    def timed_measurement(self,DURATION=10,START_DELAY=5,IMG_DELAY=0.5,SHOW_IMGS=True,**kwargs):
        for k,v in kwargs.items(): setattr(self,k,v)
        num_imgs = int(DURATION//IMG_DELAY)
        imgs=np.zeros((num_imgs,2160,3840,3),dtype=np.uint8)
        
        if hasattr(self,'fignum') and SHOW_IMGS: fig=plt.figure(self.fignum)
        elif SHOW_IMGS: plt.figure()

        dt = START_DELAY/10
        for i in range(10):
            print('\r','Starting measurement in %0.1f seconds' %(START_DELAY-i*dt),end='')
            time.sleep(dt)
        
        v=[self.daq.voltage()]
        t=[time.time()]
        imgs[0]=qb.get_img(self.camera)
        img_time=t[0]
        
        cnt=1
        while time.time()-t[0]<DURATION and cnt<num_imgs:
            t.append(time.time())
            v.append(self.daq.voltage())
            
            if t[-1]-img_time>IMG_DELAY:
                img = qb.get_img(self.camera)
                imgs[cnt]=img
                cnt+=1
                img_time=t[-1]
                if SHOW_IMGS:
                    plt.cla()
                    plt.imshow(img)
                    plt.pause(0.01)

        data={'time':t,'voltage':v,'imgs':imgs}
        return data

    def motor_scan_timed(self,DEGREES,DURATION=10,START_DELAY=5,IMG_DELAY=0.5, 
                        FOLDER_NAME=None,SHOW_IMGS=True, PAUSE_BETWEEN=False, **kwargs):
        for k,v in kwargs.items(): setattr(self,k,v)

        folder_path = self.init_savepath(FOLDER_NAME)

        if SHOW_IMGS:
            fig = plt.figure()
            self.fignum = fig.number

        for deg in DEGREES:
            savepath = os.path.join(folder_path,'Stage angle %0.2f degrees'%deg)
            if os.path.exists(savepath) and len(os.listdir(savepath))>0: raise FileExistsError('Duplicate savepath was detected in %s, please change dirpath to prevent overwriting data')
            if not os.path.exists(savepath): os.mkdir(savepath)

            pos=self.deg_to_pos(deg)
            self.motor.move(pos)

            print('\n Stage angle at %0.2f degrees, prepare to press button to measure for %0.1f seconds (PAUSE_BEWEEN is %s)'%(deg,DURATION,PAUSE_BETWEEN))
            if PAUSE_BETWEEN: input('\n Press any button to begin timed measurement (START_DELAY is %0.1f seconds)'%START_DELAY)

            data = self.timed_measurement(DURATION,START_DELAY,IMG_DELAY,SHOW_IMGS)
            with open(os.path.join(savepath,'Stage angle %0.2f degrees.pickle'),'wb') as f:
                pickle.dump(data,f)


    def jog_motor_timed(self,STEP_SIZE=0.5,DURATION=10,START_DELAY=5,IMG_DELAY=0.5,
                        FOLDER_NAME=None,SHOW_IMGS=True,PAUSE_BETWEEN=False,**kwargs):
        for k,v in kwargs.items(): setattr(self,k,v)

        folder_path = self.init_savepath(FOLDER_NAME)

        if SHOW_IMGS:
            fig = plt.figure()
            self.fignum = fig.number

        print('\n Entering measurement loop, press ctrl+c to end')

        # try:
        while True:
            value = input('\n Press 1 to increase angle, 2 to decrease angle, 3 to take measurement at same position, or 4 to change STEP_SIZE')
            if value not in ['1','2','3','4']: continue

            current_angle = self.pos_to_deg(self.motor.position)
            if value == '1':
                current_angle+=STEP_SIZE
                next_pos = self.deg_to_pos(current_angle)
                self.motor.move(next_pos)

            elif value == '2':
                current_angle-=STEP_SIZE
                next_pos=self.deg_to_pos(current_angle)
                self.motor.move(next_pos)

            elif value == '4':
                STEP_SIZE = float(input('Enter new STEP_SIZE value (current value is %0.2f degrees)'%STEP_SIZE))
                continue


            data = self.timed_measurement(DURATION,START_DELAY,IMG_DELAY,SHOW_IMGS)
            with open(os.path.join(folder_path,'Stage angle %0.2f degrees (%s).pickle'%(current_angle,datetime.now().strftime('%y%m%d-%H%M%S'))),'wb') as f:
                pickle.dump(data,f)

        # except:
        #     pass


    def motor_scan_on_button_press(self,DEGREES,IMG_DELAY=0.5,SHOW_IMGS=True,VOLT_THRESH=0.005,
        PAUSE=True,TAKE_IMGS=True, NUM_VOLT_AVG=30,FOLDER_NAME=None,BUTTON_CHAN=0,**kwargs):
        for k,v in kwargs.items(): setattr(self,k,v)

        folder_path = self.init_savepath(FOLDER_NAME)

        filename = lambda fpath, timestamp: os.path.join(fpath,'Time elapsed - %0.1f seconds.tiff'%timestamp)

        if SHOW_IMGS: plt.figure()

            
        NOT_BUTTON_CHANS = self.daq.CHANNELS.copy()
        NOT_BUTTON_CHANS.pop(NOT_BUTTON_CHANS.index(BUTTON_CHAN))
        other_daq_channels = lambda: [self.daq.voltage(CHANNEL=CHAN) for CHAN in NOT_BUTTON_CHANS]


        for deg in DEGREES:
            savepath = os.path.join(folder_path,'Stage angle %0.2f degrees'%deg)
            if os.path.exists(savepath) and len(os.listdir(savepath))>0: raise FileExistsError('Duplicate savepath was detected in %s, please change dirpath to prevent overwriting data')
            if not os.path.exists(savepath): os.mkdir(savepath)
            
            pos=self.deg_to_pos(deg)
            self.motor.move(pos)

            v = [self.daq.voltage(BUTTON_CHAN) for i in range(NUM_VOLT_AVG)]
            t=[time.time()]*NUM_VOLT_AVG
            if len(self.daq.CHANNELS)>1: vc=[other_daq_channels() for i in range(NUM_VOLT_AVG)]

            while np.mean(v) < VOLT_THRESH:
                print('\r','Motor is in position, system is ready to take data when button press is detected (current reading = %0.2f'%np.mean(v), end='')
                v.append(self.daq.voltage())
                v.pop(0)
                t.append(time.time())
                t.pop(0)
                if len(self.daq.CHANNELS)>1: 
                    vc.append(other_daq_channels())
                    vc.pop(0)

            print('\n\n')

            img_time=t[0]
            self.save_img(filename(savepath,time.time()-t[0]))
            while True:
                print('\r','Button press detected, recording data (time elapsed = %0.1f seconds)'%(time.time()-t[0]),end='')

                t.append(time.time())
                v.append(self.daq.voltage(BUTTON_CHAN))
                if len(self.daq.CHANNELS)>1: vc.append(other_daq_channels())

                if TAKE_IMGS and (t[-1]-img_time)>IMG_DELAY:
                    img_fn = filename(savepath,t[-1]-t[0])
                    img=self.save_img(img_fn)
                    img_time=t[-1]
                    if SHOW_IMGS:
                        plt.cla()
                        plt.imshow(img)
                        plt.title(f'Angle = {deg} degrees',fontsize=20)
                        plt.pause(0.01)
                
                if np.mean(v[-NUM_VOLT_AVG:]) < VOLT_THRESH: 
                    break
            
            if len(self.daq.CHANNELS)==1:
                data = np.vstack((t,v))
            else:
                data = np.vstack((t,v,vc))
            np.save(os.path.join(savepath,'voltages'),)
            print('Button release detected, system has stopped recording data. %i images/data points were recorded'%len(v))
                
            if PAUSE:
                input("\n\nPress any key to advance to next position")