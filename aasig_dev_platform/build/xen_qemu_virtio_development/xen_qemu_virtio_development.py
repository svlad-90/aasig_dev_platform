'''
Created on Nov 18, 2022

@author: vladyslav_goncharuk
'''

import os
from pathlib import Path
import re

from paf.paf_impl import Task, logger, CommunicationMode, ExecutionMode, SSHConnectionCache

minicom_dollar = "\\$$"

class XQVDBaseTask(Task):

    def __init__(self):
        super().__init__()

        self.SOURCE_PATH = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${SOURCE_DIR}/${BRANCH_DIR}"
        self.SOURCE_PATH_XEN = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${SOURCE_DIR}/${BRANCH_DIR}/xen"
        self.SOURCE_PATH_QEMU = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${SOURCE_DIR}/${BRANCH_DIR}/qemu"

        self.DOCKER_SOURCE_PATH = "/mnt/${SOURCE_DIR}/${BRANCH_DIR}"
        self.DOCKER_SOURCE_PATH_XEN = "/mnt/${SOURCE_DIR}/${BRANCH_DIR}/xen"
        self.DOCKER_SOURCE_PATH_QEMU = "/mnt/${SOURCE_DIR}/${BRANCH_DIR}/qemu"

        self.BUILD_PATH = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${BUILD_DIR}/${BRANCH_DIR}"
        self.BUILD_PATH_QEMU = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${BUILD_DIR}/${BRANCH_DIR}/qemu"

        self.DEPLOY_PATH = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${DEPLOY_DIR}/${BRANCH_DIR}"
        self.DEPLOY_PATH_QEMU = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${DEPLOY_DIR}/${BRANCH_DIR}/qemu"
        self.DEPLOY_PATH_QEMU_DEPS_LIBS = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${DEPLOY_DIR}/${BRANCH_DIR}/qemu/deps_libs"
        self.DEPLOY_PATH_EVTEST = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${DEPLOY_DIR}/${BRANCH_DIR}/evtest"

        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        self.XQVD_AUTOMATION_DIR = dir_path

        self.TEST_AUDIO_FILE_NAME = "test_audio.wav"
        self.TEST_AUDIO_FILE_PATH = self.XQVD_AUTOMATION_DIR + "/" + self.TEST_AUDIO_FILE_NAME

        self.VIRGL_LIB_NAME = "libvirglrenderer.so.1.4.2"
        self.VIRGL_LIB_PATH = self.XQVD_AUTOMATION_DIR + "/" + self.VIRGL_LIB_NAME

        self.LIBGL_LIB_NAME = "libGL.so.1.2.0"
        self.LIBGL_LIB_PATH = self.XQVD_AUTOMATION_DIR + "/" + self.LIBGL_LIB_NAME

        self.DOCKER_BUILD_PATH = "/mnt/${BUILD_DIR}/${BRANCH_DIR}"
        self.DOCKER_BUILD_PATH_QEMU = "/mnt/${BUILD_DIR}/${BRANCH_DIR}/qemu"
        self.DOCKER_PATH_EVTEST = "/usr/bin/evtest"

        self.DOCKER_DEPLOY_PATH = "/mnt/${DEPLOY_DIR}/${BRANCH_DIR}"
        self.DOCKER_DEPLOY_PATH_QEMU = "/mnt/${DEPLOY_DIR}/${BRANCH_DIR}/qemu"
        self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS = "/mnt/${DEPLOY_DIR}/${BRANCH_DIR}/qemu/deps_libs"
        self.DOCKER_DEPLOY_PATH_EVTEST = "/mnt/${DEPLOY_DIR}/${BRANCH_DIR}/evtest"

        self.DOWNLOAD_PATH = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${DOWNLOAD_DIR}/${BRANCH_DIR}"
        self.DEPLOY_PATH = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${DEPLOY_DIR}/${BRANCH_DIR}"

        self.SSH_KEYS_MARKERS_FOLDER = "${ROOT}/${XQVD_DEPLOYMENT_DIR}/${DEPLOY_DIR}/ssh_keys_markers"

        self.TARGET_DEVICE_SSH_KEY_FILENAME = os.getlogin() + "_${RPI_SSH_KEY_NAME}"
        self.TARGET_DEVICE_SSH_KEY_PATH = str(Path.home()) + f"/.ssh/" + os.getlogin() + "_${RPI_SSH_KEY_NAME}"

        self.RPI_STORAGE_FOLDER = "/dev/shm/" + os.getlogin()
        self.RPI_MINICOM_COMMANDS_FOLDER = self.RPI_STORAGE_FOLDER + "/commands"
        self.RPI_MINICOM_LOGIN_SH_FILE = self.RPI_MINICOM_COMMANDS_FOLDER + "/minicom_login_cmd.sh"
        self.RPI_MINICOM_SH_FILE = self.RPI_MINICOM_COMMANDS_FOLDER + "/minicom_cmd.sh"
        self.RPI_CAPTURE_FILE = self.RPI_MINICOM_COMMANDS_FOLDER + "/capture.txt"
        self.RPI_TMP_FOLDER_QEMU = self.RPI_STORAGE_FOLDER + "/qemu"
        self.RPI_TMP_FOLDER_QEMU_DEPS_LIBS = self.RPI_TMP_FOLDER_QEMU + "/deps_libs"
        self.RPI_TMP_FOLDER_EVTEST = self.RPI_STORAGE_FOLDER + "/evtest"
        self.RPI_TMP_FOLDER_TEST_AUDIO = self.RPI_STORAGE_FOLDER + "/audio"
        self.RPI_TMP_FILE_PATH_TEST_AUDIO = self.RPI_TMP_FOLDER_TEST_AUDIO + "/" + self.TEST_AUDIO_FILE_NAME

        self.RPI_TARGET_FOLDER_QEMU = "/srv/domd/usr/bin"
        self.RPI_TARGET_FOLDER_DOMD_LIBS = "/srv/domd/usr/lib"

        self.RPI_TARGET_FOLDER_DOMU_BINARIES = "/srv/domu/usr/bin"

        self.RPI_TARGET_FOLDER_DOMU_TEST_AUDIO = "/srv/domu/home/root"
        self.RPI_TARGET_FOLDER_DOMD_TEST_AUDIO = "/srv/domd/home/root"

    def _get_target_device_ssh_key_path_subsituted(self):
        return self.substitute_parameters(self.TARGET_DEVICE_SSH_KEY_PATH)

    def __escape_minicom_parameters(self, cmd):
        escaped_cmd = re.sub(r"\\(?=[^\$])", "\\\\\\\\\\\\\\\\\\\\\\\\", cmd, count = 1000)
        escaped_cmd = escaped_cmd.replace("\n", "\\\\\\\n").replace("\"", "\\\\\\\"").replace("^", "\\^")
        logger.info("Escaped minicom command - '" + escaped_cmd + "'")
        return escaped_cmd

    def configure_netowrk(self):
        self.xqvd_domd_ssh_command_must_succeed("sleep 5; brctl addif xenbr0 vif-emu; ifconfig vif-emu up")

