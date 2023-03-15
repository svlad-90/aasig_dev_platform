'''
Created on May 17, 2022

@author: vladyslav_goncharuk
'''

import time

from common.common import BaseAndroidTask
from paf.paf_impl import logger, CommunicationMode

class VTSDeploymentTask(BaseAndroidTask):

    def __init__(self):
        super().__init__()

class vts_deploy(VTSDeploymentTask):
    def __init__(self):
        super().__init__()
        self.set_name(vts_deploy.__name__)

    def execute(self):
        self.subprocess_must_succeed("sudo -S apt-get -y install python-dev python-protobuf "
                                     "protobuf-compiler python3-virtualenv python3-pip")

class vts_execute(VTSDeploymentTask):
    def __init__(self):
        super().__init__()
        self.set_name(vts_execute.__name__)

    def execute(self):

        # We should wait for suitable device
        attempt = 0
        max_attempt = 100
        sleep_timeout = 3

        attempt_successful = False

        while attempt < max_attempt:

            logger.info("Polling available devicesAttempt " + str(attempt))

            result = self.subprocess_must_succeed(f"cd {self.ANDROID_SOURCE_PATH} && . ./build/envsetup.sh; "
                        f"export OUT_DIR_COMMON_BASE={self.ANDROID_BUILD_DIR}; "
                        "lunch ${ANDROID_LUNCH_CONFIG} && vts-tradefed list devices",
                        communication_mode = CommunicationMode.PIPE_OUTPUT)

            if "emulator" in result:
                # Now we can run tests
                vts_module = ""

                if self.has_non_empty_environment_param("VTS_MODULE"):
                    vts_module = "-m ${VTS_MODULE} "

                self.subprocess_must_succeed(f"cd {self.ANDROID_SOURCE_PATH} && . ./build/envsetup.sh; "
                    f"export OUT_DIR_COMMON_BASE={self.ANDROID_BUILD_DIR}; "
                    "lunch ${ANDROID_LUNCH_CONFIG} && vts-tradefed run vts " + vts_module + "-l DEBUG",
                    communication_mode = CommunicationMode.PIPE_OUTPUT)
                attempt_successful = True
                break
            else:
                logger.info("Attempt " + str(attempt) + f" has failed. Will try again in {str(sleep_timeout)} seconds.")
                attempt = attempt + 1
                time.sleep(sleep_timeout)

        self.assertion(attempt_successful, "Expected 'attempt_successful' equal to 'True'")
