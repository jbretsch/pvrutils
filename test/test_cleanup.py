#!/usr/bin/python

import unittest
import shutil
import os
import cleanup
import sys

class RedirectStdStreams(object):
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

class TestCleanup(unittest.TestCase):

    testdir = os.tmpnam()

    def setUp(self):
        if (os.path.exists(self.testdir)):
            shutil.rmtree(self.testdir)
        os.makedirs(self.testdir)

    def tearDown(self):
        shutil.rmtree(self.testdir)

    def create_file(self, name, size, ts):
        name = os.path.join(self.testdir, name)

        dirname = os.path.dirname(name)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(name, "wb") as file:
            file.truncate(size * 1024 * 1024)

        os.utime(name, (ts, ts))

    def cleanup(self, size, dirs=None):
        avail_space = cleanup.avail_space_in_mb(self.testdir)
        target_avail_space = avail_space + size
        sys.argv = [ 'cleanup.py', '-s', str(target_avail_space)]

        if dirs is None:
            sys.argv.append(self.testdir)
        else:
            for d in dirs:
                sys.argv.append(os.path.join(self.testdir, d))

        devnull = open(os.devnull, 'w')
        with RedirectStdStreams(stdout=devnull, stderr=devnull):
            return cleanup.main()

    def exists(self, path):
        return os.path.exists(os.path.join(self.testdir, path))

    def test_target_free_space_equals_file_sizes(self):
        self.create_file(name = 'foo', size = 4, ts = 1)
        self.create_file(name = 'bar', size = 4, ts = 2)
        exit_code = self.cleanup(size = 8)
        self.assertEquals(exit_code, 0)
        self.assertFalse(self.exists('foo'))
        self.assertFalse(self.exists('bar'))

    def test_target_free_space_greater_than_file_sizes(self):
        self.create_file(name = 'foo', size = 4, ts = 1)
        self.create_file(name = 'bar', size = 4, ts = 2)
        exit_code = self.cleanup(size = 10)
        self.assertEquals(exit_code, 0)
        self.assertFalse(self.exists('foo'))
        self.assertFalse(self.exists('bar'))

    def test_target_free_space_lesser_than_file_sizes(self):
        self.create_file(name = 'foo', size = 4, ts = 1)
        self.create_file(name = 'bar', size = 4, ts = 2)
        exit_code = self.cleanup(size = 6)
        self.assertEquals(exit_code, 0)
        self.assertFalse(self.exists('foo'))
        self.assertFalse(self.exists('bar'))

    def test_target_free_space_lesser_than_file_sizes_2(self):
        self.create_file(name = 'foo', size = 4, ts = 1)
        self.create_file(name = 'bar', size = 4, ts = 2)
        exit_code = self.cleanup(size = 4)
        self.assertEquals(exit_code, 0)
        self.assertFalse(self.exists('foo'))
        self.assertTrue(self.exists('bar'))

    def test_target_free_space_already_met(self):
        self.create_file(name = 'foo', size = 4, ts = 1)
        self.create_file(name = 'bar', size = 4, ts = 2)
        exit_code = self.cleanup(size = 0)
        self.assertEquals(exit_code, 0)
        self.assertTrue(self.exists('foo'))
        self.assertTrue(self.exists('bar'))

    def test_target_free_space_already_met_2(self):
        self.create_file(name = 'foo', size = 4, ts = 1)
        self.create_file(name = 'bar', size = 4, ts = 2)
        exit_code = self.cleanup(size = -10)
        self.assertEquals(exit_code, 0)
        self.assertTrue(self.exists('foo'))
        self.assertTrue(self.exists('bar'))

    def test_only_delete_from_given_directories(self):
        file1 = os.path.join('d1', 'foo')
        file2 = os.path.join('d2', 'bar')
        self.create_file(name = file1, size = 4, ts = 1)
        self.create_file(name = file2, size = 4, ts = 2)
        exit_code = self.cleanup(size = 8, dirs=['d1'])
        self.assertEquals(exit_code, 0)
        self.assertFalse(self.exists(file1))
        self.assertTrue(self.exists(file2))

    def test_files_on_command_line_are_ignored(self):
        file1 = os.path.join('d1', 'foo')
        file2 = os.path.join('d2', 'bar')
        file3 = 'quuz'
        self.create_file(name = file1, size = 4, ts = 1)
        self.create_file(name = file2, size = 4, ts = 2)
        self.create_file(name = file3, size = 4, ts = 3)
        exit_code = self.cleanup(size = 8, dirs=['d1', file3])
        self.assertEquals(exit_code, 0)
        self.assertFalse(self.exists(file1))
        self.assertTrue(self.exists(file2))
        self.assertTrue(self.exists(file3))

    def test_non_existing_directories_on_command_line_are_ignored(self):
        file1 = os.path.join('d1', 'foo')
        self.create_file(name = file1, size = 4, ts = 1)
        exit_code = self.cleanup(size = 8, dirs=['d1', 'd2'])
        self.assertEquals(exit_code, 0)
        self.assertFalse(self.exists(file1))

    def test_subdirs_are_not_deleted(self):
        file1 = os.path.join('d1', 'foo')
        file2 = os.path.join('d1', 'dd1', 'quuz')
        self.create_file(name = file1, size = 4, ts = 1)
        self.create_file(name = file2, size = 4, ts = 2)
        exit_code = self.cleanup(size = 8)
        self.assertEquals(exit_code, 0)
        self.assertFalse(self.exists(file1))
        self.assertFalse(self.exists(file2))
        self.assertTrue(self.exists(os.path.dirname(file1)))
        self.assertTrue(self.exists(os.path.dirname(file2)))

    def test_exists_when_no_existing_directory_is_given(self):
        file1 = os.path.join('d1', 'foo')
        self.create_file(name = file1, size = 4, ts = 1)
        exit_code = self.cleanup(size = 8, dirs=['d2'])
        self.assertEquals(exit_code, 1)
        self.assertTrue(self.exists(file1))


if __name__ == '__main__':
    unittest.main()
