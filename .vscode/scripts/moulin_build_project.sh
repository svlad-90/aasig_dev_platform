#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/moulin/moulin.xml -ph moulin_build_project -ld=${3};
