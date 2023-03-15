'''
Created on Sep 09, 2022

@author: vladyslav_goncharuk
'''

import math
import os
from enum import Enum
from typing import Dict
from common.common import BaseAndroidTask, mkimage_command, path_leaf
from common.common import create_android_boot_image_command, bootconfig_command, split_kernel_cmd_line
from paf.paf_impl import logger, Environment

class ImagesTask(BaseAndroidTask):

    def __init__(self):
        super().__init__()

        self.RAMDISK_IMAGE_DIR=f"{self.BUILD_IMAGES_DIR}/ramdisk"
        self.RAMDISK_IMAGE=f"{self.ANDROID_PRODUCT_PATH}/ramdisk.img"
        self.RAMDISK_IMAGE_EXPERIMENTAL=f"{self.RAMDISK_IMAGE_DIR}/ramdisk.img"

        self.RAMDISK_IMAGE_PRODUCT_DIR=f"{self.ANDROID_PRODUCT_PATH}/ramdisk"
        self.VENDOR_RAMDISK_DIR=f"{self.ANDROID_PRODUCT_PATH}/vendor_ramdisk"

        self.BOOT_IMAGE_MOUNTPOINT=f"{self.BOOT_IMAGE_SUB_DIR}/mnt"

        self.VBMETA_IMAGE=f"{self.ANDROID_PRODUCT_PATH}/vbmeta.img"


class images_recreate_images_dir(ImagesTask):
    def __init__(self):
        super().__init__()
        self.set_name(images_recreate_images_dir.__name__)

    def execute(self):
        logger.info("Recreating images folder ...")

        if self.has_environment_true_param("IMAGES_BUILD_BOOT_IMAGE"):
            self.subprocess_must_succeed(f"sudo -S umount {self.BOOT_IMAGE_MOUNTPOINT} || :")

        self.subprocess_must_succeed(f"rm -rf {self.BUILD_IMAGES_DIR}")
        self.subprocess_must_succeed(f"mkdir {self.BUILD_IMAGES_DIR}")

def fileSizeInMb(filePath):
    logger.info("Size of '" + filePath + "' is - " + str(os.stat(filePath).st_size) )
    sizeOfFile = math.ceil(os.stat(filePath).st_size / 1024 / 1024)
    return sizeOfFile

class e_fs_type(Enum):
    fs_from_image = 0
    fs_empty = 1
    fs_zeroed = 2

class t_fs_metadata():
    def __init__(self, fs_type : e_fs_type):
        self.fs_type = fs_type
        self.fs_image_name_key = ""
        self.fs_image_path_key = ""
        self.fs_image_path = ""
        self.partition_type_key = ""
        self.mount_path_key = ""
        self.fs_size = 0
        self.is_bootable = False
        self.id = 0

    def dump(self):
        return "t_fs_metadata: fs_type - " + str(self.fs_type) + "; " + \
        "fs_image_name_key - " + str(self.fs_image_name_key) + "; " + \
        "fs_image_path_key - " + str(self.fs_image_path_key) + "; " + \
        "fs_image_path - " + str(self.fs_image_path) + "; " + \
        "partition_type_key - " + self.partition_type_key + "; " + \
        "mount_path_key - " + self.mount_path_key + "; " + \
        "fs_size - " + str(self.fs_size) + "; " + \
        "is_bootable - " + str(self.is_bootable) + "; " + \
        "id - " + str(self.id) + "; "

