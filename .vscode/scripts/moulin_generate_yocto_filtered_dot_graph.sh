#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/moulin/moulin.xml -s moulin_generate_yocto_filtered_dot_graph -ld=${3};
