#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/moulin/moulin.xml -s moulin_list_yocto_package_files -ld=${3};
