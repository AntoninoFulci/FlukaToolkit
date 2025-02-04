#!/bin/bash

makefile_dir="/Users/tonyf/Work/FLUKA-CERN/FlukaROOTOutput"
# Define the function to call the Makefile from another directory
compilerf() {
    local name=$1  # First argument is the executable name (rootfluka)
    shift          # Remove the first argument (name), leaving the .f files

    # Collect the full paths of the .f files from the current directory
    local objs=""
    for ffile in "$@"; do
        # Replace .f suffix with .o
        obj_file=$(basename "$ffile" .f).o
        objs="$objs $(pwd)/$obj_file"
    done

    # Call the Makefile in the specified directory, passing the name and object files
    make -C "$makefile_dir" NAME="$name" OBJS="$objs"
}

compilerf_clean() {
    local name=$1
    make -C "$makefile_dir" clean NAME="$name"
}

compilerf_cleanall() {
    local name=$1
    make -C "$makefile_dir" cleanall
}