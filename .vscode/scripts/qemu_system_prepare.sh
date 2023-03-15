#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/build_android/general_settings.xml -c ${2}/qemu/qemu.xml -c ${2}/${3} -s qemu_system_prepare -ld=${4};
