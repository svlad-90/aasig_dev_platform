'''
Created on Jan 18, 2023

@author: vladyslav_goncharuk
'''

import os
from pathlib import Path

from paf.paf_impl import Task, logger, CommunicationMode, ExecutionMode

class moulin_base_task(Task):

    def __init__(self):
        super().__init__()

        self.DOWNLOAD_PATH = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_DOWNLOAD_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}"
        self.DOCKER_DOWNLOAD_PATH = "/mnt/${MOULIN_DOWNLOAD_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}"

        self.SOURCE_PATH = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_SOURCE_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}"
        self.DOCKER_SOURCE_PATH = "/mnt/${MOULIN_SOURCE_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}"

        self.BUILD_PATH = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_BUILD_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}"
        self.DOCKER_BUILD_PATH = "/mnt/${MOULIN_BUILD_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}"

        self.DEPLOY_PATH = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}"
        self.DEPLOY_PATH_FILTERED_DOT_GRAPH_RESULT = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/dependency-analysis/filtered-dot-graph/result"
        self.DEPLOY_PATH_WRITE_YOCTO_ENV_TO_FILE = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/dependency-analysis/write-yocto-env-to-file"

        self.DOCKER_DEPLOY_PATH = "/mnt/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}"
        self.DOCKER_DEPLOY_PATH_DEPENDENCY_ANALYSIS = "/mnt/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/dependency-analysis"
        self.DOCKER_DEPLOY_PATH_FILTERED_DOT_GRAPH_RESULT = "/mnt/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/dependency-analysis/filtered-dot-graph/result"
        self.DOCKER_DEPLOY_PATH_FILTERED_DOT_GRAPH_DOT_GRAPH = "/mnt/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/dependency-analysis/filtered-dot-graph/dot-graph"
        self.DOCKER_DEPLOY_PATH_ANALYZE_DEPENDENCY_DOT_GRAPH = "/mnt/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/dependency-analysis/analyze-dependency/dot-graph"
        self.DOCKER_DEPLOY_PATH_WRITE_YOCTO_ENV_TO_FILE = "/mnt/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/dependency-analysis/write-yocto-env-to-file"

        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        self.MOULIN_AUTOMATION_DIR = dir_path

        self.SOURCE_PATH_BUILD_CONFIG = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_SOURCE_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/build_config"
        self.DOCKER_SOURCE_PATH_BUILD_CONFIG = "/mnt/${MOULIN_SOURCE_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/build_config"

        self.DEPLOY_DOM0_PATH = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/upload_sw/tftp/dom0"
        self.DEPLOY_DOMD_PATH = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/upload_sw/nfs/domd"
        self.DEPLOY_XEN_PATH = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/upload_sw/tftp/xen"

        self.UPLOAD_FILES_DEPLOY_PATH = "${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}/${MOULIN_DEPLOY_DIR}/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}/${MOULIN_PRODUCT_GIT_BRANCH}/upload_files"

class moulin_create_folders(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_create_folders.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"mkdir -p {self.SOURCE_PATH}")
        self.subprocess_must_succeed(f"mkdir -p {self.BUILD_PATH}")
        self.subprocess_must_succeed(f"mkdir -p {self.DOWNLOAD_PATH}")
        self.subprocess_must_succeed(f"mkdir -p {self.DEPLOY_PATH}")

class moulin_inject_docker_parameters(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_inject_docker_parameters.__name__)

    def execute(self):

        self.set_environment_param("DOCKERFILE_PATH", f"{self.MOULIN_AUTOMATION_DIR}/Dockerfile")

        moulin_image_name = self.substitute_parameters("${MOULIN_DOCKER_IMAGE_NAME}")
        self.set_environment_param("DOCKER_IMAGE_NAME", f"{moulin_image_name}")

        moulin_container_name = self.substitute_parameters("${MOULIN_DOCKER_CONTAINER_NAME}")
        self.set_environment_param("DOCKER_CONTAINER_NAME", f"{moulin_container_name}")

        mount_dir = self.substitute_parameters("${MOULIN_ROOT}/${MOULIN_DEPLOYMENT_DIR}")
        self.set_environment_param("DOCKER_MOUNT_FOLDER", f"{mount_dir}")

