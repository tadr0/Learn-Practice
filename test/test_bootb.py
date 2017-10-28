#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 13:07:58 2017

@author: triley
"""

# usage: run pytest from top of repo with no parameters eg.
# ~/src/Learn-Practice$ pytest

import os
import subprocess
import sys
import uuid


from src.bootb.update_bootb import (get_blkids, check_mount_point,
    find_sources, get_proc_mounts, find_dest_disk)


def test_get_proc_mounts():
    mounts = get_proc_mounts()
    # some sanity checks we can get independently from get_blkids
    assert '/' in mounts.values()
    assert '/boot/efi' in mounts.values()
    # tests that need apriori knowledge (not generally useful but fine for me)
    assert mounts['/dev/sda1'] == '/boot/efi'
    assert mounts['/dev/sda2'] == '/'


def test_get_blkids():
    sources = get_blkids()
    # independent
    # is each partition from blkid also in /proc/partitions ?
    result = subprocess.run(
        'cat /proc/partitions',
        stdout=subprocess.PIPE,
        shell=True)
    result.check_returncode()
    response = result.stdout.decode("utf-8")
    print(sources.keys())
    for part in sources.keys():
        print(part)
        part = part[5:9]  # strip off /dev/
        assert part in response
    # tests that need apriori knowledge


def test_find_sources():
    mounts = find_sources()
    # tests that need apriori knowledge
    assert mounts['/dev/sda1'] == '/boot/efi'
    assert mounts['/dev/sda2'] == '/'


def test_find_dest_disk():
    dest = find_dest_disk()
    # tests that need apriori knowledge
    assert dest['/boot/efi'] == ['/dev/sdc1']
    assert dest['/'] == '/dev/sda2'


def test_mount_point_new():
    """ check_mount_point should make the dir if it's not there
        Gamble on the non-existence of a weird directory name. """
    dir_name = f'/tmp/dir_{uuid.uuid1()}'
    check_mount_point(dir_name)
    assert os.path.isdir(dir_name)
    os.rmdir(dir_name)  # context manager here ?