def parse_fs_metadata(substitute_func,
                        subprocess_must_success_func,
                        android_fs_path : str,
                        experimental_path : str,
                        environment : Environment) -> Dict[str, t_fs_metadata]:
    variables = environment.getVariables()

    images = {}

    for key, value in variables.items():
        target_prefix = "FS_DECLARATION_"
        if key.startswith(target_prefix):

            fs_type = e_fs_type.fs_from_image

            if value.lower() == "fs_from_image":
                fs_type = e_fs_type.fs_from_image
            elif value.lower() == "fs_empty":
                fs_type = e_fs_type.fs_empty
            elif value.lower() == "fs_zeroed":
                fs_type = e_fs_type.fs_zeroed
            else:
                raise Exception('Error: wrong FS ' + "'" + value + "'" + ' was specified!')

            images[key.split(target_prefix,1)[1]] = t_fs_metadata(fs_type)

    logger.info("Parsed image names - " + str(images))

    partition_counter = 1

    for fs_name, fs_metadata in images.items():

        fs_image_name_key = "FS_" + fs_name + "_IMAGE_NAME"
        if not fs_image_name_key in variables and fs_metadata.fs_type == e_fs_type.fs_from_image:
            raise Exception("Error: the expected key '" + fs_image_name_key + "' was not found in the parameters!")

        fs_metadata.fs_image_name_key = fs_image_name_key

        fs_image_path_key = "FS_" + fs_name + "_IMAGE_PATH"
        if fs_image_path_key in variables:
            fs_metadata.fs_image_path_key = fs_image_path_key

        fs_size_key = "FS_" + fs_name + "_SIZE_MB"

        if fs_metadata.fs_image_path_key:
            fs_metadata.fs_image_path = f"${{{fs_metadata.fs_image_path_key}}}/${{{fs_metadata.fs_image_name_key}}}.img"
        else:
            fs_metadata.fs_image_path = f"{android_fs_path}/${{{fs_metadata.fs_image_name_key}}}.img"

        if fs_metadata.fs_type == e_fs_type.fs_from_image:
            if fs_size_key in variables:
                fs_metadata.fs_size = int(variables[fs_size_key])
            else:
                file_command_output = subprocess_must_success_func(f"file \"{fs_metadata.fs_image_path}\"")
                is_sparse_image = "sparse" in file_command_output.lower()
                if is_sparse_image:
                    subprocess_must_success_func(f"""function android_sparse_fs_to_raw_image()
{{
    local fs_file=$$1
    local target_file=$$2

    echo "simg2img $$fs_file $$target_file"
    simg2img $$fs_file $$target_file
}}

mkdir -p {experimental_path}/${{{fs_metadata.fs_image_name_key}}}
android_sparse_fs_to_raw_image {fs_metadata.fs_image_path} {experimental_path}/${{{fs_metadata.fs_image_name_key}}}/${{{fs_metadata.fs_image_name_key}}}.img""")
                    fs_metadata.fs_size = fileSizeInMb(substitute_func(f"{experimental_path}/${{{fs_metadata.fs_image_name_key}}}/${{{fs_metadata.fs_image_name_key}}}.img"))
                else:
                    fs_metadata.fs_size = fileSizeInMb(substitute_func(fs_metadata.fs_image_path))
        else:
            if not fs_size_key in variables:
                raise Exception("Error: the expected key '" + fs_size_key + "' was not found in the parameters!")
            fs_metadata.fs_size = int(variables[fs_size_key])

        partition_type_key = "FS_" + fs_name + "_TYPE"
        if not partition_type_key in variables:
            raise Exception("Error: the expected key '" + partition_type_key + "' was not found in the parameters!")
        fs_metadata.partition_type_key = partition_type_key

        mount_path_key = "FS_" + fs_name + "_MOUNT_PATH"
        if not mount_path_key in variables:
            raise Exception("Error: the expected key '" + mount_path_key + "' was not found in the parameters!")
        fs_metadata.mount_path_key = mount_path_key

        bootable_key = "FS_" + fs_name + "_IS_BOOTABLE"
        if bootable_key in variables:
            fs_metadata.is_bootable = environment.getVariableValue(bootable_key) == "True"

        fs_metadata.id = partition_counter
        partition_counter = partition_counter + 1

        logger.info("Parsed fs_metadata: " + fs_metadata.dump())

    return images

