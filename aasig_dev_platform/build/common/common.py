from curses.ascii import isspace
import os
import ntpath

from paf.paf_impl import Task, logger

class BaseAndroidTask(Task):

    def __init__(self):
        super().__init__()

        self.ANDROID_SOURCE_PATH = "${ROOT}/${ANDROID_DEPLOYMENT_DIR}/${SOURCE_DIR}/${ANDROID_REPO_BRANCH}"
        self.ANDROID_BUILD_DIR = "${ROOT}/${ANDROID_DEPLOYMENT_DIR}/${BUILD_DIR}/"
        self.ANDROID_BUILD_PATH = "${ROOT}/${ANDROID_DEPLOYMENT_DIR}/${BUILD_DIR}/${ANDROID_REPO_BRANCH}"
        self.ANDROID_PRODUCT_PATH=f"{self.ANDROID_BUILD_PATH}/target/product/" + "${TARGET_DEVICE}_${QEMU_ARCH}"

        self.BUILD_IMAGES_DIR=f"{self.ANDROID_PRODUCT_PATH}/build_images"
        self.BOOT_IMAGE_DIR=f"{self.BUILD_IMAGES_DIR}/boot"
        self.BOOT_IMAGE_SUB_DIR=f"{self.BUILD_IMAGES_DIR}/boot/" + "${IMAGES_BOOT_IMAGE_TYPE}"
        self.BOOT_IMAGE=f"{self.BOOT_IMAGE_SUB_DIR}/boot.img"

        self.MAIN_IMAGE_DIR=f"{self.BUILD_IMAGES_DIR}/main"
        self.MAIN_IMAGE=f"{self.MAIN_IMAGE_DIR}/main.img"

def mkimage_command( arch: str, mkimage_tool_path: str, source: str, img_type: str, **kwargs ):
    kw_source: str = ""
    kw_destination = kwargs.get( "destination", None )
    kw_os_type = kwargs.get( "os_type", "linux" )
    kw_compression = kwargs.get( "compression", "none" )
    kw_load_addr = kwargs.get( "load_addr", 0 )
    kw_entry_point = kwargs.get( "entry_point", kw_load_addr )
    kw_name = kwargs.get( "name", "NoName" )
    kw_type = img_type

    if isinstance(source, str):
        kw_source = source
        if None == kw_destination:
            kw_destination = kw_source + ".uimg"
    elif isinstance(source, tuple) or isinstance(source, list):
        for source_item in source:
            kw_source += source_item + ":"
            kw_source = kw_source[:-1]
            if None == kw_destination:
                logger.error( "'destination' must be defined" )
                return False
            if "multi" != kw_type and 1 < len(source):
                logger.warning( "image type could be only 'multi' for multiple files" )
            kw_type = "multi"
        else:
            logger.error( "undefined 'source' type" )
            return False

    return mkimage_tool_path + \
        " -A " + arch + \
        " -O " + kw_os_type + \
        " -C " + kw_compression + \
        " -T " + kw_type + \
        " -a " + kw_load_addr + \
        " -e " + kw_entry_point + \
        " -n " + kw_name + \
        " -d " + kw_source + \
        " " + kw_destination
# def mkimage

def bootconfig_command( bootconfig_tool_path: str, initrd: str, **kwargs ):
    kw_clear = kwargs.get( "clear", False )
    kw_add = kwargs.get( "add", None )
    kw_show = kwargs.get( "show", True )

    command = ""

    if True == kw_clear:
        command += f"{bootconfig_tool_path} -d {initrd}; "

    if None != kw_add:
        command += f"{bootconfig_tool_path} -a {kw_add} {initrd}; "

    if True == kw_show:
        command += f"{bootconfig_tool_path} -l {initrd};"

    return command
# def bootconfig_command

