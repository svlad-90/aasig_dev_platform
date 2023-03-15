#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/xen_qemu_virtio_development/xen_qemu_virtio_development.xml -ph xqvd_check_virtio_gpu_mmio -ld=${3};
