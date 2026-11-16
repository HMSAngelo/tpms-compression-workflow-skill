# HyperMesh 2021. Draw and mesh two planar discrete rigid platens.
proc platen {name z side divisions reverse} {
    *createentity comps name=$name
    *currentcollector components $name
    set h [expr {$side / 2.0}]
    set xy [list [list -$h -$h] [list $h -$h] [list $h $h] [list -$h $h]]
    set ids {}
    foreach p $xy {
        *createpoint [lindex $p 0] [lindex $p 1] $z 0
        lappend ids [hm_latestentityid points]
    }
    *surfacemode 1
    *createmark points 1 {*}$ids
    *surfacesplinefrompoints points 1 1
    set surf [hm_latestentityid surfaces]
    *createmark surfaces 1 $surf
    set size [expr {$side / double($divisions)}]
    *interactivemeshsurf 1 $size 4 4 1 1 0
    for {set edge 0} {$edge < 4} {incr edge} {
        *set_meshedgeparams $edge $divisions 0 0 0 0 0 0 0
    }
    *set_meshfaceparams 0 2 4 0 0 0 0.1 1 0
    *automesh 0 1 1
    *storemeshtodatabase 0
    *ameshclearsurface
    *createmark elems 1 "by comp name" $name
    if {[hm_marklength elems 1] != $divisions * $divisions} {
        error "Incorrect mapped element count for $name"
    }
    *elementtype 104 5
    *elementsettypes 1
    *createmark elems 1 "by comp name" $name
    if {$reverse} {*normalsreverse elements 1 1.0}
    puts "$name surface $surf: [hm_marklength elems 1] R3D4, target side $size mm"
}

proc main {} {
    set template "C:/Program Files/Altair/2021/hwdesktop/templates/feoutput/abaqus/explicit"
    *templatefileset $template
    if {$::env(TPMS_Z_BOTTOM) >= $::env(TPMS_Z_TOP) || $::env(TPMS_PLATE_SIDE) <= 0 ||
        ![string is integer -strict $::env(TPMS_PLATE_DIVISIONS)] || $::env(TPMS_PLATE_DIVISIONS) < 1} {
        error "Invalid platen dimensions or divisions"
    }
    platen BOTTOM $::env(TPMS_Z_BOTTOM) $::env(TPMS_PLATE_SIDE) $::env(TPMS_PLATE_DIVISIONS) 0
    platen TOP $::env(TPMS_Z_TOP) $::env(TPMS_PLATE_SIDE) $::env(TPMS_PLATE_DIVISIONS) 1
    *createmark surfaces 1 all
    if {[hm_marklength surfaces 1] != 2} {error "Expected two geometric surfaces"}
    *setoption delete_elements_mode=0
    *deletemark surfaces 1
    *createmark points 1 all
    if {[hm_marklength points 1] > 0} {*deletemark points 1}
    foreach entity {surfaces lines points} {
        *createmark $entity 1 all
        if {[hm_marklength $entity 1] != 0} {error "Geometry left after cleanup: $entity"}
    }
    *createmark elems 1 all
    set elems [hm_getmark elems 1]
    *createmark nodes 2 "by elem" {*}$elems
    set expected [expr {2 * ($::env(TPMS_PLATE_DIVISIONS) + 1)**2}]
    if {[hm_marklength nodes 2] != $expected} {error "Unexpected number of connected mesh nodes"}
    foreach {name z} [list BOTTOM $::env(TPMS_Z_BOTTOM) TOP $::env(TPMS_Z_TOP)] {
        *createnode 0 0 $z 0 0 0
        set rp [hm_latestentityid nodes]
        *createentity sets name=${name}_RP cardimage=NSET type=nodes ids=$rp
        puts "${name}_RP node $rp at (0, 0, $z)"
    }
    *createmark nodes 1 all
    if {[hm_marklength nodes 1] != $expected + 2} {error "Unexpected free nodes after cleanup"}
    puts "Geometry count 0; [llength $elems] mesh facets; $expected connected nodes and two independent RPs"
    *writefile [file join [pwd] platens.hm] 1
    *createstringarray 1 "EXPORTIDS_SKIP"
    *feoutputwithdata $template [file join [pwd] platens_hm.inp] 0 0 1 1 1
    puts "TPMS_PLATENS_EXPORT_OK"
}

if {[catch {main} message]} {
    puts stderr $::errorInfo
    error $message
}