class images_build_main_image(ImagesTask):
    def __init__(self):
        super().__init__()
        self.set_name(images_build_main_image.__name__)

    def execute(self):

        images = parse_fs_metadata(self.substitute_parameters,
                                       self.subprocess_must_succeed,
                                       self.ANDROID_PRODUCT_PATH,
                                       self.BUILD_IMAGES_DIR,
                                       self.get_environment())

        logger.info("Building 'main' image ...")

        main_fs_size = 10 # leaving some overhead 10 Mb-s, just to be on the safe side

        for fs_name, fs_metadata in images.items():
            main_fs_size = main_fs_size + int(fs_metadata.fs_size)

        logger.info("Creating main image file ...")
        self.subprocess_must_succeed(f"mkdir -p {self.MAIN_IMAGE_DIR}")
        self.subprocess_must_succeed(f"""cd {self.MAIN_IMAGE_DIR};
            dd if=/dev/zero of={self.MAIN_IMAGE} bs=1M count=0 seek={main_fs_size} status=none || exit 1""")

        logger.info("Declaring partitions ...")

        command = f"""
function mkfs_one()
{{
    local loop_base=$$1
    local part=$$2
    local label=$$3
    sudo -S mkfs.ext4 -O 64bit -F $${{loop_base}}p$${{part}} -L $$label > /dev/null
}}

loop_base=`sudo -S losetup --find --show {self.MAIN_IMAGE}`
sudo -S parted $$loop_base -s mklabel gpt
"""

        starting_point = 1

        for fs_name, fs_metadata in images.items():
            subcommand = f"""sudo -S parted $$loop_base -s mkpart ${{{fs_metadata.mount_path_key}}} ${{{fs_metadata.partition_type_key}}} {str(starting_point)}MiB {str(starting_point + fs_metadata.fs_size)}Mib;
"""

            if fs_metadata.is_bootable:
                subcommand += f"""sudo parted $$loop_base set {fs_metadata.id} boot on;
"""

            starting_point = starting_point + fs_metadata.fs_size
            command = command + subcommand

        command = command  + """sudo -S parted $$loop_base -s print
echo "Filling in partitions ..."
"""
        for fs_name, fs_metadata in images.items():

            subcommand = ""

            if fs_metadata.fs_type == e_fs_type.fs_from_image:

                subcommand = subcommand + f"""echo "Filling in '${{{fs_metadata.fs_image_name_key}}}' partition ..."
"""

                file_command_output = self.subprocess_must_succeed(f"file \"{self.ANDROID_PRODUCT_PATH}/${{{fs_metadata.fs_image_name_key}}}.img\"")
                is_sparse_image = "sparse" in file_command_output.lower()

                if is_sparse_image:
                    subcommand = subcommand + f"""sudo -S dd if={self.BUILD_IMAGES_DIR}/${{{fs_metadata.fs_image_name_key}}}/${{{fs_metadata.fs_image_name_key}}}.img of=$${{loop_base}}p{fs_metadata.id} bs=1M status=none
"""
                else:
                    subcommand = subcommand + f"""sudo -S dd if={fs_metadata.fs_image_path} of=$${{loop_base}}p{fs_metadata.id} bs=1M status=none
"""
            elif fs_metadata.fs_type == e_fs_type.fs_empty:
                subcommand = subcommand + f"""echo "Creating fs for '${{{fs_metadata.fs_image_name_key}}}' partition ..."
mkfs_one $$loop_base {fs_metadata.id} ${{{fs_metadata.fs_image_name_key}}}
"""
            elif fs_metadata.fs_type == e_fs_type.fs_zeroed:
                subcommand = subcommand + f"""echo "Wiping '${{{fs_metadata.fs_image_name_key}}}' partition ..."
sudo -S dd if=/dev/zero of=$${{loop_base}}p{fs_metadata.id} bs=1M count={fs_metadata.fs_size} status=none
"""

            command = command + subcommand

        command = command  + """sudo -S losetup -d $$loop_base
"""

        self.subprocess_must_succeed(command)

