#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 13:07:58 2017

@author: triley
"""


import subprocess


from update_bootb import (get_blkids, get_proc_mounts)


def test_get_proc_mounts():
    """ At least something works. """
    assert '/' in get_proc_mounts().values()
    assert '/boot/efi' in get_proc_mounts().values()
    assert '/dev/sda1' in get_proc_mounts().keys()
    assert '/dev/sda2' in get_proc_mounts().keys()


def test_get_blkids():

    """ some sanity checks we can get independently from get_blkids """
    sources = get_blkids()

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
