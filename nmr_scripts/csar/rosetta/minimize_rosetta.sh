#!/bin/bash
rosetta=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/source/bin/rosetta_scripts.static.linuxgccrelease
rosettadb=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/database/
script_folder=$(pwd)
export rosetta
export rosettadb
export script_folder

function make_rosetta() {
  folder=$(dirname "$1")
  complex=$(basename "$1") name=$(basename "$1" .pdb) params="${name/complex/ligand}.params" envsubst < flags_relax.txt > "$folder/flags_relax.txt"
  cd $(dirname "$1")
  cat flags_relax.txt
  echo $folder
  echo $complex
  $rosetta @flags_relax.txt -parser:protocol "$script_folder/relax.xml" -database $rosettadb
}
export -f make_rosetta

if [ $# -eq 1 ]; then
  rm -f "/cluster/scratch/hhussein/Structures/set2/$1/score.sc"
  bash -c "make_rosetta /cluster/scratch/hhussein/Structures/set2/$1/$1_complex.pdb"
else
find /cluster/scratch/hhussein/Structures -name "*_complex.pdb" | parallel -n 1 bash -c ": && make_rosetta {}"
fi
