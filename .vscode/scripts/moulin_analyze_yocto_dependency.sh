#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/moulin/moulin.xml -s moulin_analyze_yocto_dependency -ld=${3};
