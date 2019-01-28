#!/bin/bash

mkdir -pv videos
if [[ $1 == "-l" ]]; then
    rand="schedule_"$RANDOM".xml"
    wget $2 -O ${rand} && ./get_attachments.py ${rand} --verbose && ./get_videos_and_xml.py ${rand} --verbose
    rm -f ${rand}
elif [[ $1 == "-f" ]]; then
    ./get_attachments.py $2 --verbose && ./get_videos_and_xml.py $2 --verbose
else
    echo "Please use one of the following options:
    -l \"URL to remote schedule\"
    -f \"path to local schedule\""
fi