class images_append_vb_meta_digest(ImagesTask):
    def __init__(self):
        super().__init__()
        self.set_name(images_append_vb_meta_digest.__name__)

    def execute(self):

        output = self.subprocess_must_succeed(f"""AVBTOOL_PATH={self.ANDROID_BUILD_PATH}/host/linux-x86/bin/avbtool
VBMETA_DIGEST=""

VB_META_IMAGE_INFO=$$($${{AVBTOOL_PATH}} info_image --image {self.VBMETA_IMAGE})
FLAGS=$$(echo "$${{VB_META_IMAGE_INFO}}" | sed -n -e '0,/Flags/{{s/.*Flags:[ ]\+\([[:digit:]]\+\).*/\\1/p}}')
HEADER_BLOCK=$$(echo "$${{VB_META_IMAGE_INFO}}" | sed -n -e '0,/Header Block/{{s/.*Header Block:[ ]\+\([[:digit:]]\+\).*/\\1/p}}')
AUTHENTICATION_BLOCK=$$(echo "$${{VB_META_IMAGE_INFO}}" | sed -n -e '0,/Authentication Block/{{s/.*Authentication Block:[ ]\+\([[:digit:]]\+\).*/\\1/p}}')
AUXILIARY_BLOCK=$$(echo "$${{VB_META_IMAGE_INFO}}" | sed -n -e '0,/Auxiliary Block/{{s/.*Auxiliary Block:[ ]\+\([[:digit:]]\+\).*/\\1/p}}')
VBMETA_DIGEST_SIZE=$$(($$HEADER_BLOCK + $$AUTHENTICATION_BLOCK + $$AUXILIARY_BLOCK))

if [ $$(($${{FLAGS}} & 2)) != 0 ]; then
    VBMETA_DIGEST=$$(dd if={self.VBMETA_IMAGE} bs=1 count=$${{VBMETA_DIGEST_SIZE}} | sha256sum | head -c 64)
else
    VBMETA_DIGEST=$$($${{AVBTOOL_PATH}} calculate_vbmeta_digest --hash_algorithm sha256 --image {self.VBMETA_IMAGE})
fi

KERNEL_CMDLINE_ADDITION="androidboot.vbmeta.size=$${{VBMETA_DIGEST_SIZE}} \\
androidboot.vbmeta.hash_alg=sha256 \\
androidboot.vbmeta.digest=$${{VBMETA_DIGEST}}"

echo "___delimiter___$${{KERNEL_CMDLINE_ADDITION}}";
sleep 1""")

        calculated_digets = output.split("___delimiter___",1)[1]
        calculated_digets = calculated_digets.strip()

        logger.info("Calculated additional kernel cmd line - " + calculated_digets)

        self.set_environment_param("KERNEL_CMDLINE_DIGEST", calculated_digets)

class t_boot_image_metadata():
    def __init__(self):
        self.size_key = ""
        self.ramdisk_path_key = ""
        self.kernel_path_key = ""
        self.use_abi = False

def parse_boot_image_metadata(environment : Environment) -> t_boot_image_metadata:

    result = t_boot_image_metadata()

    variables = environment.getVariables()

    image_type = environment.getVariableValue("IMAGES_BOOT_IMAGE_TYPE")

    size_key = "IMAGES_" + image_type + "_SIZE_MB"
    if not size_key in variables:
        raise Exception("Error: the expected key '" + size_key + "' was not found in the parameters!")
    result.size_key = size_key

    ramdisk_path_key = "IMAGES_" + image_type + "_RAMDISK_PATH"
    if not ramdisk_path_key in variables:
        raise Exception("Error: the expected key '" + ramdisk_path_key + "' was not found in the parameters!")
    result.ramdisk_path_key = ramdisk_path_key

    kernel_path_key = "IMAGES_" + image_type + "_KERNEL_PATH"
    if not kernel_path_key in variables:
        raise Exception("Error: the expected key '" + kernel_path_key + "' was not found in the parameters!")
    result.kernel_path_key = kernel_path_key

    use_abi_key = "IMAGES_" + image_type + "_USE_ABI"
    if not use_abi_key in variables:
        raise Exception("Error: the expected key '" + use_abi_key + "' was not found in the parameters!")
    result.use_abi = environment.getVariableValue(use_abi_key) == "True"

    return result

