source /cluster/home/hhussein/home/lemmint/Documents/scripts/scripts/tcl/TMAlign.tcl
set CLEAN /cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/tools/protein_tools/scripts/clean_pdb.py

proc find_and_replace {fin name} {
    set f [open $fin]
    set replaced [regsub -all {XXX} [read $f] $name]
    close $f
    set f [open $fin w]
    puts $f $replaced
    close $f
}

proc build_complex {root_dir dir i chid lig} {
    global CLEAN
    set propreties {name resname resid chain x y z segname}
    cd structures/$i
    exec $CLEAN ${dir}_${i}.pdb $chid
    file delete *.fasta
    set id [mol new ${dir}_${i}_$chid.pdb]
    set prot [atomselect $id all]
    set rec_num [$prot num]
    set lig_num [$lig num]

    set numatoms [expr $rec_num + $lig_num]
    set id_complex [mol new atoms $numatoms]
    animate dup $id_complex 
    [atomselect $id_complex "serial 1 to $rec_num"] set $propreties [$prot get $propreties] 
    [atomselect $id_complex "index $rec_num to [expr $rec_num + $lig_num - 1]"] set $propreties [$lig get $propreties]
    [atomselect $id_complex all] writepdb ${dir}_complex_${i}.pdb
    file copy -force $root_dir/configuration_templates/relax.xml .
    file copy -force $root_dir/configuration_templates/flags_relax.txt .
    find_and_replace flags_relax.txt ${dir}_complex_${i}.pdb
    mol delete $id
    mol delete $id_complex
    cd ../../
}

proc extract_frames {folder fname nstruct} {
    set f [open $fname r]
    set dir_list [lrange [split [read $f] "\n"] 0  end-1] 
    close $f

    set IONS "FE NA MG K CA ZN CU LN MN FE2 CD CO"
    set root_dir [pwd]
    
    foreach dir $dir_list {
        cd $root_dir
        cd $folder/$dir 
        file delete -force -- structures
        file mkdir structures
        set id [mol new ${dir}_MD.psf]
        mol addfile dynamics/${dir}_MD.dcd waitfor all
        set id_complex [mol new ${dir}_complex.pdb]
        set ref [atomselect $id_complex protein]
        set lig [atomselect $id_complex "resname INH WAT $IONS"]
        set a [atomselect $id "protein"]
        set chid [join [lsort -unique [$a get chain]] ""]
        set his  [atomselect $id "resname HSD"] 
        $his set resname HIS
        $his delete
        set i 0
        set step [expr round([molinfo $id get numframes] / $nstruct.)]
        while {$i < $nstruct} {
            $a frame [expr $i * $step]
            set M [TMAlign $ref $a]
            $a move $M
            $a set occupancy 1.0
            file mkdir structures/$i
            $a writepdb structures/$i/${dir}_$i.pdb
            build_complex $root_dir $dir $i $chid $lig
            incr i 
        }
        mol delete $id 
    }
}