def create_android_boot_image_command( mkbootimg_tool_path: str, **kwargs ):
      kw_header_version = kwargs.get( "header_version", "2" )
      kw_os_version = kwargs.get( "os_version", "12.0.0" )
      kw_os_patch_level = kwargs.get( "os_patch_level", "2022-06" )
      kw_out = kwargs.get( "out" )
      kw_kernel = kwargs.get( "kernel", None )
      kw_ramdisk = kwargs.get( "ramdisk", None )
      kw_dtb = kwargs.get( "dtb", None )
      kw_cmdline = kwargs.get( "cmdline", None )
      kw_base = kwargs.get( "base", None )
      kw_kernel_offset = kwargs.get( "kernel_offset", None )
      kw_ramdisk_offset = kwargs.get( "ramdisk_offset", None )
      kw_dtb_offset = kwargs.get( "dtb_offset", None )

      command: str = mkbootimg_tool_path
      command += f" --header_version {kw_header_version}"
      command += f" --os_version {kw_os_version}"
      command += f" --os_patch_level {kw_os_patch_level}"
      command += f" --kernel {kw_kernel}"
      command += f" --ramdisk {kw_ramdisk}"
      if None != kw_dtb:
         command += f" --dtb {kw_dtb}"
      if None != kw_cmdline:
         command += f" --cmdline \"{kw_cmdline}\""
      if None != kw_base:
         command += f" --base {kw_base}"
      if None != kw_kernel_offset:
         command += f" --kernel_offset {kw_kernel_offset}"
      if None != kw_ramdisk_offset:
         command += f" --ramdisk_offset {kw_ramdisk_offset}"
      if None != kw_dtb_offset:
         command += f" --dtb_offset {kw_dtb_offset}"
      command += f" --out {kw_out}"

      return command
   # def create_android_boot_image_command

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

# parses kernel cmd line key value pair
def parse_kernel_cmdline_next_param(start_index: int, input_string: str):

    result_index = 0
    result_param_name = ""
    result_value = ""

    i = 0
    equals = 0
    in_quote = False
    quoted = False

    str_index = start_index
    str_length = len(input_string)

    if input_string[str_index] == '"':
        str_index += 1
        in_quote = 1
        quoted = True

    i = str_index

    while i < str_length:
        if input_string[i] == ' ' and not in_quote:
            break
        if equals == 0:
            if input_string[i] == '=':
                equals = i

        if input_string[i] == '"':
            in_quote = not in_quote

        i += 1

    result_param_name_start_index = str_index
    result_param_name_end_index = equals
    result_param_name = input_string[result_param_name_start_index:result_param_name_end_index]

    #logger.info("result_param_name - '" + result_param_name + "'")

    result_value_start_index = 0
    result_value_end_index = 0

    if not equals:
        result_value = None
    else:
        result_value_start_index = equals + 1

        # Don't include quotes in value.
        if input_string[result_value_start_index] == '"':
            result_value_start_index += 1

    if quoted and input_string[i-1] == '"':
        result_value_end_index = i-1
    else:
        result_value_end_index = i

    str_index = i

    result_value = input_string[result_value_start_index:result_value_end_index]

    #logger.info("result_value - '" + result_value + "'")

    while str_index < str_length:
        if input_string[str_index] == " ":
            #logger.info("Skipped space at index - " + str(str_index))
            str_index += 1
        else:
            #logger.info("No space at index - " + str(str_index) + ". Target char - '" + input_string[str_index] + "'")
            break

    result_index = str_index

    return (result_index, result_param_name, result_value)

def split_kernel_cmd_line(input_string: str):
    result_str = ""
    current_str_index = 0
    input_string_length = len(input_string)
    while current_str_index < input_string_length:
        (result_index, result_param_name, result_value) = parse_kernel_cmdline_next_param(current_str_index, input_string)

        #logger.info("result_index - '" + str(result_index) + "' " + \
        #    "result_param_name - '" + result_param_name + "' " \
        #    "result_value - '" + result_value + "'")

        result_str += result_param_name

        if result_value:
            result_str += "=\""
            result_str += result_value + "\""

        if result_index < input_string_length:
            result_str += "\n"

        current_str_index = result_index

    return result_str
