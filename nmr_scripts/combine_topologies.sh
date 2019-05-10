#!/bin/bash

topology_files=(
'toppar/top_all22_metals.rtf'
'toppar/top_all36_carb.rtf'
'toppar/top_all36_cgenff.rtf'
'toppar/top_all35_ethers.rtf'
'toppar/top_all36_lipid.rtf'
'toppar/top_all36_na.rtf'
'toppar/top_all36_prot.rtf'
'toppar/stream/prot/toppar_all36_prot_model.str'
'toppar/stream/misc/toppar_amines.str'
'toppar/stream/misc/toppar_dum_noble_gases.str'
'toppar/stream/misc/toppar_hbond.str'
'toppar/toppar_water_ions.str'
'toppar/stream/prot/toppar_all36_prot_aldehydes.str'
'toppar/stream/prot/toppar_all36_prot_pyridines.str'
'toppar/stream/prot/toppar_all36_prot_fluoro_alkanes.str'
)

> topology.rtf

for i in "${topology_files[@]}"
do
  cat ./$i >> topology.rtf
done
