#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/build_android/general_settings.xml -c ${2}/${3} -t aasig_dev_platform.build_android.android_build -ld=${4} -p LOCAL_VENDOR_SOURCE_PATH=${5} -p LOCAL_VENDOR_DESTINATION_PATH=${6};
