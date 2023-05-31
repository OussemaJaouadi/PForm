#!/bin/bash

# Check if the ID argument is provided
if [ -z "$1" ]; then
  echo "Please provide an ID as an argument."
  exit 1
fi

id="$1"
pdf_dir="$(pwd)/static/pdfs/"
image_dir="$(pwd)/static/images/"


# Create the JSON array variable
json_array="["

# Iterate over each PDF file
for file in $(find "$pdf_dir" -type f -name "*_${id}.pdf"); do
  # Get the project name by removing the ID and extension from the file name
  project_name=$(basename "$file" | sed "s/_${id}\.pdf//")

  # Initialize variables for project details
  creation_date=""
  file_size=""
  num_pages=""

  # Extract project details
  {
    # Get the creation date of the file
    creation_date=$(date -r "$file" "+%Y-%m-%d")

    # Get the file size in bytes
    file_size=$(stat -c "%s" "$file")
    size_Mb=$((file_size / 1000000))
    file_size="$size_Mb MB"

    # Get the number of pages
    num_pages=$(pdfinfo "$file" 2>/dev/null | awk '/^Pages:/ {print $2}')

    # Convert the first page of the PDF to JPEG
    if ! convert -density 300 "$file"[0] "${image_dir}${project_name}.jpg" >/dev/null 2>&1; then
      continue
    fi
  } || continue

  # Check if the image file exists; otherwise, use a default image
  if [ ! -f "${image_dir}${project_name}.jpg" ]; then
    cp "../pfa_web/static/images/default_image.jpg" "${image_dir}${project_name}.jpg"
  fi

  # Add the project details to the JSON array
  json_array+="{\"project_name\": \"$project_name\", \"creation_date\": \"$creation_date\", \"size\": \"$file_size\", \"num_pages\": $num_pages},"
done

# Remove the trailing comma and close the JSON array
json_array="${json_array%,}]"

# Print the JSON array or an empty array if no valid projects found
if [ "${json_array}" = "[" ]; then
  echo "No projects found for the given ID."
else
  echo "${json_array}"
fi
