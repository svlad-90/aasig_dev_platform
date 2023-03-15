'''
Created on Aug 22, 2022

@author: vladyslav_goncharuk
'''

from common.common import BaseAndroidTask
from paf.paf_impl import logger, CommunicationMode

class QemuTask(BaseAndroidTask):

    def __init__(self):
        super().__init__()

        self.KERNEL=f"{self.ANDROID_BUILD_PATH}/target/product/" + "${TARGET_DEVICE}_${QEMU_ARCH}/kernel"

        self.RAMDISK_IMAGE_OUT_DIR=f"{self.BUILD_IMAGES_DIR}/ramdisk"
        self.RAMDISK_IMAGE_OUT=f"{self.RAMDISK_IMAGE_OUT_DIR}/ramdisk.img"
        self.RAMDISK_IMAGE=f"{self.ANDROID_PRODUCT_PATH}/ramdisk.img"

        self.QEMU_SOURCE_DIR="${ROOT}/${ANDROID_DEPLOYMENT_DIR}/${SOURCE_DIR}/qemu"
        self.QEMU_BUILD_DIR="${ROOT}/${ANDROID_DEPLOYMENT_DIR}/${BUILD_DIR}/qemu"

    def _get_qemu_arch_type(self):
        return self.get_environment_param("QEMU_ARCH")

    def _get_qemu_path(self):

        prefix = ""

        if self.has_non_empty_environment_param("QEMU_PATH"):
            prefix = self.get_environment_param("QEMU_PATH") + "/"
        else:
            prefix = self.QEMU_BUILD_DIR + "/"

        arch_type = self._get_qemu_arch_type().lower()
        if "x86" == arch_type:
            return prefix + "qemu-system-x86_64"
        elif "x86_64" == arch_type:
            return prefix + "qemu-system-x86_64"
        elif "arm" == arch_type or "arm32" == arch_type:
            return prefix + "qemu-system-arm"
        elif "arm64" == arch_type or "aarch64" == arch_type:
            return prefix + "qemu-system-aarch64"

class qemu_install_prerequisites(QemuTask):

    def __init__(self):
        super().__init__()
        self.set_name(qemu_install_prerequisites.__name__)

    def execute(self):
        logger.info("Installing of the prerequisites ...")
        self.subprocess_must_succeed("sudo -S apt -y install autoconf gcc-aarch64-linux-gnu \
            libaio-dev libbluetooth-dev libbrlapi-dev libbz2-dev libcap-dev \
            libcap-ng-dev libcurl4-gnutls-dev libepoxy-dev libfdt-dev libgbm-dev \
            libgles2-mesa-dev libglib2.0-dev libibverbs-dev libjpeg8-dev liblzo2-dev \
            libncurses5-dev libnuma-dev librbd-dev librdmacm-dev libsasl2-dev libsdl1.2-dev \
            libsdl2-dev libseccomp-dev libsnappy-dev libssh2-1-dev libtool libusb-1.0-0 \
            libusb-1.0-0-dev libvde-dev libvdeplug-dev libvte-2.91-dev libxen-dev valgrind \
            xfslibs-dev xutils-dev zlib1g-dev")
        self.subprocess_must_succeed("sudo -S apt-get -y install libvirglrenderer-dev")
        self.subprocess_must_succeed("sudo -S apt -y install qemu-kvm libvirt-daemon-system \
            libvirt-clients bridge-utils")
        self.subprocess_must_succeed("sudo -S apt-get -y install mkbootimg")
        self.subprocess_must_succeed("sudo -S apt-get -y install android-sdk-libsparse-utils")

class qemu_run_android(QemuTask):
    def __init__(self):
        super().__init__()
        self.set_name(qemu_run_android.__name__)

    def execute(self):
        logger.info("Running qemu ...")

        qemu_execution_mode = self.get_environment_param("QEMU_EXECUTION_MODE").lower()

        if qemu_execution_mode == "u-boot":
            subcommand = "-bios ${QEMU_BIOS_PATH}"
        elif qemu_execution_mode == "initrd_kernel":
            subcommand = f"""-kernel {self.KERNEL} -append "{self.KERNEL_CMDLINE} {self.ANDROID_KERNEL_CMDLINE} {self.KERNEL_CMDLINE_DIGEST}" -initrd {self.RAMDISK_IMAGE_OUT}"""

        self.subprocess_must_succeed(self._get_qemu_path() + " " + subcommand + f""" -drive if=none,index=0,id=main,file={self.MAIN_IMAGE} -device virtio-blk-pci,modern-pio-notify=on,drive=main """ +
                                     f"{self.RUN_QEMU}",
                                     communication_mode = CommunicationMode.PIPE_OUTPUT)


class qemu_deploy_qemu(QemuTask):
    def __init__(self):
        super().__init__()
        self.set_name(qemu_deploy_qemu.__name__)

    def execute(self):

        self.subprocess_must_succeed(f"""mkdir -p {self.QEMU_SOURCE_DIR};
mkdir -p {self.QEMU_BUILD_DIR};

echo "Cloning QEMU from official GitHub repo ..."
cd {self.QEMU_SOURCE_DIR}
git clone https://gitlab.com/qemu-project/qemu.git || echo "Clone failed. Still proceeding ...";
cd {self.QEMU_SOURCE_DIR}/qemu
git checkout tags/v7.0.0
git reset --hard
git clean -f -d

echo "Cloning QEMU-fork, which contains virtio-snd functionality ..."
cd {self.QEMU_SOURCE_DIR}
git clone https://github.com/BK1603/QEMU-fork || echo "Clone failed. Still proceeding ...";

echo "Creating the patch ..."
cd {self.QEMU_SOURCE_DIR}/QEMU-fork
git diff 0cef06d18762374c94eb4d511717a4735d668a24 > ../virtio-snd.patch

echo "Applying the patch ..."
cd {self.QEMU_SOURCE_DIR}/qemu
git apply --reject --whitespace=fix ../virtio-snd.patch

echo "Fixing Kconfig.rej file ..."
echo -e "\n\
config VIRTIO_SND\n\
bool\n\
default y if PCI_DEVICES\n\
depends on PCI\n" >> hw/audio/Kconfig
rm -rf hw/audio/Kconfig.rej

echo "Fixing compilation errors ..."
printf '%s\n' '236m226' 'wq' | ed -s hw/audio/virtio-snd.c
printf '%s\n' '237m227' 'wq' | ed -s hw/audio/virtio-snd.c
printf '%s\n' '238m228' 'wq' | ed -s hw/audio/virtio-snd.c
printf '%s\n' '137m126' 'wq' | ed -s hw/audio/virtio-snd.c

cd {self.QEMU_BUILD_DIR}
{self.QEMU_SOURCE_DIR}/qemu/configure --enable-gtk
make """ + "-j${BUILD_SYSTEM_CORES_NUMBER}")