#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/build_android/general_settings.xml -c ${2}/images/images.xml -c ${2}/qemu/qemu.xml -c ${2}/qemu/qemu_uboot_arm64.xml -c ${2}/${3} -s qemu_build_images_and_run_android -ld=${4} -p IMAGES_BOOT_IMAGE_TYPE="NOABI_LINUX";
