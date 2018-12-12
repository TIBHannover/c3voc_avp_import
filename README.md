# C3VOC <-> AV Portal Download Script

This script collection downloads [videos from CCC conferences](https://media.ccc.de/), according to the given schedule, as well as their metadata and supplements (e.g., PDF slides) for the [TIB AV Portal](https://av.tib.eu/).

For proper working of the scripts, `./schedule.xml` and `./data/schedule_[conference name].xml` files (e.g., `schedule_34c3.xml`) should be available. I.e., the final directory structure should be something like the following:

    ccc_avp_import/
    ├── data
    │   └── schedule_34c3.xml
    ├── download.sh
    ├── get_attachments.py
    ├── README.md
    ├── schedule.xml
    └── transfer_to_tib-av-portal.py

## Usage

    ./download.sh

All of the metadata and supplements will be saved into the 'temp' directory, which will be created if it doesn't exist yet.