########################################################

    def xqvd_ssh_command_must_succeed(self, cmd, timeout = 0,
                                      expected_return_codes = [0],
                                      substitute_params = True,
                                      exec_mode = ExecutionMode.COLLECT_DATA,
                                      jumphost = None):

        target_device_ip_address = self.get_environment_param("RPI_IP_ADDRESS")
        target_device_user_name = self.get_environment_param("RPI_USER_NAME")

        return self.ssh_command_must_succeed(cmd, target_device_ip_address, target_device_user_name, 22,
            key_filename = [self._get_target_device_ssh_key_path_subsituted()],
            passphrase = self.get_environment_param("RPI_USER_NAME"),
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode,
            jumphost = jumphost)

    def xqvd_exec_ssh_command(self,
                              cmd,
                              timeout = 0,
                              substitute_params = True,
                              exec_mode = ExecutionMode.COLLECT_DATA):

        target_device_ip_address = self.get_environment_param("RPI_IP_ADDRESS")
        target_device_user_name = self.get_environment_param("RPI_USER_NAME")

        return self.exec_ssh_command(cmd, target_device_ip_address, target_device_user_name, 22,
            key_filename = [self._get_target_device_ssh_key_path_subsituted()],
            passphrase = self.get_environment_param("RPI_USER_NAME"),
            timeout = timeout,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

########################################################

    def __get_login_cmd_xen(self, dom0_name, dom0_username, dom0_password, domain_name, domain_console_name, domain_username, domain_password):
        login_cmd = ""

        if dom0_name:

            login_cmd += "verbose off\\n\\nexpect {\\n"

            if dom0_username:
                login_cmd += "\\\"-" + self.substitute_parameters(dom0_name).lower() + " login:\\\" send " + dom0_username + "\\n"
            if dom0_password:
                login_cmd += "\\\"Password:\\\" send " + dom0_password + "\\n"
            login_cmd += "\\\"-" + self.substitute_parameters(dom0_name).lower() + ":\\\" break\\n}\\n\\n"

        if domain_name:

            login_cmd += "send xl console " + domain_name + "\\n\\n"

            login_cmd += "expect {\\n"

            if domain_username:
                login_cmd += "\\\"" + self.substitute_parameters(domain_console_name) + " login:\\\" send " + domain_username + "\\n"
            if domain_password:
                login_cmd += "\\\"Password:\\\" send " + domain_password + "\\n"
            login_cmd += "\\\"" + self.substitute_parameters(domain_console_name) + ":\\\" break\\n}\\n\\n"

        return login_cmd

    def __get_minicom_command_xen(self, cmd, domain, domain_console_name, domain_username, domain_password):
        cmd_escaped = self.__escape_minicom_parameters(cmd)

        minicom_command = f"rm -rf {self.RPI_MINICOM_COMMANDS_FOLDER} && " \
        f"mkdir -p {self.RPI_MINICOM_COMMANDS_FOLDER}; " \
        "echo -e \"" + self.__get_login_cmd_xen( "${RPI_DOM0_NAME}" if self.has_non_empty_environment_param("RPI_DOM0_NAME") else None ,
            "${RPI_DOM0_USERNAME}" if self.has_non_empty_environment_param("RPI_DOM0_USERNAME") else None ,
            "${RPI_DOM0_PASSWORD}" if self.has_non_empty_environment_param("RPI_DOM0_PASSWORD") else None ,
            domain,
            domain_console_name,
            domain_username,
            domain_password ) + \
        f"\" > {self.RPI_MINICOM_LOGIN_SH_FILE}; " \
        f"echo -e \"send stty rows 100 cols 500\\n\\nsend echo \\\\\\\"~~~mcs\\\\\\\"; {cmd_escaped}; RESULT=$$(echo \\$$?); echo \\\\\\\"~~~mce\\\\\\\"; " \
        f"echo \\\\\\\"~~~mcr - \\$$RESULT\\\\\\\";\\n\\n\"" \
        "expect {\\\\n" \
        "\\\"~~~mcr\\\" break" \
        "\\\\n}\\\\n\\\\n" \
        f"> {self.RPI_MINICOM_SH_FILE}; " \
        f"killall minicom > /dev/null 2>&1 && sleep 3; " \
        "printf \"\\003\" > ${RPI_MINICOM_USB}; " \
        "printf \"\\035\" > ${RPI_MINICOM_USB}; " \
        "printf \"\\003\" > ${RPI_MINICOM_USB}; " \
        "printf \"\\015\" > ${RPI_MINICOM_USB}; " \
        "{ while read -t 0 var < ${RPI_MINICOM_USB}; do continue; done; }; sleep 2;" \
        "{ sleep 1; while pgrep runscript > /dev/null; do printf \"\\015\" > ${RPI_MINICOM_USB}; sleep 1; done; } | " \
        "minicom -D ${RPI_MINICOM_USB} " + f"-S {self.RPI_MINICOM_LOGIN_SH_FILE} > /dev/null; " \
        "{ while pgrep runscript > /dev/null; do sleep 1; done; sleep 2; sync; } | " \
        "minicom -D ${RPI_MINICOM_USB} " + f"-S {self.RPI_MINICOM_SH_FILE} -C {self.RPI_CAPTURE_FILE} > /dev/null; " \
        "sed -n '/~~~mcs/, /~~~mce/{ /~~~mcs/! { /~~~mce/! p } }'" + f" {self.RPI_CAPTURE_FILE}; " \
        f"(exit \"$$(sed -r -n -e 's/^.*~~~mcr - ([0-9]+)/\\1/p' {self.RPI_CAPTURE_FILE})\")"

        return minicom_command

    def xqvd_xen_minicom_command_must_succeed(self,
        cmd,
        domain = None,
        domain_console_name = None,
        domain_username = None,
        domain_password = None,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_ssh_command_must_succeed(self.__get_minicom_command_xen(cmd, domain, domain_console_name, domain_username, domain_password),
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_exec_xen_minicom_command(self,
        cmd,
        domain = None,
        domain_console_name = None,
        domain_username = None,
        domain_password = None,
        timeout = 0,
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_exec_ssh_command(self.__get_minicom_command_xen(cmd, domain, domain_console_name, domain_username, domain_password),
            timeout = timeout,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_domd_minicom_command_must_succeed(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_xen_minicom_command_must_succeed(cmd,
            domain = "${RPI_DOMD_NAME}" if self.has_non_empty_environment_param("RPI_DOMD_NAME") else None ,
            domain_console_name = "${RPI_DOMD_CONSOLE_NAME}" if self.has_non_empty_environment_param("RPI_DOMD_CONSOLE_NAME") else None ,
            domain_username = "${RPI_DOMD_USERNAME}" if self.has_non_empty_environment_param("RPI_DOMD_USERNAME") else None ,
            domain_password = "${RPI_DOMD_PASSWORD}" if self.has_non_empty_environment_param("RPI_DOMD_PASSWORD") else None ,
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_domd_exec_minicom_command(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_exec_xen_minicom_command(cmd,
            domain = "${RPI_DOMD_NAME}" if self.has_non_empty_environment_param("RPI_DOMD_NAME") else None ,
            domain_console_name = "${RPI_DOMD_CONSOLE_NAME}" if self.has_non_empty_environment_param("RPI_DOMD_CONSOLE_NAME") else None ,
            domain_username = "${RPI_DOMD_USERNAME}" if self.has_non_empty_environment_param("RPI_DOMD_USERNAME") else None ,
            domain_password = "${RPI_DOMD_PASSWORD}" if self.has_non_empty_environment_param("RPI_DOMD_PASSWORD") else None ,
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_domd_ssh_command_must_succeed(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        target_device_ip_address = self.get_environment_param("RPI_DOMD_IP_ADDRESS")
        target_device_user_name = self.get_environment_param("RPI_DOMD_USERNAME")

        return self.ssh_command_must_succeed("source /etc/profile; " + cmd, target_device_ip_address, target_device_user_name, 22,
            key_filename = [self._get_target_device_ssh_key_path_subsituted()],
            passphrase = self.get_environment_param("RPI_USER_NAME"),
            timeout = timeout, expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_domd_exec_ssh_command(self,
                                   cmd,
                                   timeout = 0,
                                   substitute_params = True,
                                   exec_mode = ExecutionMode.COLLECT_DATA):

        target_device_ip_address = self.get_environment_param("RPI_DOMD_IP_ADDRESS")
        target_device_user_name = self.get_environment_param("RPI_DOMD_USERNAME")

        return self.exec_ssh_command("source /etc/profile; " + cmd, target_device_ip_address, target_device_user_name, 22,
            timeout = timeout, key_filename = [self._get_target_device_ssh_key_path_subsituted()],
            passphrase = self.get_environment_param("RPI_USER_NAME"),
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_domu_ssh_command_must_succeed(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        jumphost = SSHConnectionCache.getInstance().find_or_create_connection(self.get_environment_param("RPI_IP_ADDRESS"),
            self.get_environment_param("RPI_USER_NAME"),
            key_filename = [self._get_target_device_ssh_key_path_subsituted()],
            passphrase = self.get_environment_param("RPI_USER_NAME"))

        return self.ssh_command_must_succeed("source /etc/profile; " + cmd,
            host = self.get_environment_param("RPI_DOMD_IP_ADDRESS"),
            user = self.get_environment_param("RPI_DOMU_USERNAME"),
            port = int(self.get_environment_param("RPI_DOMU_SSH_PORT")),
            password = self.get_environment_param("RPI_DOMU_PASSWORD"),
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode,
            jumphost = jumphost)

    def xqvd_domu_exec_ssh_command(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        jumphost = SSHConnectionCache.getInstance().find_or_create_connection(self.get_environment_param("RPI_IP_ADDRESS"),
            self.get_environment_param("RPI_USER_NAME"),
            key_filename = [self._get_target_device_ssh_key_path_subsituted()],
            passphrase = self.get_environment_param("RPI_USER_NAME"))

        return self.exec_ssh_command("source /etc/profile; " + cmd,
            host = self.get_environment_param("RPI_DOMD_IP_ADDRESS"),
            user = self.get_environment_param("RPI_DOMU_USERNAME"),
            port = int(self.get_environment_param("RPI_DOMU_SSH_PORT")),
            password = self.get_environment_param("RPI_DOMU_PASSWORD"),
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode,
            jumphost = jumphost)

    def xqvd_dom0_minicom_command_must_succeed(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_xen_minicom_command_must_succeed(cmd,
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_dom0_exec_minicom_command(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_exec_xen_minicom_command(cmd,
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

########################################################

    def __expect_boot_interruption(self):
        expect_cmd = ""

        expect_cmd += "verbose off\\n\\nexpect {\\n"
        expect_cmd += "\\\"Hit any key to stop autoboot:\\\" send 1\\n"
        expect_cmd += "\\\"=>\\\" break\\n}\\n\\n"

        return expect_cmd

    def __get_minicom_command_uboot(self, cmd):
        cmd_escaped = self.__escape_minicom_parameters(cmd)

        minicom_command = f"rm -rf {self.RPI_MINICOM_COMMANDS_FOLDER} && " \
        f"mkdir -p {self.RPI_MINICOM_COMMANDS_FOLDER}; " \
        "echo -e \"" + self.__expect_boot_interruption() + \
        f"send stty rows 100 cols 500\\n\\nsend {cmd_escaped}\" > " \
        f"{self.RPI_MINICOM_SH_FILE}; " \
        "printf \"\\003\" > ${RPI_MINICOM_USB}; " \
        "printf \"\\035\" > ${RPI_MINICOM_USB}; " \
        "printf \"\\003\" > ${RPI_MINICOM_USB}; " \
        "printf \"\\015\" > ${RPI_MINICOM_USB}; " \
        "{ sleep 1; while pgrep runscript > /dev/null; do sleep 1; done; sleep 3; } | " \
        "minicom -D ${RPI_MINICOM_USB} " + f"-S {self.RPI_MINICOM_SH_FILE} -C {self.RPI_CAPTURE_FILE} > /dev/null;" \
        f"(exit \"0\")"

        return minicom_command

    def xqvd_uboot_minicom_command_must_succeed(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_ssh_command_must_succeed(self.__get_minicom_command_uboot(cmd),
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_exec_uboot_minicom_command(self,
        cmd,
        timeout = 0,
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_exec_ssh_command(self.__get_minicom_command_uboot(cmd),
            timeout = timeout,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

########################################################

    def __get_login_cmd_yocto(self):
        login_cmd = ""

        login_cmd += "verbose off\\n\\nsend stty rows 100 cols 500\\n\\nexpect {\\n"
        login_cmd += "\\\"${RPI_YOCTO_CONSOLE_NAME} login:\\\" send root\\n"
        login_cmd += "\\\"Password:\\\" send ${RPI_YOCTO_PASSWORD}\\n"
        login_cmd += "\\\"${RPI_YOCTO_USERNAME}@${RPI_YOCTO_CONSOLE_NAME}:\\\" break\\n}\\n\\n"

        return login_cmd

    def __get_minicom_command_yocto(self, cmd):
        cmd_escaped = self.__escape_minicom_parameters(cmd)

        minicom_command = f"rm -rf {self.RPI_MINICOM_COMMANDS_FOLDER} && " \
        f"mkdir -p {self.RPI_MINICOM_COMMANDS_FOLDER}; " \
        "echo -e \"" + self.__get_login_cmd_yocto() + \
        f"\" > {self.RPI_MINICOM_LOGIN_SH_FILE}; " \
        f"echo -e \"send stty rows 100 cols 500\\n\\nsend echo \\\\\\\"~~~mcs\\\\\\\"; {cmd_escaped}; RESULT=$$(echo \\$$?); echo \\\\\\\"~~~mce\\\\\\\"; " \
        f"echo \\\\\\\"~~~mcr - \\$$RESULT\\\\\\\";\\n\\n\"" \
        "expect {\\\\n" \
        "\\\"~~~mcr\\\" break" \
        "\\\\n}\\\\n\\\\n" \
        f"> {self.RPI_MINICOM_SH_FILE}; " \
        f"killall minicom > /dev/null 2>&1 && sleep 3; " \
        "printf \"\\003\" > ${RPI_MINICOM_USB}; " \
        "printf \"\\035\" > ${RPI_MINICOM_USB}; " \
        "printf \"\\003\" > ${RPI_MINICOM_USB}; " \
        "printf \"\\015\" > ${RPI_MINICOM_USB}; " \
        "{ while read -t 0 var < ${RPI_MINICOM_USB}; do continue; done; }; sleep 2;" \
        "{ sleep 1; while pgrep runscript > /dev/null; do printf \"\\015\" > ${RPI_MINICOM_USB}; sleep 1; done; } | " \
        "minicom -D ${RPI_MINICOM_USB} " + f"-S {self.RPI_MINICOM_LOGIN_SH_FILE} > /dev/null; " \
        "{ while pgrep runscript > /dev/null; do sleep 1; done; sleep 2; sync; } | " \
        "minicom -D ${RPI_MINICOM_USB} " + f"-S {self.RPI_MINICOM_SH_FILE} -C {self.RPI_CAPTURE_FILE} > /dev/null; " \
        "sed -n '/~~~mcs/, /~~~mce/{ /~~~mcs/! { /~~~mce/! p } }'" + f" {self.RPI_CAPTURE_FILE}; " \
        f"(exit \"$$(sed -r -n -e 's/^.*~~~mcr - ([0-9]+)/\\1/p' {self.RPI_CAPTURE_FILE})\")"
        return minicom_command

    def xqvd_yocto_minicom_command_must_succeed(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_ssh_command_must_succeed(self.__get_minicom_command_yocto(cmd),
            timeout = timeout,
            expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_exec_yocto_minicom_command(self,
        cmd,
        timeout = 0,
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        return self.xqvd_exec_ssh_command(self.__get_minicom_command_yocto(cmd),
            timeout = timeout,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_yocto_ssh_command_must_succeed(self,
        cmd,
        timeout = 0,
        expected_return_codes = [0],
        substitute_params = True,
        exec_mode = ExecutionMode.COLLECT_DATA):

        target_device_ip_address = self.get_environment_param("RPI_YOCTO_IP_ADDRESS")
        target_device_user_name = self.get_environment_param("RPI_YOCTO_USERNAME")
        target_device_password = self.get_environment_param("RPI_YOCTO_PASSWORD")

        return self.ssh_command_must_succeed(cmd, target_device_ip_address, target_device_user_name, 22,
            password = target_device_password,
            timeout = timeout, expected_return_codes = expected_return_codes,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

    def xqvd_yocto_exec_ssh_command(self,
                                   cmd,
                                   timeout = 0,
                                   substitute_params = True,
                                   exec_mode = ExecutionMode.COLLECT_DATA):

        target_device_ip_address = self.get_environment_param("RPI_YOCTO_IP_ADDRESS")
        target_device_user_name = self.get_environment_param("RPI_YOCTO_USERNAME")
        target_device_password = self.get_environment_param("RPI_YOCTO_PASSWORD")

        return self.exec_ssh_command(cmd, target_device_ip_address, target_device_user_name, 22,
            password = target_device_password,
            substitute_params = substitute_params,
            exec_mode = exec_mode)

########################################################

    def create_ssh_key(self):
        self.subprocess_must_succeed(f"if [ ! -f {self.TARGET_DEVICE_SSH_KEY_PATH} ]; then "
                                     f"ssh-keygen -f {self.TARGET_DEVICE_SSH_KEY_PATH} " + "-t rsa -N ${RPI_USER_NAME}; "
                                     f"expect -c \"spawn ssh-add {self.TARGET_DEVICE_SSH_KEY_PATH}; " +
                                     "expect \\\"Enter passphrase\\\"; send \\\"${RPI_USER_NAME}\\r\\\"; expect eof\"; fi;")

########################################################

class xqvd_create_folders(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_create_folders.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"mkdir -p {self.SOURCE_PATH}")
        self.subprocess_must_succeed(f"mkdir -p {self.BUILD_PATH}")
        self.subprocess_must_succeed(f"mkdir -p {self.DOWNLOAD_PATH}")
        self.subprocess_must_succeed(f"mkdir -p {self.DEPLOY_PATH}")

class xqvd_inject_docker_parameters_for_xen_and_qemu(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_inject_docker_parameters_for_xen_and_qemu.__name__)

    def execute(self):

        self.set_environment_param("DOCKERFILE_PATH", f"{self.XQVD_AUTOMATION_DIR}/Dockerfile_qemu_xen_build")

        branch_dir = self.substitute_parameters("${BRANCH_DIR}")

        xqvd_image_name = self.substitute_parameters("${XQVD_DOCKER_IMAGE_NAME}")
        self.set_environment_param("DOCKER_IMAGE_NAME", f"{xqvd_image_name}_xen_qemu:{branch_dir}")

        xqvd_container_name = self.substitute_parameters("${XQVD_DOCKER_CONTAINER_NAME}")
        self.set_environment_param("DOCKER_CONTAINER_NAME", f"{xqvd_container_name}_xen_qemu_{branch_dir}")

        mount_dir = self.substitute_parameters("${ROOT}/${XQVD_DEPLOYMENT_DIR}")
        self.set_environment_param("DOCKER_MOUNT_FOLDER", f"{mount_dir}")

class xqvd_clone_projects(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_clone_projects.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"( cd {self.SOURCE_PATH}; sudo -S rm -rf {self.SOURCE_PATH_XEN}; "
            "git clone ${XEN_GIT_URL}" + f" {self.SOURCE_PATH_XEN}" + " -b ${XEN_GIT_BRANCH} )")

        self.subprocess_must_succeed(f"( cd {self.SOURCE_PATH}; sudo -S rm -rf {self.SOURCE_PATH_QEMU}; "
            "git clone ${QEMU_GIT_URL}" + f" {self.SOURCE_PATH_QEMU}" + " -b ${QEMU_GIT_BRANCH} )")

class xqvd_configure_xen(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_configure_xen.__name__)

    def execute(self):

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_XEN};\"")

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"cd {self.DOCKER_SOURCE_PATH_XEN}; CC=aarch64-linux-gnu-gcc "
            f"./configure --disable-docs --prefix=/usr/local --disable-stubdom --libdir=/usr/lib "
            "--enable-systemd --with-system-qemu=/usr/bin/qemu-system-aarch64;\"")

class xqvd_build_xen(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_build_xen.__name__)

    def execute(self):

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"cd {self.DOCKER_SOURCE_PATH_XEN}; CC=aarch64-linux-gnu-gcc "
            "make debball -j${BUILD_SYSTEM_CORES_NUMBER}\"")

class xqvd_share_git_folders(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_share_git_folders.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/slirp; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/capstone; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/dtc; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/tests/fp/berkeley-softfloat-3; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/tests/fp/berkeley-testfloat-3; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/ui/keycodemapdb; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/meson; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_XEN};\"")

class xqvd_configure_qemu(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_configure_qemu.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"mkdir -p {self.BUILD_PATH_QEMU}")
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/slirp; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/capstone; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/dtc; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/tests/fp/berkeley-softfloat-3; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/tests/fp/berkeley-testfloat-3; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/ui/keycodemapdb; "
            f"git config --global --add safe.directory {self.DOCKER_SOURCE_PATH_QEMU}/meson;\"")

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"cd {self.DOCKER_BUILD_PATH_QEMU}; CC=aarch64-linux-gnu-gcc "
            f"{self.DOCKER_SOURCE_PATH_QEMU}/configure --enable-fdt --target-list=aarch64-softmmu "
            f"--extra-ldflags=\\\"-L{self.DOCKER_SOURCE_PATH_XEN}/dist/install/usr/lib -lxenctrl -lxendevicemodel -lxenevtchn -lxenforeignmemory "
            "-lxengnttab -lxenguest -lxenstore -lxencall -lxentoollog -lxentoolcore\\\" "
            f"--extra-cflags=\\\"-I{self.DOCKER_SOURCE_PATH_XEN}/dist/install/usr/local/include\\\" --enable-xen --disable-kvm --enable-opengl "
            "--disable-libudev --disable-xen-pci-passthrough --enable-virtfs --audio-drv-list='alsa,oss,pa' --enable-gtk "
            "--enable-sdl "
            "--enable-virglrenderer;\"")

class xqvd_build_qemu(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_build_qemu.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"mkdir -p {self.BUILD_PATH_QEMU}")
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"cd {self.DOCKER_BUILD_PATH_QEMU}; CC=aarch64-linux-gnu-gcc "
            "make -j${BUILD_SYSTEM_CORES_NUMBER}\"")

class xqvd_clean(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_clean.__name__)

    def execute(self):

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"cd {self.DOCKER_SOURCE_PATH_XEN}; CC=aarch64-linux-gnu-gcc "
           "make mrproper -j${BUILD_SYSTEM_CORES_NUMBER}\"")

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"cd {self.DOCKER_BUILD_PATH_QEMU}; CC=aarch64-linux-gnu-gcc "
            "make distclean -j${BUILD_SYSTEM_CORES_NUMBER}\"")

        self.subprocess_must_succeed(f"sudo -S rm -rf {self.DEPLOY_PATH}")
        self.subprocess_must_succeed(f"mkdir -p {self.DEPLOY_PATH}")

class xqvd_remove_project_folders(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_remove_project_folders.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"sudo -S rm -rf {self.SOURCE_PATH}")
        self.subprocess_must_succeed(f"sudo -S rm -rf {self.BUILD_PATH}")
        self.subprocess_must_succeed(f"sudo -S rm -rf {self.DOWNLOAD_PATH}")
        self.subprocess_must_succeed(f"sudo -S rm -rf {self.DEPLOY_PATH}")

class xqvd_deploy_built_files_on_local_machine(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_deploy_built_files_on_local_machine.__name__)

    def execute(self):

        self.subprocess_must_succeed(f"rm -rf {self.DEPLOY_PATH_QEMU}; mkdir -p {self.DEPLOY_PATH_QEMU}; mkdir -p {self.DEPLOY_PATH_QEMU_DEPS_LIBS}")

        self.subprocess_must_succeed(f"cp {self.BUILD_PATH_QEMU}/qemu-system-aarch64 {self.DEPLOY_PATH_QEMU}")

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \""

            f"cp /usr/lib/aarch64-linux-gnu/libnuma.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libnuma.so.1.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libncursesw.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libncursesw.so.6.2 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libtinfo.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libtinfo.so.6.2 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libiscsi.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libiscsi.so.7.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libaio.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libaio.so.1.0.1 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libibverbs.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libibverbs.so.1.8.28.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/librdmacm.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/librdmacm.so.1.2.28.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libnl-route-3.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libnl-route-3.so.200.26.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libnl-3.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libnl-3.so.200.26.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libSDL2.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0.10.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libX11.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libX11.so.6.3.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXext.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXext.so.6.4.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXcursor.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXcursor.so.1.0.2 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXinerama.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXinerama.so.1.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            "\"")

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \""

            f"cp /usr/lib/aarch64-linux-gnu/libXi.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXi.so.6.1.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXrandr.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXrandr.so.2.2.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXss.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXss.so.1.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXxf86vm.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXxf86vm.so.1.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libxcb.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libxcb.so.1.1.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXrender.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXrender.so.1.3.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXfixes.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXfixes.so.3.1.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXau.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXau.so.6.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXdmcp.a {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
            f"cp /usr/lib/aarch64-linux-gnu/libXdmcp.so.6.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libbsd.so.0.10.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libGLdispatch.so.0.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libGLX.so.0.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libatk-bridge-2.0.so.0.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXcomposite.so.1.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libXdamage.so.1.1.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libatspi.so.0.0.1 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            f"cp /usr/lib/aarch64-linux-gnu/libOpenGL.so.0.0.0 {self.DOCKER_DEPLOY_PATH_QEMU_DEPS_LIBS}/; "

            "\"")

        self.subprocess_must_succeed(f"cp {self.VIRGL_LIB_PATH} {self.DEPLOY_PATH_QEMU_DEPS_LIBS}/; "
                                     f"cp {self.LIBGL_LIB_PATH} {self.DEPLOY_PATH_QEMU_DEPS_LIBS}/; ")

class xqvd_fetch_domd_ip_address(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_fetch_domd_ip_address.__name__)

    def execute(self):

        if not self.has_non_empty_environment_param("RPI_DOMD_IP_ADDRESS"):
            output = self.xqvd_domd_minicom_command_must_succeed("ifconfig eth0 | awk '/inet addr/ {gsub(\"addr:\", \"\", " + \
                minicom_dollar + "2); print " + minicom_dollar + "2}'")
            self.set_environment_param("RPI_DOMD_IP_ADDRESS", output)

class xqvd_fetch_yocto_ip_address(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_fetch_yocto_ip_address.__name__)

    def execute(self):

        if not self.has_non_empty_environment_param("RPI_YOCTO_IP_ADDRESS"):
            output = self.xqvd_yocto_minicom_command_must_succeed("ifconfig eth0 | awk '/inet addr/ {gsub(\"addr:\", \"\", " + \
                minicom_dollar + "2); print " + minicom_dollar + "2}'")
            self.set_environment_param("RPI_YOCTO_IP_ADDRESS", output)

class xqvd_deploy_rpi_ssh_key(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_deploy_rpi_ssh_key.__name__)

    def execute(self):
        self.create_ssh_key()
        self.subprocess_must_succeed(f"mkdir -p {self.SSH_KEYS_MARKERS_FOLDER}")
        self.subprocess_must_succeed(self._wrap_command_with_file_marker_condition(f"{self.SSH_KEYS_MARKERS_FOLDER}" +
            "/${RPI_IP_ADDRESS}_" + f"{self.TARGET_DEVICE_SSH_KEY_FILENAME}_ssh_key_installed_marker",
            "if [ -z \"$$(ssh-keygen -F ${RPI_IP_ADDRESS})\" ]; "
            "then ssh-keyscan -H ${RPI_IP_ADDRESS} >> ~/.ssh/known_hosts; fi; "
            f"echo -n " + "${RPI_USER_NAME} " + f"password:; read -s password; " + "sshpass -p $${password} ssh-copy-id -f " +
            f"-i {self.TARGET_DEVICE_SSH_KEY_PATH} " + "${RPI_USER_NAME}@${RPI_IP_ADDRESS}", f"{self.TARGET_DEVICE_SSH_KEY_FILENAME}_ssh_key_installed"))

class xqvd_prepare_rpi(XQVDBaseTask):

    def __init__(self):
            super().__init__()
            self.set_name(xqvd_prepare_rpi.__name__)

    def execute(self):
        self.xqvd_ssh_command_must_succeed(f"sudo -S apt install -y sshpass expect")

class xqvd_deploy_domd_ssh_key(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_deploy_domd_ssh_key.__name__)

    def execute(self):
        self.create_ssh_key()
        self.subprocess_must_succeed(f"mkdir -p {self.SSH_KEYS_MARKERS_FOLDER}")
        self.subprocess_must_succeed(self._wrap_command_with_file_marker_condition(f"{self.SSH_KEYS_MARKERS_FOLDER}" +
            "/${RPI_DOMD_IP_ADDRESS}_" + f"{self.TARGET_DEVICE_SSH_KEY_FILENAME}_ssh_key_installed_marker",
            "if [ -z \"$$(ssh-keygen -F ${RPI_DOMD_IP_ADDRESS})\" ]; "
            "then ssh-keyscan -H ${RPI_DOMD_IP_ADDRESS} >> ~/.ssh/known_hosts; fi; "
            f"echo -n " + "${RPI_DOMD_USERNAME} " + f"password:; read -s password; " + "sshpass -p ${RPI_DOMD_PASSWORD} ssh-copy-id -f " +
            f"-i {self.TARGET_DEVICE_SSH_KEY_PATH} " + "${RPI_DOMD_USERNAME}@${RPI_DOMD_IP_ADDRESS}", f"{self.TARGET_DEVICE_SSH_KEY_FILENAME}_ssh_key_installed"))

class xqvd_reset_ssh_keys_installation(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_reset_ssh_keys_installation.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"rm -rf {self.SSH_KEYS_MARKERS_FOLDER}")

class xqvd_reboot_board(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_reboot_board.__name__)

    def execute(self):
        self.xqvd_ssh_command_must_succeed("/home/${RPI_USER_NAME}/bin/boff; sleep 3; /home/${RPI_USER_NAME}/bin/bon; sleep 30;")
        self.xqvd_dom0_minicom_command_must_succeed("echo \"Wait for startup ...\"")
        self.xqvd_domd_minicom_command_must_succeed("echo \"Wait for startup ...\"")

class xqvd_reboot_board_from_emmc(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_reboot_board_from_emmc.__name__)

    def execute(self):
        self.xqvd_ssh_command_must_succeed(f"killall minicom > /dev/null 2>&1 && sleep 3 || :;")
        self.xqvd_ssh_command_must_succeed("/home/${RPI_USER_NAME}/bin/boff; sleep 3; /home/${RPI_USER_NAME}/bin/bon;")
        self.xqvd_uboot_minicom_command_must_succeed("run bootcmd_emmc")
        self.xqvd_ssh_command_must_succeed("sleep 30")

class xqvd_reboot_board_from_yocto(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_reboot_board_from_yocto.__name__)

    def execute(self):
        self.xqvd_ssh_command_must_succeed(f"killall minicom > /dev/null 2>&1 && sleep 3 || :;")
        self.xqvd_ssh_command_must_succeed("/home/${RPI_USER_NAME}/bin/boff; sleep 3; /home/${RPI_USER_NAME}/bin/bon;")
        self.xqvd_uboot_minicom_command_must_succeed("run bootcmd_yocto")
        self.xqvd_ssh_command_must_succeed("sleep 30")

class xqvd_reboot_board_from_tftp(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_reboot_board_from_tftp.__name__)

    def execute(self):
        self.xqvd_ssh_command_must_succeed(f"killall minicom > /dev/null 2>&1 && sleep 3 || :;")
        self.xqvd_ssh_command_must_succeed("/home/${RPI_USER_NAME}/bin/boff; sleep 3; /home/${RPI_USER_NAME}/bin/bon;")
        self.xqvd_uboot_minicom_command_must_succeed("run bootcmd_tftp")
        self.xqvd_ssh_command_must_succeed("sleep 30")

class xqvd_deploy_qemu_on_rpi(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_deploy_qemu_on_rpi.__name__)

    def execute(self):

        self.xqvd_ssh_command_must_succeed(
            f"mkdir -p {self.RPI_TMP_FOLDER_QEMU}; "
            f"mkdir -p {self.RPI_TMP_FOLDER_QEMU_DEPS_LIBS};" )

        self.subprocess_must_succeed(
            f"rsync -avz -r --progress -e ssh {self.DEPLOY_PATH_QEMU}/qemu-system-aarch64 "
            "${RPI_USER_NAME}@${RPI_IP_ADDRESS}:" + f"{self.RPI_TMP_FOLDER_QEMU}/; "
            f"rsync -avz -r --progress -e ssh {self.DEPLOY_PATH_QEMU_DEPS_LIBS}/ "
            "${RPI_USER_NAME}@${RPI_IP_ADDRESS}:" + f"{self.RPI_TMP_FOLDER_QEMU_DEPS_LIBS}/;")

        self.xqvd_ssh_command_must_succeed(f"sudo cp -u {self.RPI_TMP_FOLDER_QEMU}/qemu-system-aarch64 {self.RPI_TARGET_FOLDER_QEMU}/; "
            f"sudo cp -r -u {self.RPI_TMP_FOLDER_QEMU_DEPS_LIBS}/* {self.RPI_TARGET_FOLDER_DOMD_LIBS}/; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnuma.so.1.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnuma.so.1.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnuma.so.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnuma.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnuma.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnuma.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libncursesw.so.6.2 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libncursesw.so.6; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libncursesw.so.6 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libncursesw.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libtinfo.so.6.2 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libtinfo.so.6; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libtinfo.so.6 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libtinfo.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libiscsi.so.7.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libiscsi.so.7.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libiscsi.so.7.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libiscsi.so.7; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libiscsi.so.7 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libiscsi.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libaio.so.1.0.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libaio.so.1.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libaio.so.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libaio.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libaio.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libaio.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libibverbs.so.1.8.28.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libibverbs.so.1.8.28; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libibverbs.so.1.8.28 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libibverbs.so.1.8; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libibverbs.so.1.8 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libibverbs.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libibverbs.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libibverbs.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/librdmacm.so.1.2.28.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/librdmacm.so.1.2.28; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/librdmacm.so.1.2.28 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/librdmacm.so.1.2; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/librdmacm.so.1.2 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/librdmacm.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/librdmacm.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/librdmacm.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-route-3.so.200.26.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-route-3.so.200.26; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-route-3.so.200.26 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-route-3.so.200; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-route-3.so.200 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-route-3.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-3.so.200.26.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-3.so.200.26; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-3.so.200.26 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-3.so.200; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-3.so.200 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libnl-3.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libSDL2-2.0.so.0.10.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libSDL2-2.0.so.0.10; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libSDL2-2.0.so.0.10 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libSDL2-2.0.so.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libSDL2-2.0.so.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libSDL2-2.0.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libX11.so.6.3.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libX11.so.6.3; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libX11.so.6.3 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libX11.so.6; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libX11.so.6 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libX11.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXext.so.6.4.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXext.so.6.4; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXext.so.6.4 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXext.so.6; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXext.so.6 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXext.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcursor.so.1.0.2 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcursor.so.1.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcursor.so.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcursor.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcursor.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcursor.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXinerama.so.1.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXinerama.so.1.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXinerama.so.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXinerama.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXinerama.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXinerama.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXi.so.6.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXi.so.6.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXi.so.6.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXi.so.6; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXi.so.6 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXi.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrandr.so.2.2.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrandr.so.2.2; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrandr.so.2.2 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrandr.so.2; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrandr.so.2 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrandr.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXss.so.1.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXss.so.1.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXss.so.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXss.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXss.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXss.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXxf86vm.so.1.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXxf86vm.so.1.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXxf86vm.so.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXxf86vm.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXxf86vm.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXxf86vm.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libxcb.so.1.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libxcb.so.1.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libxcb.so.1.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libxcb.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libxcb.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libxcb.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrender.so.1.3.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrender.so.1.3; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrender.so.1.3 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrender.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrender.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXrender.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXfixes.so.3.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXfixes.so.3.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXfixes.so.3.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXfixes.so.3; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXfixes.so.3 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXfixes.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXau.so.6.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXau.so.6.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXau.so.6.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXau.so.6; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXau.so.6 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXau.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdmcp.so.6.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdmcp.so.6.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdmcp.so.6.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdmcp.so.6; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdmcp.so.6 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdmcp.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libbsd.so.0.10.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libbsd.so.0.10; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libbsd.so.0.10 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libbsd.so.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libbsd.so.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libbsd.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libvirglrenderer.so.1.4.2 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libvirglrenderer.so.1.4; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libvirglrenderer.so.1.4 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libvirglrenderer.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libvirglrenderer.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libvirglrenderer.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGL.so.1.2.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGL.so.1.2; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGL.so.1.2 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGL.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGL.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGL.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLdispatch.so.0.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLdispatch.so.0.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLdispatch.so.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLdispatch.so.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLdispatch.so.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLdispatch.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLX.so.0.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLX.so.0.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLX.so.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLX.so.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLX.so.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libGLX.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatk-bridge-2.0.so.0.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatk-bridge-2.0.so.0.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatk-bridge-2.0.so.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatk-bridge-2.0.so.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatk-bridge-2.0.so.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatk-bridge-2.0.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcomposite.so.1.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcomposite.so.1.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcomposite.so.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcomposite.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcomposite.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXcomposite.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdamage.so.1.1.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdamage.so.1.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdamage.so.1.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdamage.so.1; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdamage.so.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libXdamage.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatspi.so.0.0.1 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatspi.so.0.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatspi.so.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatspi.so.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatspi.so.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libatspi.so; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libOpenGL.so.0.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libOpenGL.so.0.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libOpenGL.so.0.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libOpenGL.so.0; "
            f"sudo ln -sfn {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libOpenGL.so.0 {self.RPI_TARGET_FOLDER_DOMD_LIBS}/libOpenGL.so; "
            )

class xqvd_domd_ldconfig(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_domd_ldconfig.__name__)

    def execute(self):

        self.xqvd_domd_ssh_command_must_succeed("ldconfig;")

class xqvd_check_virtio_block_net_pci(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_check_virtio_block_net_pci.__name__)

    def execute(self):

        self.xqvd_dom0_minicom_command_must_succeed("xl destroy DomU", expected_return_codes=[0, 1])
        self.xqvd_dom0_minicom_command_must_succeed("xl create /etc/xen/domu.cfg && xl pause DomU && xl list")
        DomU_id = self.xqvd_dom0_minicom_command_must_succeed("xl list | awk '{ if (" + minicom_dollar + "1 == \"DomU\") print " + minicom_dollar + "2 }'")
        DomU_memory = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"memory =\" | sed -rne 's/^.*memory = ([0-9]+).*/\\1/p'")
        DomU_vcpus = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"vcpus =\" | sed -rne 's/^.*vcpus = ([0-9]+).*/\\1/p'")
        self.xqvd_domd_ssh_command_must_succeed("( killall qemu-system-aarch64 || : )")
        self.xqvd_domd_ssh_command_must_succeed("setsid qemu-system-aarch64 "
            f"-xen-domid {DomU_id} "
            "-xen-attach "
            "-nographic "
            "-M xenpv "
            f"-m {DomU_memory} "
            f"-smp {DomU_vcpus} "
            "-monitor /dev/null "
            "-serial /dev/null "
            "-parallel /dev/null "
            "-device virtio-net-pci,disable-legacy=on,iommu_platform=on,romfile=\"\",id=nic0,netdev=net0,mac=08:00:27:ff:cb:cf "
            "-netdev type=tap,id=net0,ifname=vif-emu,br=xenbr0,script=no,downscript=no "
            "-device virtio-blk-pci,scsi=off,disable-legacy=on,iommu_platform=on,drive=image "
            "-drive if=none,id=image,format=raw,file=/dev/mmcblk0p3")
        self.configure_netowrk()
        self.xqvd_dom0_minicom_command_must_succeed("xl unpause DomU")
        self.subprocess_must_succeed("sleep 10")

        output = self.xqvd_domu_ssh_command_must_succeed("lspci");

        if output.find('Virtio block device') == -1:
            self.fail("Block virtio PCI device not found on DomU!")

        if output.find('Virtio network device') == -1:
            self.fail("Network virtio PCI device not found on DomU!")

class xqvd_check_virtio_block_net_mmio(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_check_virtio_block_net_mmio.__name__)

    def execute(self):

        self.xqvd_dom0_minicom_command_must_succeed("xl destroy DomU", expected_return_codes=[0, 1])
        self.xqvd_dom0_minicom_command_must_succeed("xl create /etc/xen/domu.cfg && xl pause DomU && xl list")
        DomU_id = self.xqvd_dom0_minicom_command_must_succeed("xl list | awk '{ if (" + minicom_dollar + "1 == \"DomU\") print " + minicom_dollar + "2 }'")
        DomU_memory = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"memory =\" | sed -rne 's/^.*memory = ([0-9]+).*/\\1/p'")
        DomU_vcpus = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"vcpus =\" | sed -rne 's/^.*vcpus = ([0-9]+).*/\\1/p'")
        self.xqvd_domd_ssh_command_must_succeed("( killall qemu-system-aarch64 || : )")
        self.xqvd_domd_ssh_command_must_succeed("setsid qemu-system-aarch64 "
            f"-xen-domid {DomU_id} "
            "-xen-attach "
            "-nographic "
            "-M xenpv "
            f"-m {DomU_memory} "
            f"-smp {DomU_vcpus} "
            "-monitor /dev/null "
            "-serial /dev/null "
            "-parallel /dev/null "
            "-device virtio-net-device,iommu_platform=on,id=nic0,netdev=net0,mac=08:00:27:ff:cb:cf "
            "-netdev type=tap,id=net0,ifname=vif-emu,br=xenbr0,script=no,downscript=no "
            "-device virtio-blk-device,iommu_platform=on,drive=image "
            "-drive if=none,id=image,format=raw,file=/dev/mmcblk0p3 "
            "-global virtio-mmio.force-legacy=false")
        self.configure_netowrk()
        self.xqvd_dom0_minicom_command_must_succeed("xl unpause DomU")
        self.subprocess_must_succeed("sleep 10")

        device_number = "2001000"
        output = self.xqvd_domu_ssh_command_must_succeed("ls -la /sys/bus/platform/drivers/virtio-mmio | grep -i " + device_number + ".virtio || :");
        if output.find(f'{device_number}.virtio') == -1:
            self.fail(f"The expected '{device_number}.virtio' device not found on DomU!")

        device_number = "2001200"
        output = self.xqvd_domu_ssh_command_must_succeed("ls -la /sys/bus/platform/drivers/virtio-mmio | grep -i " + device_number + ".virtio || :");
        if output.find(f'{device_number}.virtio') == -1:
            self.fail(f"The expected '{device_number}.virtio' device not found on DomU!")

class xqvd_check_virtio_block_net_mmio_and_pci_combined(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_check_virtio_block_net_mmio_and_pci_combined.__name__)

    def execute(self):

        self.xqvd_dom0_minicom_command_must_succeed("xl destroy DomU", expected_return_codes=[0, 1])
        self.xqvd_dom0_minicom_command_must_succeed("xl create /etc/xen/domu.cfg && xl pause DomU && xl list")
        DomU_id = self.xqvd_dom0_minicom_command_must_succeed("xl list | awk '{ if (" + minicom_dollar + "1 == \"DomU\") print " + minicom_dollar + "2 }'")
        DomU_memory = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"memory =\" | sed -rne 's/^.*memory = ([0-9]+).*/\\1/p'")
        DomU_vcpus = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"vcpus =\" | sed -rne 's/^.*vcpus = ([0-9]+).*/\\1/p'")
        self.xqvd_domd_ssh_command_must_succeed("( killall qemu-system-aarch64 || : )")
        self.xqvd_domd_ssh_command_must_succeed("setsid qemu-system-aarch64 "
            f"-xen-domid {DomU_id} "
            "-xen-attach "
            "-nographic "
            "-M xenpv "
            f"-m {DomU_memory} "
            f"-smp {DomU_vcpus} "
            "-monitor /dev/null "
            "-serial /dev/null "
            "-parallel /dev/null "
            "-device virtio-net-device,iommu_platform=on,id=nic0,netdev=net0,mac=08:00:27:ff:cb:cf "
            "-netdev type=tap,id=net0,ifname=vif-emu,br=xenbr0,script=no,downscript=no "
            "-device virtio-blk-pci,scsi=off,disable-legacy=on,iommu_platform=on,drive=image "
            "-drive if=none,id=image,format=raw,file=/dev/mmcblk0p3 "
            "-global virtio-mmio.force-legacy=false")

        self.configure_netowrk()
        self.xqvd_dom0_minicom_command_must_succeed("xl unpause DomU")
        self.subprocess_must_succeed("sleep 10")

        device_number = "2001200"
        output = self.xqvd_domu_ssh_command_must_succeed("ls -la /sys/bus/platform/drivers/virtio-mmio | grep -i " + device_number + ".virtio || :");
        if output.find(f'{device_number}.virtio') == -1:
            self.fail(f"The expected '{device_number}.virtio' device not found on DomU!")

        output = self.xqvd_domu_ssh_command_must_succeed("lspci");
        if output.find('Virtio block device') == -1:
            self.fail("Block virtio PCI device not found on DomU!")

class xqvd_check_virtio_console_pci(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_check_virtio_console_pci.__name__)

    def execute(self):

        self.xqvd_dom0_minicom_command_must_succeed("xl destroy DomU", expected_return_codes=[0, 1])
        self.xqvd_dom0_minicom_command_must_succeed("xl create /etc/xen/domu.cfg && xl pause DomU && xl list")
        DomU_id = self.xqvd_dom0_minicom_command_must_succeed("xl list | awk '{ if (" + minicom_dollar + "1 == \"DomU\") print " + minicom_dollar + "2 }'")
        DomU_memory = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"memory =\" | sed -rne 's/^.*memory = ([0-9]+).*/\\1/p'")
        DomU_vcpus = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"vcpus =\" | sed -rne 's/^.*vcpus = ([0-9]+).*/\\1/p'")
        self.xqvd_domd_ssh_command_must_succeed("( killall qemu-system-aarch64 || : )")

        pipe_path = "/tmp/virtio_console"

        self.xqvd_domd_ssh_command_must_succeed( "if ! [[ -p " + pipe_path + " ]]; then mkfifo " + pipe_path + "; fi; "
            "if ! [[ -p " + pipe_path + ".in ]]; then mkfifo " + pipe_path + ".in; fi; "
            "if ! [[ -p " + pipe_path + ".out ]]; then mkfifo " + pipe_path + ".out; fi; ")
        self.xqvd_domd_ssh_command_must_succeed("setsid qemu-system-aarch64 "
            f"-xen-domid {DomU_id} "
            "-xen-attach "
            "-nographic "
            "-M xenpv "
            f"-m {DomU_memory} "
            f"-smp {DomU_vcpus} "
            "-monitor /dev/null "
            "-device virtio-net-pci,disable-legacy=on,iommu_platform=on,romfile=\"\",id=nic0,netdev=net0,mac=08:00:27:ff:cb:cf "
            "-netdev type=tap,id=net0,ifname=vif-emu,br=xenbr0,script=no,downscript=no "
            "-device virtio-blk-pci,scsi=off,disable-legacy=on,iommu_platform=on,drive=image "
            "-drive if=none,id=image,format=raw,file=/dev/mmcblk0p3 "
            "-device virtio-serial-pci,disable-legacy=on,iommu_platform=on "
            "-chardev pipe,id=virtio_console_chardev,path=" + pipe_path + " "
            "-device virtconsole,chardev=virtio_console_chardev,id=virtio_console ")

        self.configure_netowrk()
        self.xqvd_dom0_minicom_command_must_succeed("xl unpause DomU")
        self.subprocess_must_succeed("sleep 10")

        output = self.xqvd_domu_ssh_command_must_succeed("lspci");
        if output.find('Virtio console') == -1:
            self.fail("Virtio console PCI device not found on DomU!")

        test_str = "Virtio console test!"

        self.xqvd_domd_ssh_command_must_succeed("echo \"" + test_str + "\" > " + pipe_path + ".in")
        output = self.xqvd_domu_ssh_command_must_succeed("head -n 1 /dev/hvc1")

        if output.find(test_str) == -1:
            self.fail("Expected output - '" + test_str + "'. Actual output - '" + output + "'.")
        else:
            logger.info("Test passed! Expected output '" + output + "' was found on the DomU side.")
            logger.info("Data was successfully passed through the virtio console from host to the guest.")

class xqvd_deploy_evtest(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_deploy_evtest.__name__)

    def execute(self):

        self.subprocess_must_succeed(f"rm -rf {self.DEPLOY_PATH_EVTEST}; mkdir -p {self.DEPLOY_PATH_EVTEST}")

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \""

            f"cp {self.DOCKER_PATH_EVTEST} {self.DOCKER_DEPLOY_PATH_EVTEST}/; "

            "\"")

        self.xqvd_ssh_command_must_succeed(f"mkdir -p {self.RPI_TMP_FOLDER_EVTEST};")

        self.subprocess_must_succeed(
            f"rsync --update -avz -r --progress -e ssh {self.DEPLOY_PATH_EVTEST}/evtest "
            "${RPI_USER_NAME}@${RPI_IP_ADDRESS}:" + f"{self.RPI_TMP_FOLDER_EVTEST}/;")

        self.xqvd_ssh_command_must_succeed(f"sudo cp -u {self.RPI_TMP_FOLDER_EVTEST}/evtest {self.RPI_TARGET_FOLDER_DOMU_BINARIES}/")

class xqvd_check_virtio_input(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_check_virtio_input.__name__)

    def execute(self):

        self.xqvd_dom0_minicom_command_must_succeed("xl destroy DomU", expected_return_codes=[0, 1])
        self.xqvd_dom0_minicom_command_must_succeed("xl create /etc/xen/domu.cfg && xl pause DomU && xl list")
        DomU_id = self.xqvd_dom0_minicom_command_must_succeed("xl list | awk '{ if (" + minicom_dollar + "1 == \"DomU\") print " + minicom_dollar + "2 }'")
        DomU_memory = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"memory =\" | sed -rne 's/^.*memory = ([0-9]+).*/\\1/p'")
        DomU_vcpus = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"vcpus =\" | sed -rne 's/^.*vcpus = ([0-9]+).*/\\1/p'")
        self.xqvd_domd_ssh_command_must_succeed("( killall qemu-system-aarch64 || : )")

        monitor_telnet_address = "127.0.0.1:12345"

        self.xqvd_domd_ssh_command_must_succeed("setsid qemu-system-aarch64 "
            f"-xen-domid {DomU_id} "
            "-xen-attach "
            "-nographic "
            "-M xenpv "
            f"-m {DomU_memory} "
            f"-smp {DomU_vcpus} "
            f"-monitor telnet:{monitor_telnet_address},server,nowait "
            "-device virtio-net-pci,disable-legacy=on,iommu_platform=on,romfile=\"\",id=nic0,netdev=net0,mac=08:00:27:ff:cb:cf "
            "-netdev type=tap,id=net0,ifname=vif-emu,br=xenbr0,script=no,downscript=no "
            "-device virtio-blk-pci,scsi=off,disable-legacy=on,iommu_platform=on,drive=image "
            "-drive if=none,id=image,format=raw,file=/dev/mmcblk0p3 "
            "-device virtio-keyboard-pci,id=kbd0,serial=virtio-keyboard,disable-legacy=on,iommu_platform=on ")

        self.configure_netowrk()
        self.xqvd_dom0_minicom_command_must_succeed("xl unpause DomU")
        self.subprocess_must_succeed("sleep 10")

        output = self.xqvd_domu_ssh_command_must_succeed("lspci")
        if output.find('Virtio input') == -1:
            self.fail("Virtio input PCI device not found on DomU!")

        self.xqvd_domd_ssh_command_must_succeed("( killall telnet || : )")
        self.xqvd_domd_ssh_command_must_succeed("{ sleep 2; echo -e \"sendkey z 20000\\n\"; sleep 2;} | telnet " + monitor_telnet_address)

        self.xqvd_domu_ssh_command_must_succeed("ldconfig")
        self.xqvd_domu_ssh_command_must_succeed("evtest --query /dev/input/event0 EV_KEY KEY_Z", expected_return_codes = [10])
        self.xqvd_domd_ssh_command_must_succeed("( killall telnet || : )")

class xqvd_inject_docker_parameters_for_kernel(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_inject_docker_parameters_for_kernel.__name__)

    def execute(self):

        self.set_environment_param("DOCKERFILE_PATH", f"{self.XQVD_AUTOMATION_DIR}/Dockerfile_kernel_build")

        branch_dir = self.substitute_parameters("${BRANCH_DIR}")

        xqvd_image_name = self.substitute_parameters("${XQVD_DOCKER_IMAGE_NAME}")
        self.set_environment_param("DOCKER_IMAGE_NAME", f"{xqvd_image_name}_kernel:{branch_dir}")

        xqvd_container_name = self.substitute_parameters("${XQVD_DOCKER_CONTAINER_NAME}")
        self.set_environment_param("DOCKER_CONTAINER_NAME", f"{xqvd_container_name}_kernel_{branch_dir}")

        mount_dir = self.substitute_parameters("${ROOT}/${XQVD_DEPLOYMENT_DIR}")
        self.set_environment_param("DOCKER_MOUNT_FOLDER", f"{mount_dir}")

        self.set_environment_param("DOCKER_CREATE_ADDITIONAL_PARAMS",
            "-v " + str(Path.home()) + "/.ssh:/home/builder/.ssh " + \
	        "-v " + str(Path.home()) + "/.gitconfig:/home/builder/.gitconfig")

class xqvd_check_virtio_snd(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_check_virtio_snd.__name__)

    def execute(self):

        self.xqvd_dom0_minicom_command_must_succeed("xl destroy DomU", expected_return_codes=[0, 1])
        self.xqvd_dom0_minicom_command_must_succeed("xl create /etc/xen/domu.cfg && xl pause DomU && xl list")
        DomU_id = self.xqvd_dom0_minicom_command_must_succeed("xl list | awk '{ if (" + minicom_dollar + "1 == \"DomU\") print " + minicom_dollar + "2 }'")
        DomU_memory = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"memory =\" | sed -rne 's/^.*memory = ([0-9]+).*/\\1/p'")
        DomU_vcpus = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"vcpus =\" | sed -rne 's/^.*vcpus = ([0-9]+).*/\\1/p'")
        self.xqvd_domd_ssh_command_must_succeed("( killall qemu-system-aarch64 || : )")

        monitor_telnet_address = "127.0.0.1:12345"

        self.xqvd_domd_ssh_command_must_succeed("setsid qemu-system-aarch64 "
            f"-xen-domid {DomU_id} "
            "-xen-attach "
            "-nographic "
            "-M xenpv "
            f"-m {DomU_memory} "
            f"-smp {DomU_vcpus} "
            f"-monitor telnet:{monitor_telnet_address},server,nowait "
            "-device virtio-net-pci,disable-legacy=on,iommu_platform=on,romfile=\"\",id=nic0,netdev=net0,mac=08:00:27:ff:cb:cf "
            "-netdev type=tap,id=net0,ifname=vif-emu,br=xenbr0,script=no,downscript=no "
            "-device virtio-blk-pci,scsi=off,disable-legacy=on,iommu_platform=on,drive=image "
            "-drive if=none,id=image,format=raw,file=/dev/mmcblk0p3 "
            "-audiodev alsa,id=snd0,out.dev=default "
            "-device virtio-snd-pci,audiodev=snd0,disable-legacy=on,iommu_platform=on "
            "-global virtio-mmio.force-legacy=false" )

        self.configure_netowrk()
        self.xqvd_dom0_minicom_command_must_succeed("xl unpause DomU")
        self.subprocess_must_succeed("sleep 10")

        output = self.xqvd_domu_ssh_command_must_succeed("lspci")
        if output.find('Multimedia audio controller') == -1:
            self.fail("Virtio sound PCI device not found on DomU!")
        else:
            logger.info("Virtio sound PCI device is available ( as expected )")

        self.xqvd_domu_ssh_command_must_succeed("killall -s 9 speaker-test && sleep 3 || :")

        self.xqvd_domu_ssh_command_must_succeed(f"setsid speaker-test -P 2")

        self.xqvd_domd_ssh_command_must_succeed("( killall telnet || : )")
        self.xqvd_domd_ssh_command_must_succeed("rm -rf /tmp/qemu_captured.wav; { sleep 2; echo -e "
            "\"wavcapture /tmp/qemu_captured.wav snd0\\n\"; sleep 20;} "
            "| telnet " + monitor_telnet_address)
        self.xqvd_domd_ssh_command_must_succeed("{ sleep 2; echo -e \"stopcapture 0\"; sleep 2;} | telnet " + monitor_telnet_address)

        self.xqvd_domu_ssh_command_must_succeed("killall -s 9 speaker-test && sleep 3 || :")

        self.subprocess_must_succeed("scp ${RPI_DOMD_USERNAME}@${RPI_DOMD_IP_ADDRESS}:/tmp/qemu_captured.wav " + f"{self.DEPLOY_PATH}/qemu_captured.wav")

        self.subprocess_must_succeed(f"xdg-open {self.DEPLOY_PATH}/qemu_captured.wav",
            communication_mode = CommunicationMode.PIPE_OUTPUT)

class xqvd_check_snd(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_check_snd.__name__)

    def execute(self):

        logger.info("Testing audio inside DomD")

        self.xqvd_domd_ssh_command_must_succeed("killall -s 9 speaker-test && sleep 3 || :")

        self.xqvd_domd_ssh_command_must_succeed(f"setsid speaker-test")

        output = self.xqvd_domd_ssh_command_must_succeed("pactl list short sinks | grep \"RUNNING\"")

        if not output:
            self.fail("Audio was started on DomD, but it is not playing!")
        else:
            logger.info("Audio was started on DomD and is playing ( as expected )")

        self.xqvd_domd_ssh_command_must_succeed("killall -s 9 speaker-test && sleep 3 || :")

        output = self.xqvd_domd_ssh_command_must_succeed("pactl list short sinks | grep \"RUNNING\"", expected_return_codes=[0, 1])

        if output:
            self.fail("Audio was sopped on DomD, but it is still playing!")
        else:
            logger.info("Audio was stopped on DomD and is not playing ( as expected )")

        logger.info("Testing audio inside DomU")

        self.xqvd_domu_ssh_command_must_succeed("killall -s 9 speaker-test && sleep 3 || :")

        self.xqvd_domu_ssh_command_must_succeed(f"setsid speaker-test")

        output = self.xqvd_domd_ssh_command_must_succeed("pactl list short sinks | grep \"RUNNING\"")

        if not output:
            self.fail("Audio was started on DomU, but it is not playing inside DomD!")
        else:
            logger.info("Audio was started on DomU and is playing inside DomD ( as expected )")

        self.xqvd_domu_ssh_command_must_succeed("killall -s 9 speaker-test && sleep 3 || :")

        output = self.xqvd_domd_ssh_command_must_succeed("pactl list short sinks | grep \"RUNNING\"", expected_return_codes=[0, 1])

        if output:
            self.fail("Audio was sopped on DomU, but it is still playing inside DomD!")
        else:
            logger.info("Audio was stopped on DomU and is not playing inside DomD ( as expected )")

class xqvd_check_virtio_gpu_pci(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_check_virtio_gpu_pci.__name__)

    def execute(self):

        self.xqvd_dom0_minicom_command_must_succeed("xl destroy DomU", expected_return_codes=[0, 1])
        self.xqvd_dom0_minicom_command_must_succeed("xl create /etc/xen/domu.cfg && xl pause DomU && xl list")
        DomU_id = self.xqvd_dom0_minicom_command_must_succeed("xl list | awk '{ if (" + minicom_dollar + "1 == \"DomU\") print " + minicom_dollar + "2 }'")
        DomU_memory = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"memory =\" | sed -rne 's/^.*memory = ([0-9]+).*/\\1/p'")
        DomU_vcpus = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"vcpus =\" | sed -rne 's/^.*vcpus = ([0-9]+).*/\\1/p'")
        self.xqvd_domd_ssh_command_must_succeed("( killall qemu-system-aarch64 || : )")

        self.xqvd_domd_ssh_command_must_succeed("export SDL_VIDEODRIVER=wayland; setsid qemu-system-aarch64 "
            f"-xen-domid {DomU_id} "
            "-xen-attach "
            "-M xenpv "
            f"-m {DomU_memory} "
            f"-smp {DomU_vcpus} "
            "-d guest_errors "
            "-monitor /dev/null "
            "-device virtio-net-pci,disable-legacy=on,iommu_platform=on,romfile=\"\",id=nic0,netdev=net0,mac=08:00:27:ff:cb:cf "
            "-netdev type=tap,id=net0,ifname=vif-emu,br=xenbr0,script=no,downscript=no "
            "-device virtio-blk-pci,scsi=off,disable-legacy=on,iommu_platform=on,drive=image "
            "-drive if=none,id=image,format=raw,file=/dev/mmcblk0p3 "
            "-device virtio-gpu-gl-pci,disable-legacy=on,iommu_platform=on "
            "-display sdl,gl=on "
            "-vga std "
            "-global virtio-mmio.force-legacy=false "
            "-device virtio-keyboard-pci,disable-legacy=on,iommu_platform=on" )

        self.configure_netowrk()
        self.xqvd_dom0_minicom_command_must_succeed("xl unpause DomU")
        self.subprocess_must_succeed("sleep 10")

        output = self.xqvd_domu_ssh_command_must_succeed("lspci")
        if output.find('Virtio GPU') == -1:
            self.fail("Virtio GPU PCI device not found on DomU!")
        else:
            logger.info("Virtio GPU PCI device is available ( as expected )")