class moulin_clone_build_config(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_clone_build_config.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"( cd {self.SOURCE_PATH}; sudo -S rm -rf {self.SOURCE_PATH_BUILD_CONFIG}; "
            "git clone ${MOULIN_PRODUCT_GIT_URL}" + f" {self.SOURCE_PATH_BUILD_CONFIG}" + " -b ${MOULIN_PRODUCT_GIT_BRANCH} )")

        if self.has_non_empty_environment_param("MOULIN_PRODUCT_GIT_COMMIT"):
            self.subprocess_must_succeed(f"cd {self.SOURCE_PATH_BUILD_CONFIG}; git checkout " + "${MOULIN_PRODUCT_GIT_COMMIT};")

class moulin_generate_ninja(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_generate_ninja.__name__)

    def execute(self):

        command = "docker exec -it ${DOCKER_CONTAINER_NAME} " \
        "bash -c \"" \
        f"cd {self.DOCKER_BUILD_PATH}; " \
        f"moulin {self.DOCKER_SOURCE_PATH_BUILD_CONFIG}" + "/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}${MOULIN_BUILD_CONFIGURATION_FILE_EXTENSION} " \
        "--MACHINE ${MOULIN_MACHINE}"

        if self.has_non_empty_environment_param("MOULIN_ADDITIONAL_PARAMETERS"):
            command += " ${MOULIN_ADDITIONAL_PARAMETERS}"

        command += "\""

        self.subprocess_must_succeed(command)

class moulin_build_project(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_build_project.__name__)

    def execute(self):

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"cd {self.DOCKER_BUILD_PATH}; "
            "ninja -v -d stats -d explain"
            "\"")

class moulin_create_full_image(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_create_full_image.__name__)

    def execute(self):

        command = "docker exec -it ${DOCKER_CONTAINER_NAME} " \
        "bash -c \"" \
        f"cd {self.DOCKER_BUILD_PATH}; " \
        f"rouge {self.DOCKER_SOURCE_PATH_BUILD_CONFIG}" + "/${MOULIN_BUILD_CONFIGURATION_FILE_NAME}${MOULIN_BUILD_CONFIGURATION_FILE_EXTENSION} " \
        "--MACHINE ${MOULIN_MACHINE}"

        if self.has_non_empty_environment_param("MOULIN_ADDITIONAL_PARAMETERS"):
            command += " ${MOULIN_ADDITIONAL_PARAMETERS}"

        command += " -fi full -o full.img\""

        self.subprocess_must_succeed(command)

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            f"bash -c \"mv {self.DOCKER_BUILD_PATH}/full.img {self.DOCKER_DEPLOY_PATH}/full.img\"")

class moulin_inject_copy_to_target_parameters_emmc(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_inject_copy_to_target_parameters_emmc.__name__)

    def execute(self):
        moulin_image_name = self.substitute_parameters(f"{self.DEPLOY_PATH}/full.img")
        self.set_environment_param("XQVD_COPY_TO_RPI_SOURCE", moulin_image_name)
        rpi_user_name = self.get_environment_param("RPI_USER_NAME")
        self.set_environment_param("XQVD_COPY_TO_RPI_DESTINATION", self.substitute_parameters("${RPI_NFS_YOCTO_ROOT}/_images_/full.img"))

# NFS and TFTP
class moulin_inject_copy_to_target_parameters_doma_nfs(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_inject_copy_to_target_parameters_doma_nfs.__name__)

    def execute(self):
        pass

class moulin_inject_copy_to_target_parameters_domu_nfs(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_inject_copy_to_target_parameters_domu_nfs.__name__)

    def execute(self):
        pass

class moulin_deploy_domd_nfs_content(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_deploy_domd_nfs_content.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"rm -rf {self.DEPLOY_DOMD_PATH} && "
            f"mkdir -p {self.DEPLOY_DOMD_PATH} && "
            f"cp {self.BUILD_PATH}/yocto/build-domd/tmp/deploy/images/h3ulcb/core-image-weston-h3ulcb.tar.bz2 {self.DEPLOY_DOMD_PATH}/")

