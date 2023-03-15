from paf.paf_impl import Task, logger, CommunicationMode

class docker_install(Task):

    def __init__(self):
        super().__init__()
        self.set_name(docker_install.__name__)

    def execute(self):

        self.subprocess_must_succeed("sudo -S apt-get update; "
            "sudo -S apt-get install -y ca-certificates curl gnupg lsb-release; ")

        self.subprocess_must_succeed("if [ ! -f /usr/share/keyrings/docker-archive-keyring.gpg ]; then curl -fsSL ${DOCKER_GPG_KEY_URL} "
            "| sudo -S gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg; fi")

        target_string = "deb [arch=$$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] "\
            "https://download.docker.com/linux/ubuntu $$(lsb_release -cs) stable"

        self.subprocess_must_succeed(f'( sudo -S grep -qxF \'{target_string}\' /etc/apt/sources.list.d/docker.list ) || ( echo "{target_string}" | '
            'sudo -S tee /etc/apt/sources.list.d/docker.list > /dev/null )')

        self.subprocess_must_succeed("sudo -S apt-get update; "
             "sudo -S apt-get install -y docker-ce docker-ce-cli containerd.io; "
             "sudo -S groupadd docker; "
             "sudo -S usermod -aG docker $$USER;")

class docker_install_qemu_static(Task):

    def __init__(self):
        super().__init__()
        self.set_name(docker_install_qemu_static.__name__)

    def execute(self):

        self.subprocess_must_succeed("sudo -S apt-get -y install qemu binfmt-support qemu-user-static")

class docker_build_image(Task):

    def __init__(self):
        super().__init__()
        self.set_name(docker_build_image.__name__)

    def execute(self):

        self.subprocess_must_succeed("if ! [[ \"$$(docker images -q ${DOCKER_IMAGE_NAME} 2> /dev/null)\" == \"\" ]]; then " \
            "docker rmi ${DOCKER_IMAGE_NAME};" \
            " fi")

        self.subprocess_must_succeed("docker build -f ${DOCKERFILE_PATH} -t ${DOCKER_IMAGE_NAME} .")


class docker_remove_image(Task):

    def __init__(self):
        super().__init__()
        self.set_name(docker_remove_image.__name__)

    def execute(self):

        self.subprocess_must_succeed("if ! [[ \"$$(docker images -q ${DOCKER_IMAGE_NAME} 2> /dev/null)\" == \"\" ]]; then " \
            "docker rmi ${DOCKER_IMAGE_NAME};" \
            " fi")

class docker_create_container(Task):

    def __init__(self):
        super().__init__()
        self.set_name(docker_create_container.__name__)

    def execute(self):

        if self.has_non_empty_environment_param("DOCKER_MOUNT_FOLDER"):
            mount_folders = "-v ${DOCKER_MOUNT_FOLDER}:/mnt "

        if self.has_non_empty_environment_param("DOCKER_SSH_MOUNT_FOLDER"):
            mount_folders += "-v ${DOCKER_SSH_MOUNT_FOLDER}:/home/builder/.ssh "

        if self.has_non_empty_environment_param("DOCKER_GIT_CONFIG_MOUNT_FOLDER"):
            mount_folders += "-v ${DOCKER_GIT_CONFIG_MOUNT_FOLDER}:/home/builder/.gitconfig "

        self.subprocess_must_succeed("docker create --name ${DOCKER_CONTAINER_NAME} -ti " + "--env=\"DISPLAY\" --network=host " + mount_folders + \
            " " + ( "${DOCKER_CREATE_ADDITIONAL_PARAMS}" if self.has_non_empty_environment_param("DOCKER_CREATE_ADDITIONAL_PARAMS") else "" ) + " ${DOCKER_IMAGE_NAME}"
            )

class docker_start_container(Task):

    def __init__(self):
        super().__init__()
        self.set_name(docker_start_container.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker start ${DOCKER_CONTAINER_NAME}")

class docker_stop_container(Task):

    def __init__(self):
        super().__init__()
        self.set_name(docker_stop_container.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker stop ${DOCKER_CONTAINER_NAME} | :")

class docker_remove_container(Task):

    def __init__(self):
        super().__init__()
        self.set_name(docker_stop_container.__name__)

    def execute(self):
        self.subprocess_must_succeed("docker rm ${DOCKER_CONTAINER_NAME} | :")