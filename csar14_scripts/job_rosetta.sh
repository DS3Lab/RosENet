#! /bin/bash

rosetta=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/source/bin/rosetta_scripts.static.linuxgccrelease
rosettadb=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/database/
var=0
while IFS= read -r folder
do
    cd /cluster/scratch/hhussein/refined_set_cleaned/$folder/minimized
    $rosetta @flags_relax.txt -parser:protocol relax.xml -database $rosettadb &
    var=$((var+1))
    if [ $var -eq 2 ]
    then
        var=0
        wait
    fi
done < $HOME/rerun2/XXX 
wait
