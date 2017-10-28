#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 17:34:02 2017

@author: triley
"""


import os
import errno
import re
from collections import namedtuple
# import sys
# from subprocess import check_call, run
import subprocess
from pprint import pprint


def get_proc_mounts():
    """ filter mounted for disks """
    mounts = {}  # mount points indexed by '/dev/sdxx'
    with open('/proc/mounts') as f:
        lines = f.readlines()

    for line in lines:
        if '/dev/' in line[:5]:  # then it's a disk device
            line = line.split()
            mounts[line[0]] = line[1]
    return mounts


def get_blkids():
    re_uuid = re.compile(b'UUID="(.*?)"')
    re_type = re.compile(b'TYPE="(.*?)"')
    re_puuid = re.compile(b'PARTUUID="(.*?)"')
    DiskPart = namedtuple('DiskPart', 'dev uuid ptype puuid mount_point')

    mounts = get_proc_mounts()
    blkids = {}  # device info indexed by '/dev/sdxx'
    result = subprocess.run('blkid', stdout=subprocess.PIPE)
    result.check_returncode()
    lines = result.stdout.split(b'\n')
    for line in lines:
        if b'/dev/' in line:  # ignore empty lines
            p = line.split(b':')
            dev = p[0].strip().decode("utf-8")  # python3 string, no blanks
            if dev in mounts.keys():
                mount = mounts[dev]
            else:
                mount = None
            blkids[dev] = DiskPart(
                dev=dev,  # keep dev info in the DiskPart instance
                uuid=re_uuid.search(p[1]).group(1).decode("utf-8"),
                ptype=re_type.search(p[1]).group(1).decode("utf-8"),
                puuid=re_puuid.search(p[1]).group(1).decode("utf-8"),
                mount_point=mount)

    return blkids
