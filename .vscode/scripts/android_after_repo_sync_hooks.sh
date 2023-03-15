#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/build_android/general_settings.xml -c ${2}/${3} -t aasig_dev_platform.build_android.android_after_repo_sync_hooks -ld=${4} -p IS_SDK_BUILD="True";
