#!/bin/bash

python ${1}/paf_main.py -imd ${2}/../paf/linux_deployment -c ${2}/../paf/linux_deployment/scenarios.xml -t linux_deployment.linux_kernel.linux_kernel_configure -p LINUX_KERNEL_CONFIG_ADJUSTMENT_MODE="USER_INTERACTIVE" -p LINUX_KERNEL_CONFIGURE_EDIT="True" -ld=${3};

