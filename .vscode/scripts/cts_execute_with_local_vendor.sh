#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/build_android/general_settings.xml -c ${2}/${3} -c ${2}/cts.xml -ph execute_cts_with_local_vendor -ld=${4} -p LOCAL_VENDOR_SOURCE_PATH=${5} -p LOCAL_VENDOR_DESTINATION_PATH=${6};
