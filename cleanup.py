#!/usr/bin/python

"""Cleans up a given directory until a given amount of free space is available
   in this directory. See the usage method below for further details.

   Copyright (c) 2014 Jan Bretschneider <jan@bretti.net>
   License: The MIT License (http://opensource.org/licenses/MIT)
"""


def usage():
    """Prints the usage information of this script."""

    print '''
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
'''.strip()


import sys
import os
import getopt


class File:
    """A simple file class. A File has a path and a modification time. The
    modification time is stored as seconds since the epoch. 
       
       Usage:
          >>> f = File('/tmp/foo', 1395506398)
          >>> f.path
          '/tmp/foo'
          >>> f.mtime
          1395506398
    """ 

    def __init__(self, path, mtime):
        """Creates a File with the given path and modification time."""
        self.path = path
        self.mtime = mtime

    def __repr__(self):
        """Print File('/tmp/foo', 1395506398) as ('/tmp/foo', 1395506398)."""
        return repr((self.path, self.mtime))


def process_dir(all_files, dirname, filenames):
    """Is called by find_files_sorted_by_mtime() for every found directory
       while recursively scanning a parent directory.

       Adds all files given in filenames to all_files. all_files contains only
       File objects. All fields (path and mtime) of all File objects are set.

       Parameters:
         all_files (list of File objects): Accumulates all found files.
         dirname (string):                 Name of the current directory.
         filenames (list of strings):      Names of all files in the current
                                           directory.
    """
    for filename in filenames:
        fullpath = os.path.join(dirname, filename)

        if not os.path.isfile(fullpath):
            continue

        mtime = os.path.getmtime(fullpath)
        file = File(fullpath, mtime)
        all_files.append(file)


def find_files_sorted_by_mtime(directory):
    """Recursively scans the given directory and returns a list of all found
       files.

       Parameters:
         directory (string) - The directory to scan.

       Returns:
         A list of File objects. The list is sorted by the modification time
         (mtime) of the files with the oldest file at index 0. If no files were
         found the returned list is empty.
    """
    files=[]
    os.path.walk(directory, process_dir, files)
    return sorted(files, key=lambda file: file.mtime)
    

def avail_space_in_mb(directory):
    """Returns the amount of megabytes that are free (available) in the given
       directory.

       Parameters:
         directory (string) - The directory to check.
    """ 
    st = os.statvfs(directory)
    return st.f_frsize*st.f_bavail/1024/1024


def cleanup(path, min_avail_space):
    """Cleans up the given path until there is at least the given minimal
       amount of space available. The cleanup method is described at the top of
       this script.
       
       Parameters:
         path (string)         - The directory that should be cleaned up.
         min_avail_space (int) - The amount of free space in megabytes that
                                 should be available in the given directory.
    """

    if avail_space_in_mb(path) >= min_avail_space:
        print "There is enough space available: %d MB" % avail_space_in_mb(path)
        print "No cleanup necessary. Exiting."
        return

    # all_files contains a list of all Files in path.
    all_files = find_files_sorted_by_mtime(path)

    # Delete the oldest file until there is enough space available.
    while avail_space_in_mb(path) < min_avail_space and len(all_files) > 0:
        file = all_files.pop(0)
        print "Removing %s" % file.path
        os.remove(file.path)
        print "Space now available: %d MB." % avail_space_in_mb(path)

    # Report if there is not enough space available and no more file to delete.
    if avail_space_in_mb(path) < min_avail_space and len(all_files) == 0:
        print "There is NOT enough space available: %d MB" % \
              avail_space_in_mb(path)
        print "And there are no more files to delete."


def parse_opts(directory, min_avail_space):
    """Parses the command line options passed to this script.
       If this script is called with -h or --help then this method prints the
       usage information to stdout and exits the scripts.
       Otherwise it returns the directory and minimal available space given on
       the command line or the default values for both options passed into this
       method.

       Parameters:
         directory (string):    default value for the directory to clean.
         min_avail_space (int): default value for the desired minimal available
                                space.

       Returns:
         (directory, min_avail_space) where directory and min_avail_space are
         the values given on the command line or the default values.
    """

    # We use getopt to parse the command line arguments because argparse or
    # optparse are not available on Dreamboxes.
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:s:", ["help"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt == '-d':
            directory = arg
        elif opt == '-s':
            try:
                min_avail_space = int(arg)
            except ValueError as err:
                print "You have given the option -d %s. " \
                      "But '%s' is not a number." % (arg, arg)
                print "Run %s --help for help." % sys.argv[0]
                sys.exit(1)
        else:
            assert False, "unhandled option"

    print "You requested to have %d MB available in %s." % (min_avail_space,\
                                                           directory)
    return directory, min_avail_space


def main():
    """Main method of this script."""

    # Use the directory that contains recordings on Dreamboxes as default.
    directory = '/media/hdd/movie'

    # Per default we want to have 50GB of free space.
    min_avail_space = 50*1024

    # Override defaults with values given on the command line.
    directory, min_avail_space = parse_opts(directory, min_avail_space)

    # Do the actual cleanup.
    cleanup(directory, min_avail_space)

if __name__ == '__main__':
    main()
