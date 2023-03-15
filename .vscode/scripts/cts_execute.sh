#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/build_android/general_settings.xml -c ${2}/${3} -c ${2}/cts.xml -ph execute_cts -ld=${4};
