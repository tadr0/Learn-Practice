#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 13:07:58 2017

@author: triley
"""

import os
import subprocess
import sys

#src_dir = os.path.dirname(os.path.abspath('./src/bootb/update_bootb.py'))
#if not src_dir in sys.path:
#    sys.path.append(src_dir)
#print(sys.path)

# run pytest from top of repo
from src.bootb.update_bootb import get_blkids, get_proc_mounts


def test_get_proc_mounts():
    mounts = get_proc_mounts()
    # some sanity checks we can get independently from get_blkids
    assert '/' in mounts.values()
    assert '/boot/efi' in mounts.values()
    # tests that need apriori knowledge (not generally useful but fine for me)
    assert '/dev/sda1' in mounts.keys()
    assert '/dev/sda2' in mounts.keys()


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
