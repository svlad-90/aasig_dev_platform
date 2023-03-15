#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/xen_qemu_virtio_development/xen_qemu_virtio_development.xml -c ${2}/moulin/moulin.xml -s moulin_nfs_and_tftp_deploy -ld=${3};
