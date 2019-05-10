#!/bin/bash
rosetta=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/source/bin/rosetta_scripts.static.linuxgccrelease
rosettadb=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/database/
rpkmin=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/source/bin/ligand_rpkmin.linuxgccrelease 
rel=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/source/bin/relax.static.linuxgccrelease
minimize=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/source/bin/minimize.static.linuxgccrelease
script_folder=$(pwd)
export rosetta
export rosettadb
export script_folder
export rel
export minimize
function make_rosetta() {
  folder=$(dirname "$1")
  echo $folder
  cd $(dirname "$1")
  if [ ! -f "processed" ]; then
    echo "################################################ $(basename $folder)"
    complex=$(basename "$1") name=$(basename "$1" .pdb) params="${name/complex/ligand}.params" envsubst < $script_folder/flags_relax.txt > "flags_relax.txt"
    touch "processed"
    ($rosetta @flags_relax.txt -parser:protocol  "$script_folder/relax_3.xml" -database $rosettadb) && echo "Finished $(basename $folder) correctly"
    #($rpkmin -database $rosettadb -extrachi_cutoff 1 -no_optH false -flip_HNQ -docking:ligand:old_estat -docking:ligand:soft_rep -nstruct 10)
    #($rel @flags_relax.txt -database $rosettadb -relax:constrain_relax_to_start_coords -relax:coord_constrain_sidechains -relax:ramp_constraints false) && echo "Finished $(basename $folder) correctly"
    #($minimize @flags_relax.txt -database $rosettadb) && echo "Finished $(basename $folder) correctly"
    #($rosetta @flags_relax.txt -parser:protocol "$script_folder/relax.xml" -database $rosettadb ) && echo "Finished $(basename $folder) correctly"
  fi
}
export -f make_rosetta

if [ $# -eq 1 ]; then
  rm -f "/cluster/scratch/hhussein/pdbbind2018/$1/score.sc"
  rm -f "/cluster/scratch/hhussein/pdbbind2018/$1/processed"
  bash -c "make_rosetta /cluster/scratch/hhussein/pdbbind2018/$1/$1_complex.pdb"
else
find /cluster/scratch/hhussein/pdbbind2018/ -name "*_complex.pdb" | parallel -j 2 -n 1 --ungroup  bash -c ": && make_rosetta {}"
fi