class moulin_inject_copy_to_target_parameters_domd_nfs(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_inject_copy_to_target_parameters_domd_nfs.__name__)

    def execute(self):
        deploy_path = self.substitute_parameters("${RPI_NFS_DOMD_ROOT}")
        archive_path = f"{deploy_path}/core-image-weston-h3ulcb.tar.bz2"

        self.set_environment_param("XQVD_COPY_TO_RPI_BEFORE_COPY_HOOK", f"sudo -S rm -rf {deploy_path}; "
            f"mkdir -p {deploy_path}")
        self.set_environment_param("XQVD_COPY_TO_RPI_SOURCE", self.substitute_parameters(f"{self.DEPLOY_DOMD_PATH}/core-image-weston-h3ulcb.tar.bz2"))
        self.set_environment_param("XQVD_COPY_TO_RPI_DESTINATION", archive_path)
        self.set_environment_param("XQVD_COPY_TO_RPI_AFTER_COPY_HOOK", f"cd {deploy_path} && tar -xvf {archive_path} && "
            f"rm {archive_path}")

class moulin_deploy_dom0_tftp_content(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_deploy_dom0_tftp_content.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"rm -rf {self.DEPLOY_DOM0_PATH} && "
            f"mkdir -p {self.DEPLOY_DOM0_PATH} && "
            f"cp {self.BUILD_PATH}/yocto/build-dom0/tmp/deploy/images/generic-armv8-xt/uInitramfs {self.DEPLOY_DOM0_PATH}/ && "
            f"cp {self.BUILD_PATH}/yocto/build-dom0/tmp/deploy/images/generic-armv8-xt/Image {self.DEPLOY_DOM0_PATH}/ && "
            f"cp {self.BUILD_PATH}/yocto/build-domd/tmp/deploy/images/h3ulcb/r8a77951-h3ulcb-4x2g-kf-xen.dtb {self.DEPLOY_DOM0_PATH}/board.dtb;")

class moulin_inject_copy_to_target_parameters_dom0_tftp(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_inject_copy_to_target_parameters_dom0_tftp.__name__)

    def execute(self):
        deploy_path = self.substitute_parameters("${RPI_TFTP_DOM0_ROOT}")

        self.set_environment_param("XQVD_COPY_TO_RPI_BEFORE_COPY_HOOK", f"rm -rf {deploy_path}; "
            f"mkdir -p {deploy_path}")

        self.set_environment_param("XQVD_COPY_TO_RPI_SOURCE", self.substitute_parameters(f"{self.DEPLOY_DOM0_PATH}/"))
        self.set_environment_param("XQVD_COPY_TO_RPI_DESTINATION", deploy_path + "/")

class moulin_deploy_xen_tftp_content(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_deploy_xen_tftp_content.__name__)

    def execute(self):
        self.subprocess_must_succeed(f"rm -rf {self.DEPLOY_XEN_PATH} && "
            f"mkdir -p {self.DEPLOY_XEN_PATH} && "
            f"cp {self.BUILD_PATH}/yocto/build-domd/tmp/deploy/images/h3ulcb/xen-uImage {self.DEPLOY_XEN_PATH}/ && "
            f"cp {self.BUILD_PATH}/yocto/build-domd/tmp/deploy/images/h3ulcb/xenpolicy-h3ulcb {self.DEPLOY_XEN_PATH}/xenpolicy;")

class moulin_inject_copy_to_target_parameters_xen_tftp(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_inject_copy_to_target_parameters_xen_tftp.__name__)

    def execute(self):
        deploy_path = self.substitute_parameters("${RPI_TFTP_XEN_ROOT}")

        self.set_environment_param("XQVD_COPY_TO_RPI_BEFORE_COPY_HOOK", f"rm -rf {deploy_path}; "
            f"mkdir -p {deploy_path}")

        self.set_environment_param("XQVD_COPY_TO_RPI_SOURCE", self.substitute_parameters(f"{self.DEPLOY_XEN_PATH}/"))
        self.set_environment_param("XQVD_COPY_TO_RPI_DESTINATION", deploy_path + "/")
# NFS and TFTP end

class moulin_generate_yocto_dot_graph(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_generate_yocto_dot_graph.__name__)

    def execute(self):
        graph_bitbake_parameters = self.get_environment_param("MOULIN_DOT_GRAPH_BITBAKE_PARAMETERS", "")
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"cd {self.DOCKER_BUILD_PATH}; cd yocto; "
            ". poky/oe-init-build-env build-${MOULIN_DOT_GRAPH_YOCTO_COMPONENT}; "
            f"bitbake -g {graph_bitbake_parameters} " "${MOULIN_DOT_GRAPH_BITBAKE_TARGET} && "
            "rm -rf ${DOCKER_DEPLOY_PATH_DOT_GRAPH} && "
            "mkdir -p ${DOCKER_DEPLOY_PATH_DOT_GRAPH} && "
            "mv ./task-depends.dot ${DOCKER_DEPLOY_PATH_DOT_GRAPH}/ && "
            "mv ./pn-buildlist ${DOCKER_DEPLOY_PATH_DOT_GRAPH}/;"
            "\"")

