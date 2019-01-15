# C3VOC <-> AV Portal Download Script

This script collection downloads [videos from CCC conferences](https://media.ccc.de/), 
according to the given schedule, as well as their metadata and supplements (e.g., PDF slides) 
for the [TIB AV Portal](https://av.tib.eu/).

For proper working of the scripts, a schedule file of the conference, the "Fahrplan", usually: `schedule.xml`,
should be available and put into the root directory (but any other path works too). 
I.e., the final directory structure, before the download can start, should be something like the following:

    ccc_avp_import/
    ├── download.sh
    ├── get_attachments.py
    ├── get_videos_and_xml.py
    ├── README.md
    └── schedule.xml

A list of currently published schedules is available 
under [https://c3voc.de/wiki/events_tib](https://c3voc.de/wiki/events_tib).

You will also need to install additional python modules to run the scripts. You can install them either with `pip` 
or the package manager of your OS, e.g., `sudo apt install python-pycurl`. In the best case, you have all of them 
installed already, so that the script won't complain.

## Usage

    ./download.sh <path to schedule file>

All of the videos, metadata, and supplements will be saved into the `videos` directory, 
which will be created if it doesn't exist yet.