class xqvd_check_virtio_gpu_mmio(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_check_virtio_gpu_mmio.__name__)

    def execute(self):

        self.xqvd_dom0_minicom_command_must_succeed("xl destroy DomU", expected_return_codes=[0, 1])
        self.xqvd_dom0_minicom_command_must_succeed("xl create /etc/xen/domu.cfg && xl pause DomU && xl list")
        DomU_id = self.xqvd_dom0_minicom_command_must_succeed("xl list | awk '{ if (" + minicom_dollar + "1 == \"DomU\") print " + minicom_dollar + "2 }'")
        DomU_memory = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"memory =\" | sed -rne 's/^.*memory = ([0-9]+).*/\\1/p'")
        DomU_vcpus = self.xqvd_dom0_minicom_command_must_succeed("cat /etc/xen/domu.cfg | grep \"vcpus =\" | sed -rne 's/^.*vcpus = ([0-9]+).*/\\1/p'")
        self.xqvd_domd_ssh_command_must_succeed("( killall qemu-system-aarch64 || : )")

        self.xqvd_domd_ssh_command_must_succeed("export SDL_VIDEODRIVER=wayland; setsid qemu-system-aarch64 "
            f"-xen-domid {DomU_id} "
            "-xen-attach "
            "-M xenpv "
            f"-m {DomU_memory} "
            f"-smp {DomU_vcpus} "
            "-d guest_errors "
            "-monitor /dev/null "
            "-device virtio-net-pci,disable-legacy=on,iommu_platform=on,romfile=\"\",id=nic0,netdev=net0,mac=08:00:27:ff:cb:cf "
            "-netdev type=tap,id=net0,ifname=vif-emu,br=xenbr0,script=no,downscript=no "
            "-device virtio-blk-pci,scsi=off,disable-legacy=on,iommu_platform=on,drive=image "
            "-drive if=none,id=image,format=raw,file=/dev/mmcblk0p3 "
            "-device virtio-gpu-gl-device,iommu_platform=on "
            "-display sdl,gl=on "
            "-vga std "
            "-global virtio-mmio.force-legacy=false "
            "-device virtio-keyboard-pci,disable-legacy=on,iommu_platform=on" )

        self.configure_netowrk()
        self.xqvd_dom0_minicom_command_must_succeed("xl unpause DomU")
        self.subprocess_must_succeed("sleep 10")

        device_number = "2001200"
        output = self.xqvd_domu_ssh_command_must_succeed("ls -la /sys/bus/platform/drivers/virtio-mmio | grep -i " + device_number + ".virtio || :");
        if output.find(f'{device_number}.virtio') == -1:
            self.fail(f"The expected '{device_number}.virtio' device not found on DomU!")

