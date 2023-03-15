#!/bin/bash

python ${1}/paf_main.py -imd ${2} -c ${2}/moulin/moulin.xml -s moulin_open_dot_dependency_graph_in_taskexp -ld=${3};
