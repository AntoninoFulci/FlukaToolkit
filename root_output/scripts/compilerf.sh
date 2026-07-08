#!/bin/bash

makefile_dir=$FLUKA_ROOT

# Define the function to call the Makefile from another directory
compilerf() {
    local make_flags=""
    
    # Parse optional flags (like --rntuple)
    while [[ "$1" == -* ]]; do
        case "$1" in
            --rntuple)
                make_flags="USE_RNTUPLE=1"
                shift # Shift past the flag
                ;;
            *)
                echo "Error: Unknown option '$1'"
                return 1
                ;;
        esac
    done

    # After shifting options, the next argument is the executable name
    local name=$1  
    shift          # Remove the executable name, leaving only the .f files

    # Collect the full paths of the .f files from the current directory
    local objs=""
    for ffile in "$@"; do
        # Replace .f suffix with .o
        obj_file=$(basename "$ffile" .f).o
        objs="$objs $(pwd)/$obj_file"
    done

    # Call the Makefile in the specified directory, passing the variables
    make -C "$makefile_dir" NAME="$name" OBJS="$objs" $make_flags
}

compilerf_clean() {
    local name=$1
    make -C "$makefile_dir" clean NAME="$name"
}

compilerf_cleanall() {
    make -C "$makefile_dir" cleanall
}