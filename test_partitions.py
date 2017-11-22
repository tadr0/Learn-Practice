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
import pytest
# import sys
# from pprint import pprint
# from typing import Dict
from collections import OrderedDict

from partitions import (
        DiskPart,
        PartitionTable)


@pytest.fixture(scope='module')
def os_partition_table():
    return PartitionTable()


def os_one_liner(cmd):
    """ one cli line that you already know is right """
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        shell=True)
    result.check_returncode()
    return result.stdout.decode("utf-8").split('\n')


def test_mounts(os_partition_table):
    mounts = os_partition_table.mounts
    # some sanity checks we can get independently from get_blkids
    assert '/' in mounts.keys()
    assert '/boot/efi' in mounts.keys()
    # tests that need apriori knowledge (not generally useful but fine for me)
    assert mounts['/boot/efi'].dev == '/dev/sda1'
    assert mounts['/'].dev == '/dev/sda2'
    # TODO
    # Check for stale mounts: You can actually get partitions that no longer
    # exist showing up in /proc/mounts after a USB move or coming out of sleep.


def test_partitions(os_partition_table):
    """ check that partion_table returns same info as /proc/partitions """

    # # independent tests
    # tests that work as non-root user
    #
    # get independent list of partitions from kernel

    re_part = re.compile(' (sd[a-z][1-9])$')
    lines_out = os_one_liner('cat /proc/partitions')
    proc_parts = []  # partitions from /proc/partitions
    for line in lines_out:
        if re_part.search(line):
            proc_parts += [re_part.search(line).group(1)]

    # Are patitions from proc_parts in partition_table
    for d in proc_parts:
        test = f'/dev/{d}'
        assert test in [v.dev for i, v in os_partition_table.partitions.items()]
    for key, value in os_partition_table.partitions.items():
        assert key == value.dev
        assert value.disk in key
        assert value.part_num in key
    # more tests


def mock_pt(descriptions: str) -> PartitionTable:
    """ make a mock partition table from a a string describing
        partitions and their state.
    """
    mounts: OrderedDict[str, DiskPart] = {}
    partitions: OrderedDict[str, DiskPart] = {}
    code_to_ptype = {'e': 'vfat', 'r': 'ext4'}
    code_to_mount_point =  {'e': '/', 'r': '/boot/efi'}
    for i, pt_description in enumerate(descriptions.split()):
        p = DiskPart(dev=f'/dev/{pt_description[:5]}')
        code = pt_description[-1]
        p.ptype = code_to_ptype[code]
        if i < 2:  # then we magically make it mounted as the running partitions
            p.mount_point = code_to_mount_point[code]
            mounts[p.mount_point] = p
        # else assume it's unmounted leave as None
        print('mp', p)
    pt = PartitionTable(partitions=partitions, mounts=mounts)
    print('\nin mock_pt returning:', pt)
    return pt


@pytest.fixture(
        # scope='test',
        params=[
            # (dest '/', available disk partitions)
            #         first two are source, rest are potential dests

            ('sdb2', 'sda1_e sda2_r sdb1_e sdb2_r'),
#           ('sdb2', 'sda1_e sda2_r sdb1_v sdb2_e'),
#            ('sdb2', 'sda1_v sda2_e sdb1_v sdb2_e'),
#
#            # from usb back to HDD
#            ('sda2', 'sdb1_v_b sdb2_e_r sda1_v_u sda2_e_m'),
#
#
#            # force not found
#            (None, 'sda1_v_b sda2_e_r'),
#            # and more later
            ])
def test_case(request):
    return request.param


def test_find_dest_disk(test_case):
    (right_answer, descriptions) = test_case
    mk_partition_table = mock_pt(descriptions)
    print('\nBeforeFind')
    print(mk_partition_table)
    mk_partition_table.find_dest_disk()
    print('\nAfterFind\n')
    print(mk_partition_table)
    for mnt in mk_partition_table.dests:
        print('mnt =', mnt)
        dev = mk_partition_table.partitions[f'/dev/{right_answer}']
        print('dev =', dev, mk_partition_table.partitions[dev])
        assert right_answer in mnt


def test_mount_dest_disk():
    # mounted and unmounted
    pass


def test_find_source_disk(os_partition_table):
    os_partition_table.find_source_disk()
    assert os_partition_table.sources['/'].dev == '/dev/sda2'
    assert os_partition_table.sources['/boot/efi'].dev == '/dev/sda1'


if __name__ == '__main__':
    test_partitions(PartitionTable())
    # test_find_dest_disk(PartitionTable())
    # test_mounts(PartitionTable())