class xqvd_copy_file_to_the_rpi(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_copy_file_to_the_rpi.__name__)

    def execute(self):

        if self.has_non_empty_environment_param("XQVD_COPY_TO_RPI_BEFORE_COPY_HOOK"):
            self.xqvd_ssh_command_must_succeed(self.substitute_parameters("${XQVD_COPY_TO_RPI_BEFORE_COPY_HOOK}"))
            self.delete_environment_param("XQVD_COPY_TO_RPI_BEFORE_COPY_HOOK")

        self.subprocess_must_succeed(
            "rsync -avz -r --progress -e ssh ${XQVD_COPY_TO_RPI_SOURCE} "
            "${RPI_USER_NAME}@${RPI_IP_ADDRESS}:${XQVD_COPY_TO_RPI_DESTINATION};")
        self.delete_environment_param("XQVD_COPY_TO_RPI_SOURCE")
        self.delete_environment_param("XQVD_COPY_TO_RPI_DESTINATION")

        if self.has_non_empty_environment_param("XQVD_COPY_TO_RPI_AFTER_COPY_HOOK"):
            self.xqvd_ssh_command_must_succeed(self.substitute_parameters("${XQVD_COPY_TO_RPI_AFTER_COPY_HOOK}"))
            self.delete_environment_param("XQVD_COPY_TO_RPI_AFTER_COPY_HOOK")

class xqvd_flash_full_image_to_emmc(XQVDBaseTask):
    def __init__(self):
        super().__init__()
        self.set_name(xqvd_flash_full_image_to_emmc.__name__)

    def execute(self):
        self.xqvd_yocto_ssh_command_must_succeed("dd conv=sparse if=/_images_/full.img of=/dev/mmcblk0 status=progress bs=1M;")
