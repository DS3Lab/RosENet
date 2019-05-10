#package require psfgen
package require autopsf

#topology toppar/top_all22_metals.rtf
#topology toppar/top_all36_carb.rtf
#topology toppar/top_all36_cgenff.rtf
#topology toppar/top_all35_ethers.rtf
#topology toppar/top_all36_lipid.rtf
#topology toppar/top_all36_na.rtf
#topology toppar/top_all36_prot.rtf
#topology toppar/stream/prot/toppar_all36_prot_aldehydes.str
#topology toppar/stream/prot/toppar_all36_prot_pyridines.str
#topology toppar/stream/prot/toppar_all36_prot_fluoro_alkanes.str
#topology toppar/stream/misc/toppar_amines.str
#topology toppar/stream/misc/toppar_dum_noble_gases.str
#topology toppar/toppar_water_ions.str
#topology toppar/stream/prot/toppar_all36_prot_model.str
  
#pdbalias residue HIS HSE 


proc gen_psf {pdb_path} {
  set molID [mol load pdb $pdb_path]
  autopsf -mol $molID -protein -regen
}
proc generate_psf {pdb_path} {
  set psf_path [file rootname $pdb_path].psf
  mol load pdb $pdb_path
  #set protein [atomselect $pdb "protein"]
  #segment PROT {pdb $pdb_path}
  #pdbalias atom ILE CD1 CD
  #pdbalias residue HIS HSE
  #coordpdb $pdb_path PROT
  guesscoord
  writepsf cmap $psf_path
  #mol delete $pdb
}

proc generate_psf_2 {pdb_path} {
  resetpsf
  topology toppar/top_all22_prot.rtf
  pdbalias residue HIS HSE
  pdbalias atom ILE CD1 CD
  segment PROT {
        first NTER
        last CTER
        auto angles dihedrals
        pdb $pdb_path
        }
  patch CTER ...
  patch NTER ...
  regenerate angles dihedrals
  coordpdb $pdb_path A
  guesscoord
  set psf_path [file rootname $pdb_path].psf
  writepsf charmm $psf_path
}

gen_psf [lindex $argv 0]
exit
