#!/bin/bash
rosetta=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/source/bin/rosetta_scripts.static.linuxgccrelease
rosettadb=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/database/
script_folder=$(pwd)
export rosetta
export rosettadb
export script_folder

function make_rosetta() {
  folder=$(dirname "$1")
  complex=$(basename "$1") envsubst < flag_from_cen_to_fa > "$folder/flag_from_cen_to_fa"
  cd $(dirname "$1")
  cat flag_from_cen_to_fa
  $rosetta @flag_from_cen_to_fa -parser:protocol "$script_folder/cen_to_fa.xml"
}
export -f make_rosetta

if [ $# -eq 1 ]; then
  rm -f "/cluster/scratch/hhussein/Structures/set1/$1/score.sc"
  bash -c "make_rosetta /cluster/scratch/hhussein/Structures/set1/$1/$1_complex.pdb"
else
find /cluster/scratch/hhussein/Structures -name "*_complex.pdb" | parallel -n 1 bash -c ": && make_rosetta {}"
fi
