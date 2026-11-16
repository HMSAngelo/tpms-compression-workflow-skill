# HyperMesh 2021, Abaqus Explicit solver profile. Input contains specimen only.
proc main {} {
    set template "C:/Program Files/Altair/2021/hwdesktop/templates/feoutput/abaqus/explicit"
    set input [file normalize $::env(HPS_LINEAR_INP)]
    set output [file normalize $::env(HPS_SECOND_INP)]
    *templatefileset $template
    *createstringarray 1 "IMPORT_BY1COMP "
    *feinputwithdata2 "#abaqus/abaqus" $input 0 0 0 0 0 1 1 1 0
    *createmark elems 1 all
    *createmark nodes 1 all
    set initial [hm_marklength elems 1]
    set initialNodes [hm_marklength nodes 1]
    if {$initial <= 0 || $initialNodes <= 0} {error "Empty input"}
    *createmark elems 2 "by config" 204
    if {[hm_marklength elems 2] != $initial} {error "Expected only tetra4 in nTop input"}
    puts "Input: $initial tetra4, $initialNodes nodes"
    # Mid-edge placement on the imported FE boundary without surface projection.
    *elementtype 210 3
    *orderchangetosecond 1 0 0
    *createmark elems 1 "by config" 210
    if {[hm_marklength elems 1] != $initial} {error "Unexpected tetra10 count"}
    *elementsettypes 1
    *createmark nodes 1 all
    puts "Output: $initial tetra10, [hm_marklength nodes 1] nodes"
    *writefile [file join [pwd] HPS180_second_order.hm] 1
    *createstringarray 1 "EXPORTIDS_SKIP"
    *feoutputwithdata $template $output 0 0 1 1 1
    if {![file exists $output] || [file size $output] == 0} {error "Missing Abaqus export"}
    puts "HPS_HM_EXPORT_OK"
}
if {[catch {main} message]} {
    puts stderr $::errorInfo
    error $message
}
