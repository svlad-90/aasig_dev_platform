'''
Created on Jan 21, 2022

@author: vladyslav_goncharuk
'''

from common.common import BaseAndroidTask
from asyncio.log import logger

class CuttlefishDeploymentTask(BaseAndroidTask):

    def __init__(self):
        super().__init__()

        self.CUTTLEFISH_PATH = "${ROOT}/${ANDROID_DEPLOYMENT_DIR}/${SOURCE_DIR}/${CUTTLEFISH_SUB_DIR}"

class cuttlefish_sync(CuttlefishDeploymentTask):

    def __init__(self):
        super().__init__()
        self.set_name(cuttlefish_sync.__name__)

    def execute(self):

        self.subprocess_must_succeed(f"mkdir -p {self.CUTTLEFISH_PATH}")

        self.subprocess_must_succeed("( cd ${ROOT}/${ANDROID_DEPLOYMENT_DIR}/${SOURCE_DIR} && "
            "git clone ${CUTTLEFISH_GIT_URL}) || "
            f"(cd {self.CUTTLEFISH_PATH} && git checkout main && git pull)")

        if self.has_non_empty_environment_param("CUTTLEFISH_COMMIT_ID"):
            self.subprocess_must_succeed(f"cd {self.CUTTLEFISH_PATH} && git checkout " + "${CUTTLEFISH_COMMIT_ID}")

class cuttlefish_build(CuttlefishDeploymentTask):

    def __init__(self):
        super().__init__()
        self.set_name(cuttlefish_build.__name__)

    def execute(self):

        self.subprocess_must_succeed(f"cd {self.CUTTLEFISH_PATH}; "
                                     "source docker/setup.sh; "
                                     "export ANDROID_PRODUCT_OUT=${ANDROID_PRODUCT_OUT}; "
                                     "export ANDROID_HOST_OUT=${ANDROID_HOST_OUT}; "
                                     "cf_docker_rm_all; ")

        self.subprocess_must_succeed(f"cd {self.CUTTLEFISH_PATH}/docker; ./build.sh --build_debs_only --rebuild_debs_verbose")

class cuttlefish_start(CuttlefishDeploymentTask):

    def __init__(self):
        super().__init__()
        self.set_name(cuttlefish_start.__name__)

    def execute(self):

        logger.info("In case of failure of this step check the content of the ANDROID_PRODUCT_OUT & ANDROID_HOST_OUT parameters.")
        logger.info("How to fill them in?")
        logger.info("Go to https://ci.android.com/.")
        logger.info("Select any specific aosp_cf_x86_64_phone artifacts build and download the following artifacts:")
        logger.info("- aosp_cf_x86_64_phone-img-xxxxxxx.zip")
        logger.info("- cvd-host_package.tar.gz ")
        logger.info("Place cvd-host_package.tar.gz to any folder and specify it as the ANDROID_HOST_OUT, without unpacking the archive.")
        logger.info("Place aosp_cf_x86_64_phone-img-xxxxxxx.zip to any folder, unpack it, and specify as ANDROID_PRODUCT_OUT")
        logger.info("Unfortunately it is quite hard to automate this download. So, currently it is a TODO task!")
        logger.info("As an alternative, you can specify the folders of the manually built AOSP:")
        logger.info("ANDROID_PRODUCT_OUT=/android_source_root_folder/out/target/product/vsoc_x86")
        logger.info("ANDROID_HOST_OUT=/android_source_root_folder/soong/host/linux-x86")

        self.subprocess_must_succeed(f"cd {self.CUTTLEFISH_PATH}; "
                                     "source docker/setup.sh; "
                                     "export ANDROID_PRODUCT_OUT=${ANDROID_PRODUCT_OUT}; "
                                     "export ANDROID_HOST_OUT=${ANDROID_HOST_OUT}; "
                                     "cf_docker_rm_all; ")

        self.subprocess_must_succeed(f"cd {self.CUTTLEFISH_PATH}; "
                                     "source docker/setup.sh; "
                                     "export ANDROID_PRODUCT_OUT=${ANDROID_PRODUCT_OUT}; "
                                     "export ANDROID_HOST_OUT=${ANDROID_HOST_OUT}; "
                                     "cf_docker_create -A -C ${CUTTLEFISH_DOCKER_CONTAINER_NAME}; ")

        self.subprocess_must_succeed(f"cd {self.CUTTLEFISH_PATH}; "
                                     "source docker/setup.sh; "
                                     "export ANDROID_PRODUCT_OUT=${ANDROID_PRODUCT_OUT}; "
                                     "export ANDROID_HOST_OUT=${ANDROID_HOST_OUT}; "
                                     "cf_start_${CUTTLEFISH_DOCKER_CONTAINER_NAME} ${CUTTLEFISH_PARAMS} -console=true")

class cuttlefish_stop(CuttlefishDeploymentTask):

    def __init__(self):
        super().__init__()
        self.set_name(cuttlefish_stop.__name__)

    def execute(self):

        self.subprocess_must_succeed(f"cd {self.CUTTLEFISH_PATH}; "
                             "source docker/setup.sh; "
                             "export ANDROID_PRODUCT_OUT=${ANDROID_PRODUCT_OUT}; "
                             "export ANDROID_HOST_OUT=${ANDROID_HOST_OUT}; "
                             "cf_stop_${CUTTLEFISH_DOCKER_CONTAINER_NAME}")

