#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/xen_qemu_virtio_development/xen_qemu_virtio_development.xml -ph xqvd_docker_build_image_for_xen_and_qemu -ld=${3};
