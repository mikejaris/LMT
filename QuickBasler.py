# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 10:14:08 2024

@author: jaris
"""
from pypylon import pylon
import numpy as np

def rgb_converter():
    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_RGB8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
    return converter


def connect_cam(sn='40305789'):
    info = pylon.DeviceInfo()
    info.SetSerialNumber(sn)
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()
    return camera

def get_img(camera,convert_to_rgb=True):
    if not camera.IsGrabbing():
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    camera.ExecuteSoftwareTrigger()
    result = camera.RetrieveResult(2000)
    
    if convert_to_rgb:
        try:
            converter=rgb_converter()
            targetImage=converter.Convert(result)
            return targetImage.Array
        except:
            print('Image was not transferred successfully, returning empty array')
            return np.zeros((2160,3840,3),dtype=np.uint8)
    
    else:
        return result