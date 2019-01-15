#!/bin/bash

mkdir -pv videos && ./get_attachments.py $1 --verbose && ./get_videos_and_xml.py $1 --verbose
