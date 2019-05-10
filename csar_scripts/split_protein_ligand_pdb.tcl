proc read_database {input_file} {
  set pdb_dict [dict create]
  set fp [open $input_file r]
  set rows [split [read $fp] "\n"]
  foreach line $rows {
    set pdb [lindex $line 0]
    set val [lindex $line 1]
    set resnames [lrange $val 0 end-3]
    set k_type [lindex $val end-2]
    set k_rel [lindex $val end-1]
    set k_val [lindex $val end]
    dict lappend pdb_dict $pdb $resnames
  }
  return $pdb_dict
}

set pdb_dict [read_database "/cluster/scratch/hhussein/nr_bind_cleaned.csv"]

# Open a PDB file and write its not-protein atoms in a mol2 formatted file.
#
# Parameters:
#
#   input_file: String. Path of the PDB input (it does not require a .pdb extension)
#   output_file: String. Path of the MOL2 output (it does not require a .mol2 extension)
#
# Returns:
#
#   Nothing
#
proc split_protein_ligand_pdb {input_file output_folder} {
  global pdb_dict
  set pdb [string toupper [file rootname [file tail $input_file]]]
  set compound_data [mol addfile $input_file type pdb]
  set prot_selection [atomselect $compound_data "protein"]
  $prot_selection writepdb "${output_folder}/${pdb}_protein.pdb"
  set inh_selection [atomselect $compound_data "not water and not protein"]
  set complex_selection [atomselect $compound_data "all"]
  set residues [lsort -unique [$inh_selection get resname]]
  if { [llength $residues] > 1 } then {
    set choices [dict get $pdb_dict $pdb]
    foreach choice $choices {
      set selector {}
      foreach element $choice {lappend selector "resname $element"}
      set selector [join $selector " or "]
      set inh_selection [atomselect $compound_data $selector]
      set alias [join [lsort -unique [$inh_selection get resname]] "_"]
      set complex_selection [atomselect $compound_data "protein or water or $selector"]
      $inh_selection writepdb "${output_folder}/${pdb}_ligand_${alias}.pdb"
      $complex_selection writepdb "${output_folder}/${pdb}_complex_${alias}.pdb"
    }
  } else {
    $inh_selection writepdb "$output_folder/${pdb}_ligand.pdb"
    $complex_selection writepdb "$output_folder/${pdb}_complex.pdb"
  }
  mol delete $compound_data
}

# Generate mol2 files for ligands of each PDB file listed on the input.
#
# Parameters:
# 
#   input_list: List of String. Paths of the PDB inputs.
#   output_folder: String. Path of the directory to store the MOL2 outputs.
#
# Returns:
#
#   Nothing
#
proc split_protein_ligand_pdb_list {input_list output_folder} {
  set counter 1
  set total [llength $input_list]
  foreach input_file $input_list {
    split_protein_ligand_pdb $input_file $output_folder
    puts "Processed $input_file ($counter/$total)"
    incr counter
  }
}

if { [llength $argv] > 2 } then {
  split_protein_ligand_pdb_list [lrange $argv 1 end-1] [lindex $argv end]
} else {
  split_protein_ligand_pdb [lindex $argv 0] [lindex $argv 1]
}
