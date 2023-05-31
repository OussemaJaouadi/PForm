#!/bin/bash

log_file="/var/www/html/access.log"  # Replace with the path to your log file

# Read log file and count requests and responses
total_requests=0
get_requests=0
post_requests=0
response_200=0
response_300=0
response_400=0
response_500=0

while IFS= read -r line; do
  # Count requests
  ((total_requests++))

  # Check request type
  if [[ $line == *"GET"* ]]; then
    ((get_requests++))
  elif [[ $line == *"POST"* ]]; then
    ((post_requests++))
  fi

  # Check response status
  if [[ $line == *" 200 "* ]]; then
    ((response_200++))
  elif [[ $line == *" 300 "* ]]; then
    ((response_300++))
  elif [[ $line == *" 400 "* ]]; then
    ((response_400++))
  elif [[ $line == *" 500 "* ]]; then
    ((response_500++))
  fi
done < "$log_file"

# Generate JSON output
json_output="{\"total_requests\": $total_requests, \"get_requests\": $get_requests, \"post_requests\": $post_requests, \"response_200\": $response_200, \"response_300\": $response_300, \"response_400\": $response_400, \"response_500\": $response_500}"

# Print JSON output
echo "$json_output"

