#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 13:07:58 2017

@author: triley
"""

# usage: run pytest from top of repo with no parameters eg.
# ~/src/Learn-Practice$ pytest


import re
# import os
import subprocess
# import sys
# from pprint import pprint
# from typing import Dict
from typing import Dict

from partitions import (
        DiskPart,
        PartitionTable)


def test_mounts(partition_table):
    mounts = partition_table.mounts
    # some sanity checks we can get independently from get_blkids
    assert '/' in mounts.keys()
    assert '/boot/efi' in mounts.keys()
    # tests that need apriori knowledge (not generally useful but fine for me)
    assert mounts['/boot/efi'].dev == '/dev/sda1'
    assert mounts['/'].dev == '/dev/sda2'
    # TODO
    # Check for stale mounts: You can actually get partitions that no longer
    # exist showing up in /proc/mounts after a USB move or coming out of sleep.


def test_partitions(partition_table):
    """ check that partion_table returns same info as /proc/partitions """

    # # independent tests
    # tests that work as non-root user
    # https://stackoverflow.com/questions/13857856/split-byte-string-into-lines
    #
    # get independent list of partitions from kernel

    re_part = re.compile(b' (sd[a-z][1-9])$')
    result = subprocess.run(
        'cat /proc/partitions',
        stdout=subprocess.PIPE,
        shell=True)
    result.check_returncode()
    lines_out = result.stdout.split(b'\n')  # .decode("utf-8")
    proc_parts = []  # partitions from /proc/partitions
    for line in lines_out:
        if re_part.search(line):
            proc_parts += [re_part.search(line).group(1).decode('utf8')]

    # Are patitions from proc_parts in partition_table
    for d in proc_parts:
        test = f'/dev/{d}'
        assert test in [v.dev for i, v in partition_table.partitions.items()]
    for key, value in partition_table.partitions.items():
        assert key == value.dev
        assert value.disk in key
        assert value.part_num in key
    # more tests


def test_mount_dest_disk():
    # mounted and unmounted
    pass


def test_find_dest_disk(partition_table):  # make partition_table and test

    # "all" possible states for 3 dsks to be in
    # (someday "all" might be a useful useful subset)
    disk_states: Dict[str, DiskPart] = {}
    for name in ['sda', 'sdb', 'sdc']:
        n = name[2]
        for part_number in ['1', '2']:
            full_name = f'/dev/{name}{part_number}'
            for ptype in ['vfat', 'junk', 'ext4']:
                t = ptype[0]
                for m, mount in {
                        'u': None,
                        'm': f'/mnt/{name}{part_number}',
                        'r': '/',
                        'b': '/boot/efi'}.items():
                    idx = f'sd{n}{part_number}_{t}_{m}'
                    test_part = DiskPart(
                        dev=full_name,
                        ptype=ptype,
                        mount_point=mount)
                    disk_states[idx] = test_part
                    # print(idx, full_name, ptype, mount, None)

    test_casess = [  # correct answers for each test case
        # efi mount, root mount,  list [diskpartition_ptype_mount]
        ('sdb2', 'sda1_v_b sda2_e_r sdb1_v_u sdb2_e_u'.split()),
        ('sdb2', 'sda1_v_b sda2_e_r sdb1_v_u sdb2_e_m'.split()),
        ('sdb2', 'sda1_v_b sda2_e_r sdb1_v_m sdb2_e_u'.split()),

        # from usb back to HDD
        ('sda2', 'sdb1_v_b sdb2_e_r sda1_v_u sda2_e_m'.split()),

        # list order shouldn't matter
        ('sda2', 'sda1_v_b sda2_e_r sdb1_v_u sdb2_e_m'.split()),

        # force not found
        (None, 'sda1_v_b sda2_e_r'.split()),
        # and more later
        ]

    for case in test_casess:
        partitions: Dict[str, DiskPart] = {}
        for idx in case[1]:
            part = disk_states[idx]
            partitions[part.dev] = part
        partition_table = PartitionTable(partitions=partitions)
        print(partition_table)
        if case[0]:
            right_disk = case[0][:3]
            mount_base = f'/mnt/{case[0]}'
            mount_efi = f'/mnt/{case[0]}/boot/efi'

        try:
            partition_table.find_dest_disk()
            dest_to_mount = partition_table.dests
            print(dest_to_mount)
            # they exist
            assert mount_base in dest_to_mount
            assert mount_efi in dest_to_mount
            # they are on the right disk
            assert dest_to_mount[mount_base].disk == right_disk
            assert dest_to_mount[mount_efi].disk == right_disk
            assert dest_to_mount[mount_efi].ptype == 'vfat'
        except:
            if case[0] is None:
                pass
            else:
                raise


# def test_find_dest_disk():


# some test that partitions are outomatically mounted for dest


def test_find_source_disk(partition_table):
    partition_table.find_source_disk()

    assert partition_table.sources['/'].dev == '/dev/sda2'
    assert partition_table.sources['/boot/efi'].dev == '/dev/sda1'


if __name__ == '__main__':
    test_partitions(PartitionTable())
    test_find_dest_disk(PartitionTable())
    # test_mounts()
