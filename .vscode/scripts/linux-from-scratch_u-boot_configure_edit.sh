#!/bin/bash

python ${1}/paf_main.py -imd ${2}/../paf/linux_deployment -c ${2}/../paf/linux_deployment/scenarios.xml -t linux_deployment.uboot.uboot_configure -p UBOOT_CONFIGURE_EDIT="True" -ld=${3};

