#!/bin/bash

# check utility
message=$(pkill -f /usr/lib/firefox/firefox)

# echo message
echo "All Firefox must die"
echo $message

# if you want allways have a OK response
exit 0
