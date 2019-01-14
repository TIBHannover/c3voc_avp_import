#!/bin/bash

mkdir -pv videos && ./get_attachments.py $1 --verbose && ./transfer_to_tib-av-portal.py $1 --verbose
