set ROSETTA /cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle
set root_top /cluster/home/hhussein/topologies 
set topfiles [list $root_top/top_all22_metals.inp  $root_top/top_all36_prot.rtf  $root_top/toppar_water_ions_namd.str $root_top/top_all36_cgenff.rtf $root_top/toppar_all36_prot_na_combined.str]

proc find_and_replace {fin name} {
    set f [open $fin]
    set replaced [regsub -all {XXX} [read $f] $name]
    close $f
    set f [open $fin w]
    puts $f $replaced
    close $f
}

proc rebuild_error {fname} {
    set f [open $fname r] 
    set dir_list [lrange [split [read $f] "\n"] 0  end-1] 
    close $f 

    set root_dir [pwd]
    foreach dir $dir_list {
        cd $root_dir
        cd $dir
        puts $dir
        set name [lindex [split $dir "/"] end]
        puts $name
        if {[catch {build_md $name $root_dir} issue]} {
            puts "FAILED again!"
        }
    }
}

proc build_md {name root_dir} {
    global topfiles
    resetpsf
#    pdbalias residue CA CAL
#    pdbalias residue NA SOD 
    set id [mol new ${name}_protein.pdb]
    [atomselect $id "resname WAT"] set resname TIP3
    [atomselect $id "resname NA"] set resname SOD
    [atomselect $id "resname CA"] set resname CAL
    [atomselect $id "resname SR"] set resname CAL
    [atomselect $id "resname SR"] set name CA
    [atomselect $id "resname ACE"] set resname ACET
    # remove unknown residue
    [atomselect $id "resname CSO"] set resname CYS
    [atomselect $id "resname PTR"] set resname TYR
    [atomselect $id "resname SEP"] set resname SER
    [atomselect $id "resname TPO"] set resname THR
    [atomselect $id "resname MSE"] set resname MET
    [atomselect $id "resname KCX"] set resname LYS
    [atomselect $id "resname IAS CAS PCA LI LLP"] set segname DELE
    
    [atomselect $id "not segname DELE"] writepdb tmp_md.pdb
    set id [mol new tmp_md.pdb]
    file delete tmp_md.pdb
    #set patchlist [list "PRES SEG RESID"]
    autopsf -mol $id -prefix $name -top $topfiles
    
    file rename -force ${name}_formatted_autopsf.pdb ${name}_MD.pdb
    file rename -force ${name}_formatted_autopsf.psf ${name}_MD.psf
    ssrestraints -psf ${name}_MD.psf -pdb ${name}_MD.pdb -o restraints.txt
    
    file mkdir dynamics
    file copy -force $root_dir/configuration_templates/md.conf dynamics/ 
    find_and_replace dynamics/md.conf ${name}_MD
}

proc create_test_md {fout} {
    set folders [glob -directory $fout -type d *]
    set root_dir [pwd]
    foreach f $folders {
        set name [file tail $f]
        if {$name == "parameters"} {
            continue
        }
        file copy -force configuration_templates/test.conf $f/dynamics
        find_and_replace $f/dynamics/test.conf ${name}_MD
    }
}

# Parameters:
#
#  fin: directory containing the protein directories (e.g. refined_set_cleaned)
#  fout: directory where the complexes will be stored
#
proc build_complexes {fin fout} {
    global ROSETTA
    set bad_pdb [list]
    set folders [glob -directory $fin -type d *]
    set propreties {name resname resid chain x y z segname}
    set root_dir [pwd]
    foreach f $folders {
        cd $root_dir
        #create output folder
        set name [file tail $f]
        file mkdir $fout/$name
        #ligand
        # NEED: pdb_ligand.mol2
        file copy -force $f/${name}_ligand.mol2 ${fout}/${name}/${name}_ligand.mol2
        exec $ROSETTA/main/source/scripts/python/public/molfile_to_params.py -n INH  ${fout}/${name}/${name}_ligand.mol2 --clobber --keep-names
        # NEED: INH_0001.pdb
        set lig_idx [mol new INH_0001.pdb]
        set ligand [atomselect $lig_idx all]
        $ligand set chain X
        $ligand set resname INH
        set lig_num [$ligand num]

        #receptor
        # NEED: pdb_protein.pdb
        set prot_idx [mol new $f/${name}_protein.pdb]
        set protein [atomselect $prot_idx protein]
        set chains [lsort -unique [$protein get chain]]
        set i 65
        foreach c $chains {
            [atomselect $prot_idx "not protein and within 3 of chain $c"] set chain [format %c $i]
            [atomselect $prot_idx "chain $c"] set chain [format %c $i]
            incr i
        }

        set water [atomselect $prot_idx "water"]
        $water set chain W
        $water set resname WAT
        $water delete
        
        #merge structures
        set receptor [atomselect $prot_idx all]
        #renumber everything
        set residue [$receptor get residue]
        set resid {}
        foreach r $residue {
            lappend resid [expr $r +1]
        }
        $receptor set resid $resid
        set rec_num [$receptor num]
        set numatoms [expr $rec_num + $lig_num]
        set id [mol new atoms $numatoms]
        animate dup $id 
        [atomselect $id "serial 1 to $rec_num"] set $propreties [$receptor get $propreties] 
        [atomselect $id "index $rec_num to [expr $rec_num + $lig_num - 1]"] set $propreties [$ligand get $propreties]
        $protein delete
        $ligand delete
        [atomselect $id all] writepdb tmp.pdb
        mol delete $id
        # NEED: tmp.pdb
        set id [mol new tmp.pdb]
        # WRITES: pdb_complex.pdb
        [atomselect $id "(not water and same chain as (protein and within 5 of resname INH))  or resname INH or (water and ((within 3 of protein) and (within 3 of resname INH)))"] writepdb ${name}_complex.pdb
        # WRITES: pdb_ligand.mol2
        animate write mol2 ${name}_ligand.mol2 beg 0 end 0 skip 1 $lig_idx
        # WRITES: pdb_protein.pdb
        [atomselect $id "(not (water or resname INH) and same chain as (protein and within 5 of resname INH)) or (water and ((within 3 of protein) and (within 3 of resname INH)))"] writepdb ${name}_protein.pdb
        
        mol delete $lig_idx
        mol delete $prot_idx
        mol delete $id
        exit 
        #build topology for protein
        if {1} {
            if {[catch {build_md $name $root_dir} issue]} {
                lappend bad_pdb $name
            }
        }
        mol delete all
        file delete tmp.pdb
    }


    cd $root_dir
    set f [open "error.dat" w]
    puts $f [join $bad_pdb "\n"]
    close $f
}