class images_build_ramdisk(ImagesTask):
    def __init__(self):
        super().__init__()
        self.set_name(images_build_ramdisk.__name__)

    def execute(self):

        logger.info("Building ramdisk ...")
        self.subprocess_must_succeed(f"mkdir -p {self.RAMDISK_IMAGE_DIR} && cd {self.RAMDISK_IMAGE_DIR} \
            && lz4 -d {self.RAMDISK_IMAGE} {self.RAMDISK_IMAGE}.cpio && cpio -idv < {self.RAMDISK_IMAGE}.cpio \
            && rm {self.RAMDISK_IMAGE}.cpio && cp -R {self.RAMDISK_IMAGE_PRODUCT_DIR}/* {self.RAMDISK_IMAGE_DIR} \
            && cp -R {self.VENDOR_RAMDISK_DIR}/* {self.RAMDISK_IMAGE_DIR} \
            && find . ! -name . | LC_ALL=C sort | cpio -o -H newc -R root:root | lz4 -l -12 --favor-decSpeed \
            > {self.RAMDISK_IMAGE_EXPERIMENTAL}")

        if self.has_environment_true_param("IMAGES_BUILD_BOOT_IMAGE"):
            boot_image_metadata = parse_boot_image_metadata(self.get_environment())

            if True == boot_image_metadata.use_abi:
                # We should add bootconfig
                splited_kernel_cmdline = split_kernel_cmd_line(self.substitute_parameters("${ANDROID_KERNEL_CMDLINE} " + self.KERNEL_CMDLINE_DIGEST))
                self.subprocess_must_succeed(f'echo "{splited_kernel_cmdline}" >> {self.RAMDISK_IMAGE_DIR}/android_bootconfig.txt')

                logger.info( "Adding bootconfig to the ramdisk ..." )

                self.subprocess_must_succeed(bootconfig_command( "${IMAGES_KERNEL_BOOTCONFIG_PATH}",
                                                                f"{self.RAMDISK_IMAGE_EXPERIMENTAL}",
                                                                clear = True,
                                                                add = f"{self.RAMDISK_IMAGE_DIR}/android_bootconfig.txt" ))

