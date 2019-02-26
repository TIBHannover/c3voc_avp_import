# C3VOC <-> AV Portal Download Script

This script collection downloads [videos from CCC conferences](https://media.ccc.de/), 
according to the given schedule, as well as their metadata and supplements (e.g., PDF slides) 
for the [TIB AV Portal](https://av.tib.eu/).

For proper working of the scripts, a schedule file of the conference, the "Fahrplan", usually: `schedule.xml`,
should be available and put into the root directory (but any other path works too). 
I.e., the final directory structure, before the download can start, should be something like the following:

    ccc_avp_import/
    ├── ccc_download
    ├── get_attachments.py
    ├── get_videos_and_xml.py
    ├── install.sh
    ├── README.md
    └── schedule.xml

A list of currently published schedules is available 
under [https://c3voc.de/wiki/events_tib](https://c3voc.de/wiki/events_tib).

It is also possible to use the URL of the schedule, e.g., by copying it from the list above. In this case, the schedule will be temporarily saved and deleted after the videos have been downloaded. (see also Usage section)

## Dependencies

You will also need to install additional python modules to run the scripts. You can install them either with `pip` 
or the package manager of your OS. In the best case, you have all of them 
installed already, so that the script won't complain. Following dependencies are usually needed to be installed on a "clean" Ubuntu or Debian machine:

    sudo apt install python-pycurl
    pip install requests lxml python-magic
    
## Install

    ./install.sh

**Installation is optional**

The scripts will be installed in your `/usr/local/bin`, however you can modify the path in `install.sh`.

## Usage

If installed

    ccc_download [option] [schedule]
    
If NOT installed

    ./ccc_download [option] [schedule]

### Available Options

    -f (path to local schedule)
    -l (URL of the schedule)

### Examples

Remote schedule (will be automatically removed after the video download process is complete)

    ./download.sh -l https://fahrplan.events.ccc.de/congress/2018/Fahrplan/schedule.xml

Download and use local schedule

    wget https://fahrplan.events.ccc.de/congress/2018/Fahrplan/schedule.xml
    ./download.sh -f schedule.xml

All of the videos, metadata, and supplements will be saved into the `videos_c3voc` directory, 
which will be created if it doesn't exist yet.
