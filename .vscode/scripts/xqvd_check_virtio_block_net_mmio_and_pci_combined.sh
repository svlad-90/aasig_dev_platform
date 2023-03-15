#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/xen_qemu_virtio_development/xen_qemu_virtio_development.xml -ph xqvd_check_virtio_block_net_mmio_and_pci_combined -ld=${3};