class images_build_boot_image(ImagesTask):
    def __init__(self):
        super().__init__()
        self.set_name(images_build_boot_image.__name__)

    def execute(self):

        logger.info("Building 'boot' image ...")

        boot_image_metadata = parse_boot_image_metadata(self.get_environment())

        self.subprocess_must_succeed(f"mkdir -p {self.BOOT_IMAGE_DIR}; rm -rf {self.BOOT_IMAGE_SUB_DIR}; mkdir {self.BOOT_IMAGE_SUB_DIR}")

        logger.info("Creating 'boot' image file ...")
        self.subprocess_must_succeed(f"""dd if=/dev/zero of={self.BOOT_IMAGE} bs=1M count=0 seek=${{{boot_image_metadata.size_key}}}
status=none || exit 1; mkfs.ext2 {self.BOOT_IMAGE}""")

        logger.info("Mounting 'boot' partition ...")
        self.subprocess_must_succeed(f"""mkdir -p {self.BOOT_IMAGE_MOUNTPOINT}; sudo -S mount -o rw {self.BOOT_IMAGE} {self.BOOT_IMAGE_MOUNTPOINT};
sudo -S chmod 777 {self.BOOT_IMAGE_MOUNTPOINT}; mkdir -p {self.BOOT_IMAGE_MOUNTPOINT}/boot""")

        logger.info("Copying files into the mounted 'boot' partition ...")
        copy_files = []

        kernel_file_name = "Image"

        if False == boot_image_metadata.use_abi:

            self.subprocess_must_succeed( mkimage_command("${QEMU_ARCH}",
                                                          "${IMAGES_UBOOT_MKIMAGE_PATH}",
                                                          f"${boot_image_metadata.kernel_path_key}",
                                                          "kernel",
                                                          compression = "none",
                                                          load_addr = "0x53000000",
                                                          destination = f"{self.BOOT_IMAGE_SUB_DIR}/kernel.uimg"))

            copy_files.append( (f"{self.BOOT_IMAGE_SUB_DIR}/kernel.uimg", f"{self.BOOT_IMAGE_MOUNTPOINT}/boot/{kernel_file_name}") )

            self.subprocess_must_succeed( mkimage_command("${QEMU_ARCH}",
                                        "${IMAGES_UBOOT_MKIMAGE_PATH}",
                                        f"${boot_image_metadata.ramdisk_path_key}",
                                        "ramdisk",
                                        compression = "none",
                                        load_addr = "0x55000000",
                                        destination = f"{self.BOOT_IMAGE_SUB_DIR}/ramdisk.uimg"))

            copy_files.append( (f"{self.BOOT_IMAGE_SUB_DIR}/ramdisk.uimg", f"{self.BOOT_IMAGE_MOUNTPOINT}/boot/rootfs.cpio") )

            self.subprocess_must_succeed("cp ${IMAGES_BOOT_SCR_PATH}" + f" {self.BOOT_IMAGE_SUB_DIR}/boot.scr")
            self.subprocess_must_succeed(f"sed -i -e '/setenv use_abi/ s/use_abi .*/use_abi 0/' {self.BOOT_IMAGE_SUB_DIR}/boot.scr")
            self.subprocess_must_succeed(f"sed -i -e '/setenv kernel_location/ s/kernel_location .*/kernel_location \/boot\/{kernel_file_name}/' {self.BOOT_IMAGE_SUB_DIR}/boot.scr")
            ramdisk_file_name = path_leaf(self.get_environment().getVariableValue(boot_image_metadata.ramdisk_path_key))
            self.subprocess_must_succeed(f"sed -i -e '/setenv ramdisk_location/ s/ramdisk_location .*/ramdisk_location \/boot\/{ramdisk_file_name}/' {self.BOOT_IMAGE_SUB_DIR}/boot.scr")
            self.subprocess_must_succeed(f"sed -i -e '/setenv dtb_location/ s/dtb_location .*/dtb_location \/boot\/dtb.dtb/' {self.BOOT_IMAGE_SUB_DIR}/boot.scr")
            escaped_kernel_cmd_line = self.get_environment().getVariableValue("KERNEL_CMDLINE")
            escaped_kernel_cmd_line = escaped_kernel_cmd_line.replace("/", "\\/")
            self.subprocess_must_succeed(f"""sed -i -e "/setenv bootargs_custom/ s/bootargs_custom .*/bootargs_custom \\\"{escaped_kernel_cmd_line}\\\"/" {self.BOOT_IMAGE_SUB_DIR}/boot.scr""")

            self.subprocess_must_succeed( mkimage_command("${QEMU_ARCH}",
                                        "${IMAGES_UBOOT_MKIMAGE_PATH}",
                                        f"{self.BOOT_IMAGE_SUB_DIR}/boot.scr",
                                        "script",
                                        compression = "none",
                                        load_addr = "0x65000000",
                                        destination = f"{self.BOOT_IMAGE_SUB_DIR}/boot.scr.uimg"))

            copy_files.append( (f"{self.BOOT_IMAGE_SUB_DIR}/boot.scr.uimg", f"{self.BOOT_IMAGE_MOUNTPOINT}/boot/boot.scr") )

            copy_files.append( ("${IMAGES_DTB_PATH}", f"{self.BOOT_IMAGE_MOUNTPOINT}/boot/dtb.dtb") )
        else:

            non_android_boot_config = self.subprocess_must_succeed("")

            self.subprocess_must_succeed( create_android_boot_image_command(
                f"{self.ANDROID_BUILD_PATH}/host/linux-x86/bin/mkbootimg",
                header_version = 2,
                kernel = f"${{{boot_image_metadata.kernel_path_key}}}",
                ramdisk = f"${{{boot_image_metadata.ramdisk_path_key}}}",
                dtb = "${IMAGES_DTB_PATH}",
                cmdline = "bootconfig" + " ${KERNEL_CMDLINE}",
                out = f"{self.BOOT_IMAGE_SUB_DIR}/abi.img",
                base = 0x50000000,
                kernel_offset = 0x3000000,
                ramdisk_offset = 0x6000000,
                dtb_offset = 0x00000000) )
            copy_files.append( (f"{self.BOOT_IMAGE_SUB_DIR}/abi.img", f"{self.BOOT_IMAGE_MOUNTPOINT}/boot/boot_linux.img") )

            self.subprocess_must_succeed("cp ${IMAGES_BOOT_SCR_PATH}" + f" {self.BOOT_IMAGE_SUB_DIR}/boot.scr")
            self.subprocess_must_succeed(f"sed -i -e '/setenv use_abi/ s/use_abi .*/use_abi 1/' {self.BOOT_IMAGE_SUB_DIR}/boot.scr")
            self.subprocess_must_succeed(f"sed -i -e '/setenv abi_location/ s/abi_location .*/abi_location \/boot\/boot_linux.img/' {self.BOOT_IMAGE_SUB_DIR}/boot.scr")
            self.subprocess_must_succeed(f"sed -i -e '/setenv dtb_location/ s/dtb_location .*/dtb_location \/boot\/dtb.dtb/' {self.BOOT_IMAGE_SUB_DIR}/boot.scr")

            self.subprocess_must_succeed( mkimage_command("${QEMU_ARCH}",
                                        "${IMAGES_UBOOT_MKIMAGE_PATH}",
                                        f"{self.BOOT_IMAGE_SUB_DIR}/boot.scr",
                                        "script",
                                        compression = "none",
                                        load_addr = "0x65000000",
                                        destination = f"{self.BOOT_IMAGE_SUB_DIR}/boot.scr.uimg"))

            copy_files.append( (f"{self.BOOT_IMAGE_SUB_DIR}/boot.scr.uimg", f"{self.BOOT_IMAGE_MOUNTPOINT}/boot/boot.scr") )

            copy_files.append( ("${IMAGES_DTB_PATH}", f"{self.BOOT_IMAGE_MOUNTPOINT}/boot/dtb.dtb") )

        copy_command = ""

        for copy_file in copy_files:
            copy_command += "cp " + copy_file[0] + " " + copy_file[1] + "; "
        self.subprocess_must_succeed(copy_command)

        logger.info("Unmounting 'boot' partition ...")
        self.subprocess_must_succeed(f"""sudo -S umount {self.BOOT_IMAGE_MOUNTPOINT}""")

        self.set_environment_param("FS_DECLARATION_BOOT", "fs_from_image")
        substituted_boot_image_path = self.substitute_parameters(self.BOOT_IMAGE_SUB_DIR)
        self.set_environment_param("FS_BOOT_IMAGE_PATH", f"{substituted_boot_image_path}")
        self.set_environment_param("FS_BOOT_IMAGE_NAME", "boot")
        self.set_environment_param("FS_BOOT_TYPE", "ext2")
        self.set_environment_param("FS_BOOT_SIZE_MB", "256")
        self.set_environment_param("FS_BOOT_MOUNT_PATH", "boot_a")
        self.set_environment_param("FS_BOOT_IS_BOOTABLE", "True")
