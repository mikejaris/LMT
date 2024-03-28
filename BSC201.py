# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 17:45:18 2024

@author: jaris
"""

import os
import time
import sys
import clr
from System import Decimal  # necessary for real world units

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import *


class BSC201:
    def __init__(self,serial_no = '40418024',DeviceType='DRV250',max_velocity=2,acceleration=1,**kwargs):
        self.DeviceType=DeviceType
        for k,v in kwargs.items():
            setattr(self,k,v)
        
        DeviceManagerCLI.BuildDeviceList()

        self.connect(serial_no=serial_no,build_device=True)
        self.set_velocity_params(max_velocity,acceleration)

    @property
    def is_connected(self):
        return self.device.IsConnected
    
    def connect(self,serial_no=None,build_device=True):
        self.serial_no = serial_no = self.serial_no if serial_no is None else serial_no
        self.device = device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial_no)
        device.Connect(serial_no)
        time.sleep(0.25)  # wait statements are important to allow settings to be sent to the device
        if not self.is_connected:
            raise ConnectionError('Device failed to connect')
        if build_device:
            self.build_device()
            
    def build_device(self):
        # For benchtop devices, get the channel
        self.channel = channel = self.device.GetChannel(1)
        # Ensure that the device settings have been initialized
        if not channel.IsSettingsInitialized():
            channel.WaitForSettingsInitialized(10000)  # 10 second timeout
            assert channel.IsSettingsInitialized() is True
            
        # Start polling and enable
        channel.StartPolling(250)  #250ms polling rate
        time.sleep(0.25)
        channel.EnableDevice()
        time.sleep(0.25)  # Wait for device to enable
        
        # Get Device Information and display description
        device_info = channel.GetDeviceInfo()
        print(device_info.Description)
        
        # Load any configuration settings needed by the controller/stage
        self.channel_config = channel_config = channel.LoadMotorConfiguration(channel.DeviceID) # If using BSC203, change serial_no to channel.DeviceID. 
        self.chan_setting = chan_settings = channel.MotorDeviceSettings
        channel.GetSettings(chan_settings)
        
        channel_config.DeviceSettingsName = self.DeviceType
        channel_config.UpdateCurrentConfiguration()
        channel.SetSettings(chan_settings, True, False)
        self.device_info = self.device.GetDeviceInfo()

        
    def disconnect(self):
        self.channel.StopPolling()
        self.device.Disconnect()
        
    def home(self):
        # Home or Zero the device (if a motor/piezo)
        print("Homing Motor")
        self.channel.Home(60000)
        print("Done")


    def move(self,pos_mm):
        self.channel.SetMoveAbsolutePosition(Decimal(float(pos_mm)))
        self.channel.MoveAbsolute(10000)
         
    def get_position(self):
        return float(str(self.channel.Position))
    
    def set_jog_step_size(self,step_size=0.05):
        self.channel.SetJogStepSize(Decimal(float(step_size)))
        
    def move_relative(self,distance=0.001):
        self.channel.SetMoveRelativeDistance(Decimal(float(distance)))
        self.channel.MoveRelative(10000)
    
    @property
    def status(self):
        return self.channel.Status
    
    @property
    def state(self):
        return self.channel.State
    
    @property
    def position(self):
        return self.get_position()

    def move_smooth(self,pos_mm,step_size=0.001):
        num_moves = int((pos_mm-self.position)/step_size)
        self.channel.SetMoveRelativeDistance(Decimal(float(step_size)))
        for i in range(num_moves):
            self.channel.MoveRelative(10000)

    @property
    def max_velocity(self):
        vp = self.channel.GetVelocityParams()
        self._max_velocity=float(str(vp.MaxVelocity))
        return self._max_velocity
    
    @property
    def acceleration(self):
        vp = self.channel.GetVelocityParams()
        self._acceleration=float(str(vp.Acceleration))
        return self._acceleration
    
    def set_velocity_params(self,max_velocity=1,accel= 1):
        _vel0,_accel0 = self.max_velocity,self.acceleration
        self.channel.SetVelocityParams(Decimal(float(max_velocity)),Decimal(float(accel)))
        _vel,_accel = self.max_velocity,self.acceleration
        
        print('Previous settings: max velocity was %0.2f, acceleration was %0.2f'%(_vel0,_accel0))
        print('New settings: max velocity is %0.2f, acceleration is %0.2f'%(_vel,_accel))