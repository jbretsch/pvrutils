pvrutils
========

Provides utilities for personal video recorders (PVRs) (e.g. a Dreambox).

## Cleanup

At the moment there is only one utility script: `cleanup.py`. It solves the
following problem.

If you let your PVR automatically record all your favorite TV shows and films
then its hard drive will eventually fill up. So from time to time you have to 
manually delete old recordings to make room for new recordings. This is a chore.
A chore that can be easily forgotten. And then you come home from a stressful
day looking forward to watching the brand new episode of your favorite TV show
only to find your PVR _not_ having recorded it because its hard drive was full.

With `cleanup.py` this will never ever happen to you again.

Just copy `cleanup.py` to your PVR and create a cronjob that runs it every night.
`cleanup.py` will then delete your old recordings (starting with the oldest one)
until there is again a configurable amount of free space available on your hard
drive.

### Usage

Here is what `cleanup.py --help` says:

```
Cleans up a given directory until a given amount of free space is available in
this directory.

Usage: cleanup.py [OPTIONS]

Options:
  -h, --help          Show this help message.

  -d DIRECTORY        Specifies the directory to clean up.
                      The default is /hdd/media/movie.

  -s MIN_AVAIL_SPACE  Specifies the minimal amount of space in megabytes you
                      wish to have available in DIRECTORY.
                      The default is 51200 MB (50 GB).

If MIN_AVAIL_SPACE is already available in DIRECTORY then this script
deletes nothing and exists with a corresponding message.

Otherwise the script cleans up DIRECTORY as follows:
  1. It recursively finds all files in the given directory.
  2. It deletes the oldest files (according to their modification time (mtime))
     until MIN_AVAIL_SPACE is available in DIRECTORY or there are no more
     files to delete.

The script does NOT delete any (sub) directories.

Examples:
  ./cleanup.py
  ./cleanup.py -d /path/to/my/recordings
  ./cleanup.py -d /path/to/my/recordings -s 12000
```

### Installation

If you have a `wget` or `curl` with HTTPS support installed on your PVR then telnet into your PVR and download `cleanup.py` directly, e.g.,

    $ telnet dm8000
    $ wget https://raw.github.com/jbretsch/pvrutils/master/cleanup.py

Otherwise download `cleanup.py` first, upload it to your PVR, and telnet into your PVR afterwards e.g.

    $ wget https://raw.github.com/jbretsch/pvrutils/master/cleanup.py
    $ ftp -u ftp://root@dm8000/ cleanup.py
    $ telnet dm8000

Make it executable.

    $ chmod u+x cleanup.py

Run `cleanup.py` manually to test it. You have to know where your recordings
reside. (In Dreamboxes this is usually `/hdd/media/movie`). And you have to decide
how much free space there should be available after each `cleanup.py` run. If you
are happy with the defaults (recordings in `/hdd/media/movie` and at least 50GB
available space), then you can run `cleanup.py` without any further options.

    $ ./cleanup.py

Otherwise use the `-d` or `-s` option to specify a different directory to clean up
or a different desired amount of free space. See the usage above for details.

Now create a cronjob to let `cleanup.py` run periodically. For example, call

    $ crontab -e

and add the line

    0 3 * * * /home/root/cleanup.py

to the file that opens if `cleanup.py` resides in `/home/root` and you want it to be
run every night at 3 o'clock.

See if your cron daemon actually runs by checking if

    $ ps aux | grep cron | grep -v grep

outputs anything. If not then find out how to start it and start it.