class moulin_generate_yocto_dot_graph_inject_parameters_filtered(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_generate_yocto_dot_graph_inject_parameters_filtered.__name__)

    def execute(self):
        dot_graph_path = self.substitute_parameters(f"{self.DOCKER_DEPLOY_PATH_FILTERED_DOT_GRAPH_DOT_GRAPH}")
        self.set_environment_param("DOCKER_DEPLOY_PATH_DOT_GRAPH", f"{dot_graph_path}")

class moulin_generate_yocto_filtered_dot_graph(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_generate_yocto_filtered_dot_graph.__name__)

    def execute(self):

        self.subprocess_must_succeed("if [ $$(dpkg-query -W -f='$${Status}' xdot 2>/dev/null | grep -c \"ok installed\") -eq 0 ]; "
            "then "
            "sudo -S apt-get -y install xdot; "
            "fi")

        filter_target = ".${MOULIN_FILTERED_DOT_GRAPH_BITBAKE_TARGET}'" if self.has_non_empty_environment_param("MOULIN_FILTERED_DOT_GRAPH_BITBAKE_TARGET") else "'"

        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"rm -rf {self.DOCKER_DEPLOY_PATH_FILTERED_DOT_GRAPH_RESULT}; "
            f"mkdir -p {self.DOCKER_DEPLOY_PATH_FILTERED_DOT_GRAPH_RESULT}; "
            f"cat {self.DOCKER_DEPLOY_PATH_DOT_GRAPH}/task-depends.dot | grep -E "
            "'digraph depends {|}|"
            f"{filter_target} > {self.DOCKER_DEPLOY_PATH_FILTERED_DOT_GRAPH_RESULT}/task-depends-firtered.dot"
            "\"")

        self.subprocess_must_succeed(f"xdot {self.DEPLOY_PATH_FILTERED_DOT_GRAPH_RESULT}/task-depends-firtered.dot",
            communication_mode = CommunicationMode.PIPE_OUTPUT)

class moulin_generate_yocto_dot_graph_inject_parameters_analyze_dependency(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_generate_yocto_dot_graph_inject_parameters_analyze_dependency.__name__)

    def execute(self):
        dot_graph_path = self.substitute_parameters(f"{self.DOCKER_DEPLOY_PATH_ANALYZE_DEPENDENCY_DOT_GRAPH}")
        self.set_environment_param("DOCKER_DEPLOY_PATH_DOT_GRAPH", f"{dot_graph_path}")

class moulin_analyze_yocto_dependency(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_analyze_yocto_dependency.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"cd {self.DOCKER_BUILD_PATH}; cd yocto; "
            ". poky/oe-init-build-env build-${MOULIN_ANALYZE_YOCTO_DEPENDENCY_COMPONENT}; "
            "oe-depends-dot -k ${MOULIN_ANALYZE_YOCTO_DEPENDENCY_KEY} "
            f"-w {self.DOCKER_DEPLOY_PATH_ANALYZE_DEPENDENCY_DOT_GRAPH}/task-depends.dot"
            "\"")

class moulin_find_yocto_package_by_path(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_find_yocto_package_by_path.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"cd {self.DOCKER_BUILD_PATH}; cd yocto; "
            ". poky/oe-init-build-env build-${MOULIN_FIND_YOCTO_PACKAGE_BY_IMAGE_PATH_COMPONENT}; "
            "oe-pkgdata-util find-path ${MOULIN_FIND_YOCTO_PACKAGE_BY_IMAGE_PATH}"
            "\"")

class moulin_write_yocto_env_to_file(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_write_yocto_env_to_file.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"rm -rf {self.DOCKER_DEPLOY_PATH_WRITE_YOCTO_ENV_TO_FILE}; "
            f"mkdir -p {self.DOCKER_DEPLOY_PATH_WRITE_YOCTO_ENV_TO_FILE}; "
            f"cd {self.DOCKER_BUILD_PATH}; cd yocto; "
            ". poky/oe-init-build-env build-${MOULIN_WRITE_YOCTO_ENV_TO_FILE_COMPONENT}; "
            "bitbake -e ${MOULIN_WRITE_YOCTO_ENV_TO_FILE_TARGET} > "
            f"{self.DOCKER_DEPLOY_PATH_WRITE_YOCTO_ENV_TO_FILE}/yocto_env.txt"
            "\"")

        self.subprocess_must_succeed(f"xdg-open {self.DEPLOY_PATH_WRITE_YOCTO_ENV_TO_FILE}/yocto_env.txt",
            communication_mode = CommunicationMode.PIPE_OUTPUT)

