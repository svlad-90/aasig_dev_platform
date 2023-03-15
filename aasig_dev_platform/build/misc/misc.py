'''
Created on Mar 11, 2022

@author: vladyslav_goncharuk
@brief: Custom automation scenarios for various projects
'''

from paf.paf_impl import Task

class update_diagrams(Task):

    def __init__(self):
        super().__init__()
        self.set_name(update_diagrams.__name__)

    def execute(self):
        diagrams_location = "~/Projects/epam/aosp-vhal/md/puml/diagrams"
        self.subprocess_must_succeed(f"rm -rf {diagrams_location}; mkdir -p {diagrams_location};")
        self.subprocess_must_succeed("adb root")
        self.subprocess_must_succeed('adb shell "pidof epam_android.hardware.automotive.vehicle@2.0-service | xargs kill -SIGUSR1"')
        self.subprocess_must_succeed(f'cd {diagrams_location}; adb shell find "/data/vendor/epam/vehicle" -iname "*.puml" | tr -d \'\015\' | while read line; do adb pull "$$line"; done;')
        self.subprocess_must_succeed(f'java -jar /usr/share/plantuml/plantuml.jar -tsvg {diagrams_location}/*')