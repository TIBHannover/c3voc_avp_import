#!/bin/bash

ulb="/usr/local/bin"

for script in ccc_download get_attachments.py get_videos_and_xml.py; do
    ln -s $PWD"/"${script} ${ulb}/${script}
done
