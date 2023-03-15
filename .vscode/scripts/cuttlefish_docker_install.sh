#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/build_android/general_settings.xml -c ${2}/${3} -c ${2}/${4} -ph cuttlefish_docker_install -ld=${5};

