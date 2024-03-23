# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 10:14:08 2024

@author: jaris
"""
from pypylon import pylon

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
            if not isinstance(converter,pylon.ImageFormatConverter):
                converter=rgb_converter()
        except NameError:
            converter=rgb_converter()
        targetImage=converter.Convert(result)
        return targetImage.Array
    
    else:
        return result