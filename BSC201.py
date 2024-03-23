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
    def __init__(self,serial_no = '40418024',DeviceType='DRV250',**kwargs):
        self.DeviceType=DeviceType
        for k,v in kwargs.items():
            setattr(self,k,v)
        
        DeviceManagerCLI.BuildDeviceList()

        self.device = device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial_no)
        device.Connect(serial_no)
        time.sleep(0.25)  # wait statements are important to allow settings to be sent to the device
        if not self.is_connected:
            raise ConnectionError('Device failed to connect')
        self.build_device()

    @property
    def is_connected(self):
        return self.device.IsConnected
    
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
        
    def move_relative(self,distance):
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