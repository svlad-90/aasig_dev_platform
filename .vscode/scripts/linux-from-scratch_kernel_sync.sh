#!/bin/bash

python ${1}/paf_main.py -imd ${2}/../paf/linux_deployment -c ${2}/../paf/linux_deployment/scenarios.xml -t linux_deployment.linux_kernel.linux_kernel_sync -ld=${3};

