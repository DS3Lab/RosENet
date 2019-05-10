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
proc make_INH_mol2 {input_file output_folder} {
  global pdb_dict
  set pdb [string toupper [file rootname [file tail $input_file]]]
  set compound_data [mol addfile $input_file type pdb]
  set inh_selection [atomselect $compound_data "not water and not protein"]
  set residues [lsort -unique [$inh_selection get resname]]
  puts $residues
  if { [llength $residues] > 1 } then {
    set choices [dict get $pdb_dict $pdb]
    foreach choice $choices {
      set selector {}
      foreach element $choice {lappend selector "resname $element"}
      set selector [join $selector " or "]
      set inh_selection [atomselect $compound_data $selector]
      set alias [join [lsort -unique [$inh_selection get resname]] "_"]
      $inh_selection writemol2 "${output_folder}/${pdb}_${alias}.mol2"
    }
    mol delete $compound_data
  } else {
    $inh_selection writemol2 "$output_folder/$pdb.mol2"
    mol delete $compound_data
  }
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
proc make_INH_mol2_list {input_list output_folder} {
  set counter 1
  set total [llength $input_list]
  foreach input_file $input_list {
    make_INH_mol2 $input_file $output_folder
    puts "Processed $input_file ($counter/$total)"
    incr counter
  }
}

proc read_database {input_file} {
  set pdb_dict [dict create]
  set fp [open $input_file r]
  set rows [split [read $fp] "\n"]
  foreach line $rows {
    set resnames [lrange $line 0 end-3]
    set k_type [lindex $line end-2]
    set k_rel [lindex $line end-1]
    set k_val [lindex $line end]
    dict lappend $pdb_dict $resname {$resname}
  }
  return $pdb_dict
}


if { [llength $argv] > 2 } then {
  make_INH_mol2_list [lrange $argv 1 end-1] [lindex $argv end]
} else {
  make_INH_mol2 [lindex $argv 0] [lindex $argv 1]
}
