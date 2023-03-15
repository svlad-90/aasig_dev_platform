#!/bin/bash

python ${1}/paf_main.py -imd ${2}/../paf/linux_deployment -c ${2}/../paf/linux_deployment/scenarios.xml -t linux_deployment.busybox.busybox_configure -p BUSYBOX_CONFIG_ADJUSTMENT_MODE="USER_INTERACTIVE" -p BUSYBOX_CONFIGURE_EDIT="True" -ld=${3};

