#!/bin/bash

mkdir -pv temp && ./get_attachments.py --verbose && ./transfer_to_tib-av-portal.py schedule.xml --verbose --nobaseurl
