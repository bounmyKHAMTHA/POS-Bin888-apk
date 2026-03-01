[app]
# (str) Title of your application
title = ຂາຍເຄື່ອງອອນລາຍ

# (str) Package name
package.name = bin888

# (str) Package domain (needed for android/ios packaging)
package.domain = org.bounmykhamtha

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf,json
source.exclude_exts = spec,txt

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3, kivy==2.3.0, kivymd==1.2.0, requests, pyjnius, Pillow

# (str) Custom source folders for requirements
# ค้นหาไฟล์ฟอนต์และไฟล์ประกอบอื่นๆ
source.include_patterns = assets/*,*.ttf,*.json,*.png

# (str) Icon of the application
icon.filename = %(source.dir)s/app_icon.png

# (str) Presplash of the application
presplash.filename = %(source.dir)s/presplash.png

# (str) Presplash color
android.presplash_color = #311B92

# (str) Application versioning (method 1)
version = 1.0.7

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
# เพิ่ม Fine Location เพื่อความแน่นอนในการสแกน Bluetooth บน Android 10-11
android.permissions = INTERNET, BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 23

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK directory
# android.sdk = /path/to/android/sdk

# (str) Android NDK directory
# android.ndk = /path/to/android/ndk

# (list) Android additionnal libraries
# android.add_libs_armeabi_v7a = lib/android/libname.so

# (bool) Use --private data storage (True) or --dir public storage (False)
# android.private_storage = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (str) Android additional Java classes to add to the project.
# android.add_javaclasses =

# (list) Android extra xml resources
# android.extra_xml = res/xml/file.xml

# (str) Android entry point, default is to use start.py
# android.entrypoint = org.kivy.android.PythonActivity

# (list) List of service to declare
# services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

# (str) Path to a custom whitelist file
# android.whitelist =

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# use latest stable p4a
p4a.branch = master

# (bool) enables Android auto backup feature (on by default)
android.allow_backup = True

# (str) Android additional java classes to be added to the build
# android.add_javaclasses = 

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (str) Path to build artifacts
bin_dir = ./bin
