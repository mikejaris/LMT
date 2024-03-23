# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 11:05:51 2024

@author: jaris
"""

import numpy as np
from ctypes import cast, POINTER, c_double, c_ushort, c_ulong
import time
from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status, InterfaceType, ULRange, AnalogInputMode, TriggerSource, TriggerEvent, TriggerSensitivity
from mcculw.ul import ULError, a_input_mode
from mcculw.device_info import DaqDeviceInfo
from dataclasses import dataclass, field

class MCC_DAQ:
    def __init__(self,**kwargs):
        self.SAMPLE_RATE=int(10e3)
        self.NUM_SAMPLES=int(50e3)
        self.BOARD_NUM=0
        self.CHANNELS=[0]
        self.VOLT_RANGE=10
        for k,v in kwargs.items():
            setattr(self,k,v)
        
        ul.ignore_instacal()#ignores their crappy software
        self.daqdevice = ul.get_daq_device_inventory(InterfaceType.USB)#find DAQ
        ul.create_daq_device(self.BOARD_NUM, self.daqdevice[0])#create DAQ handle for python
        
        self.scan_options = ScanOptions.FOREGROUND | ScanOptions.SCALEDATA

    @property
    def LOW_CHAN(self):
        return min(self.CHANNELS)
    
    @property
    def HIGH_CHAN(self):
        return max(self.CHANNELS)
        
    @property
    def VOLT_RANGE_ENUM(self):
        volt_to_ul = {10:'BIP10VOLTS', 15:'BIP15VOLTS', 1.25:'BIP1PT25VOLTS',
         1.67:'BIP1PT67VOLTS', 1:'BIP1VOLTS', 20:'BIP20VOLTS', 2.5:'BIP2PT5VOLTS',
         2:'BIP2VOLTS', 30:'BIP30VOLTS', 4:'BIP4VOLTS', 5:'BIP5VOLTS', 60:'BIP60VOLTS',
         0.005:'BIPPT005VOLTS', 0.01:'BIPPT01VOLTS', 0.025:'BIPPT025AMPS', 0.05:'BIPPT05VOLTS',
         0.078:'BIPPT078VOLTS', 0.125:'BIPPT125VOLTS', 0.156:'BIPPT156VOLTS',0.1:'BIPPT1VOLTS',
         0.25:'BIPPT25VOLTS', 0.2:'BIPPT2VOLTS', 0.312:'BIPPT312VOLTS', 0.5:'BIPPT5VOLTS',
         0.625:'BIPPT625VOLTS'}
        
        volts=np.fromiter(volt_to_ul.keys(),float)
        im = np.sort(volts[volts>self.VOLT_RANGE])[0]
        return getattr(ULRange,volt_to_ul[im])

    def voltage_scan(self,**kwargs):
        for k,v in kwargs.items():
            setattr(self,k,v)
            
        while self.NUM_SAMPLES%len(self.CHANNELS) != 0:
            self.NUM_SAMPLES-=1
            
        memhandle = ul.scaled_win_buf_alloc(self.NUM_SAMPLES)#buffer handle (direct access to buffer - be careful!)
        buf_data = cast(memhandle,POINTER(c_double))#create buffer to copy data to
        
        ul.a_in_scan(self.BOARD_NUM, self.LOW_CHAN, self.HIGH_CHAN, self.NUM_SAMPLES,self.SAMPLE_RATE, self.VOLT_RANGE_ENUM, memhandle, self.scan_options)#function to setup analog scan
                
        ul.scaled_win_buf_to_array(memhandle, buf_data, 0, int(self.NUM_SAMPLES))
        BUF_DATA = np.asarray(buf_data[:int(self.NUM_SAMPLES)])
        
        SAMPLES_PER_CHANNEL = self.NUM_SAMPLES//len(self.CHANNELS)
            
        DATA = np.array([BUF_DATA[i::(len(self.CHANNELS))][:SAMPLES_PER_CHANNEL] for i in range(len(self.CHANNELS))])
            
        ul.stop_background(self.BOARD_NUM, FunctionType.AIFUNCTION)#stop recording the DAQ
        ul.win_buf_free(memhandle)#release the buffer to prevent crashing system
        return DATA
    
    def voltage(self,CHANNEL=None):
        if CHANNEL is None:
            val = [ul.to_eng_units_32(self.BOARD_NUM,self.VOLT_RANGE_ENUM,
                  ul.a_in_32(self.BOARD_NUM,CHANNEL,self.VOLT_RANGE_ENUM)) for CHANNEL in self.CHANNELS]
        else:
            val = ul.to_eng_units_32(self.BOARD_NUM,self.VOLT_RANGE_ENUM,
                 ul.a_in_32(self.BOARD_NUM,CHANNEL,self.VOLT_RANGE_ENUM))
        if len(val) ==1: val=val[0]

        return val