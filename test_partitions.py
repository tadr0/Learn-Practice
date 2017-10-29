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


from update_bootb import (
        DiskPart,
        partition_table,  # <-- live when imported
        find_source_disk,
        find_dest_disk)

def test_get_proc_mounts():
    mounts = partition_table.mounts
    # some sanity checks we can get independently from get_blkids
    assert '/' in mounts.values()
    assert '/boot/efi' in mounts.values()
    # tests that need apriori knowledge (not generally useful but fine for me)
    assert mounts['/dev/sda1'] == '/boot/efi'
    assert mounts['/dev/sda2'] == '/'


def test_proc_partitions():
    print(partition_table.partitions.keys())
    """ check that partion_table returns same info as /proc/paretitions """

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
    proc_parts = []
    for line in lines_out:
        if re_part.search(line):
            proc_parts += [re_part.search(line).group(1).decode('utf8')]
    print(proc_parts)
    # Are patitions from proc_parts in partition_table
    for d in proc_parts:
        test = f'/dev/{d}'
        assert test in [v.dev for i, v in partition_table.partitions.items()]
    for key, value in partition_table.partitions.items():
        assert key == value.dev
    # more tests


def test_find_source_disk():
    mounts = partition_table.mounts
    # tests that need apriori knowledge
    assert mounts['/dev/sda1'] == '/boot/efi'
    assert mounts['/dev/sda2'] == '/'


def test_find_dest_disk():
    # most typical
    def any_part(name, ptype, mount_point, fake_data):
        return DiskPart(
            dev=None,
            uuid=None,
            ptype=None,
            puuid=None,
            mount_point=None)

    # make all the combinations without having to check them by hand
    # partitions = {}
    disk_states = {}
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
        ('sdb1', 'sdb2', 'sda1_v_b sda2_e_r sdb1_v_u sdb2_e_u'.split()),
        ('sdb1', 'sdb2', 'sda1_v_b sda2_e_r sdb1_v_u sdb2_e_m'.split()),

        # from usb back to HDD
        ('sda1', 'sda2', 'sdb1_v_b sdb2_e_r sda1_v_u sda2_e_m'.split()),

        # list order shouldn't matter
        ('sda1', 'sda2', 'sda1_v_b sda2_e_r sdb1_v_u sdb2_e_m'.split()),

        # and more later
        ]

    for case in test_casess:
        potentials = [disk_states[idx] for idx in case[2]]
        try:
            dest = find_dest_disk(potentials)
            assert dest['/boot/efi'] == f'/dev/{case[0]}'
            assert dest['/'] == f'/dev/{case[1]}'
        except:
            if case[1] is None:
                pass


# some test that partitions are outomatically mounted for dest


def test_find_source_disk():
    source = find_source_disk(partition_table)

    assert source['/'].dev == '/dev/sda2'
    assert source['/boot/efi'].dev == '/dev/sda1'


if __name__ == '__main__':
    test_find_source_disk()
