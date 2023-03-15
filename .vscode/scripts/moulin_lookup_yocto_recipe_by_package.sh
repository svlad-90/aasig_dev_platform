#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/moulin/moulin.xml -s moulin_lookup_yocto_recipe_by_package -ld=${3};
