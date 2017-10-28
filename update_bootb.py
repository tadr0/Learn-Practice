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


def find_sources():
    """ Find out where to copy from and return a reverse lookup, sources. """
    mounts = get_proc_mounts()  # indexed by '/dev/sdxx/
    all_parts = get_blkids()  # indexed by '/dev/sdxx/
    sources = {}

    for part in mounts.keys():
        for mount in ['/', '/boot/efi']:
            if mounts[part] == mount:
                sources[mount] = all_parts[part]
    # BIST: Make sure we have two source partitions with correct mounts.
    k = sources.keys()
    assert len(k) == 2, 'wtf: Failed to find sources.'
    for mnt in k:
        msg = 'wtf: sources mis-mapped'
        assert sources[mnt].mount_point == mnt, msg
    assert sources['/boot/efi'].ptype == 'vfat'
    return sources


def find_dest_disk():
    potentials = get_blkids()  # idexed by '/dev/sdxx'
    mounts = get_proc_mounts()  # idexed by '/dev/sdxx'

    efi_candidates = []
    root_candidates = []
    # Find available vfat partitions for EFI.
    efi_disks = []
    for p in potentials.keys():  # exclude mounted EFI

        if potentials[p].ptype == 'vfat' and ('/boot/efi' not in mounts[p]):
            efi_candidates += [potentials[p]]
            # '/' has to be on the same disk as EFI.
            efi_disks += [p[5:8]]  # disk canddates

    for p in potentials.keys():
        # print(p)
        disk = p[5:8]
        if disk in efi_disks:
            # print(f'checking {p}')
            if (p not in mounts.keys()):  # p not mounted is a good sign
                # print(f'{p} not mounted')
                root_candidates[p] = potentials[p]
            else:  # if mounted, cant be '/'
                # print(f'mounts[{p}] = {mounts[p]}')
                if potentials[p].ptype != 'vfat':
                    root_candidates += [potentials[p]]

    if len(root_candidates) == 1:
        return {'/boot/efi': efi_candidates[0], '/': root_candidates[0]}
#    elif len(root_candidates) == 0:
#        assert False, 'No install candidates found'
#    else:
#        assert False, 'TODO fix me later by allowing choice from candidates'



def check_mount_point(mount_point):
    if not os.path.isdir(mount_point):
        try:
            os.mkdir(mount_point)
        except OSError as e:
            if e.errno == errno.EEXIST:  # seems impossible
                pass
            elif e.errno == errno.EACCES:
                assert False, 'Must be run as root user'
            elif e.errno == 2:  # TODO look up non-numeric
                # because we got crap for mount_point ?
                assert False, f'{mount_point} not found making mount_point'
            else:
                pprint(e)
                assert False, f'wtf checking mount_point {mount_point}'
        # print(f'created mount point {mount_point}')
        return
    else:
        pass


if __name__ == '__main__':
    pprint(find_dest_disk())