class moulin_lookup_yocto_recipe_by_package(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_lookup_yocto_recipe_by_package.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"cd {self.DOCKER_BUILD_PATH}; cd yocto; "
            ". poky/oe-init-build-env build-${MOULIN_LOOKUP_YOCTO_RECIPE_BY_PACKAGE_COMPONENT}; "
            "oe-pkgdata-util lookup-recipe ${MOULIN_LOOKUP_YOCTO_RECIPE_BY_PACKAGE}"
            "\"")

class moulin_list_yocto_package_files(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_list_yocto_package_files.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"cd {self.DOCKER_BUILD_PATH}; cd yocto; "
            ". poky/oe-init-build-env build-${MOULIN_LIST_YOCTO_PACKAGE_FILES_COMPONENT}; "
            "oe-pkgdata-util list-pkg-files ${MOULIN_LIST_YOCTO_PACKAGE_FILES}"
            "\"")

class moulin_open_dot_dependency_graph_in_taskexp(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_open_dot_dependency_graph_in_taskexp.__name__)

    def execute(self):

        graph_bitbake_parameters = self.get_environment_param("MOULIN_DOT_GRAPH_BITBAKE_PARAMETERS", "")
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"cd {self.DOCKER_BUILD_PATH}; cd yocto; "
            ". poky/oe-init-build-env build-${MOULIN_DOT_GRAPH_YOCTO_COMPONENT}; "
            f"bitbake -g -u taskexp {graph_bitbake_parameters} " "${MOULIN_DOT_GRAPH_BITBAKE_TARGET} "
            "\"")

# Rebuild of the target

class moulin_dev_rebuild_target(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_dev_rebuild_target.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker exec -it ${DOCKER_CONTAINER_NAME} "
            "bash -c \""
            f"cd {self.DOCKER_BUILD_PATH}; cd yocto; "
            ". poky/oe-init-build-env build-${MOULIN_DEV_REBUILD_TARGET_YOCTO_COMPONENT}; "
            f"bitbake -f -v -c compile " "${MOULIN_DEV_REBUILD_TARGET} && "
            f"bitbake -v -c install " "${MOULIN_DEV_REBUILD_TARGET} && "
            "bitbake -v ${MOULIN_DEV_REBUILD_IMAGE};"
            "\"")

class moulin_dev_upload_files_inject_copy_to_target_parameters(moulin_base_task):
    def __init__(self):
        super().__init__()
        self.set_name(moulin_dev_upload_files_inject_copy_to_target_parameters.__name__)

    def execute(self):
        files_list = self.get_environment_param("MOULIN_UPLOAD_FILES_SOURCE").split(";")

        cmd = ""

        for file_path in files_list:
            full_file_path = self.BUILD_PATH + "/" + file_path
            full_file_path_substituted_params = self.substitute_parameters(full_file_path)

            if os.path.isfile(full_file_path_substituted_params):
                cmd += f"cp -f {full_file_path} {self.UPLOAD_FILES_DEPLOY_PATH} &&"
            elif os.path.isdir(full_file_path_substituted_params):
                cmd += f"cp -rf {full_file_path} {self.UPLOAD_FILES_DEPLOY_PATH} &&"
            else:
                logger.warning(f"Provided path '{file_path}' does not exist in the build directory.")

        deploy_folder = self.substitute_parameters(f"{self.UPLOAD_FILES_DEPLOY_PATH}")

        if cmd:
            cmd = f"rm -rf {deploy_folder} && mkdir -p {deploy_folder} && " + cmd[:-3] + ";"
            self.subprocess_must_succeed(cmd)

        self.set_environment_param("XQVD_COPY_TO_RPI_SOURCE", deploy_folder)
        self.set_environment_param("XQVD_COPY_TO_RPI_DESTINATION", self.substitute_parameters("${MOULIN_UPLOAD_FILES_DESTINATION}"))
