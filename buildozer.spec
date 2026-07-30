[app]
title = SOSmart
package.name = sosmart
package.domain = org.guardianesdigitales

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 0.1.0

requirements = python3==3.11.9,hostpython3==3.11.9,kivy,plyer,pyjnius

orientation = portrait
fullscreen = 0

services = Tracking:service/tracking_service.py

android.permissions = INTERNET,RECORD_AUDIO,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,SEND_SMS,FOREGROUND_SERVICE,FOREGROUND_SERVICE_LOCATION

android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
