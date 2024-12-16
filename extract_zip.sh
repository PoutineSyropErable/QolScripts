#!/bin/bash

# Check if any arguments are provided
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <file.zip> [file2.zip ...] or $0 '*.zip'"
    exit 1
fi

# Loop through all provided arguments
for zip_file in "$@"; do
    # Expand the wildcard and check if any .zip files are found
    for file in $zip_file; do
        if [[ ! -e "$file" ]]; then
            echo "No such file: $file"
            continue
        fi

        # Get the directory name by removing the .zip extension
        dir_name="${file%.zip}"

        # Create the directory with the same name as the zip file
        mkdir -p "$dir_name"

        # Extract the zip file into the new directory
        unzip -d "$dir_name" "$file"
        echo "Extracted $file to $dir_name/"
    done
done
