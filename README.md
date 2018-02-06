# CCC Download Script

This script collection transfers videos from CCC conferences, according to the given schedule, as well as their metadata and supplements (e.g., PDF slides) to the FTP server of the TIB AV Portal.

For proper working of the scripts, ./schedule.xml and ./data/schedule_[conference name].xml files (e.g., schedule_34c3.xml) should be available. FTP username and password are required as well and should be adapted in the configuration.

## Usage

With FTP upload:

    ./import.sh

Without FTP (dry run, only metadata and supplements will be downloaded):

    ./dryrun.sh

All of the metadata and supplements will be saved into the 'temp' directory, which will be created if not exists by either of the shell scripts.
