#!/usr/bin/env bash

CONFIG_FILE="ADD CONFIG FILE HERE"
INTERPOLATION="pointwise_gaussian"

declare -a pids

batch_size=$1

if [ $1 -ge 1 ]
then
    counter=0
    for PROT in $(find "${PWD}" -maxdepth 1 -printf '%f\n')
    do
        if [ ${PROT} != "sandbox" ] && [ ${PROT} != "configuration_templates" ]
        then
            python -p ${PROT} -c ${CONFIG_FILE} -i ${INTERPOLATION} -P &
            pids[${counter}]=$!
        fi
        counter=$((counter + 1))
        if [ ${counter} -eq ${batch_size} ]
        then
            for pid in ${pids[*]}
            do
                wait ${pid}
            done
        fi
    done
fi