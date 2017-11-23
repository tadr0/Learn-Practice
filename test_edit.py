#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  3 08:27:51 2017

@author: triley
"""

from pprint import pprint
import filecmp

import pytest

from partitions import PartitionTable
from edit import (rsync, edit_files, edit_file_names, chroot_mounts,
                  os_one_liner, is_mounted)


@pytest.fixture(scope='module')
def partition_table():
    partition_table = PartitionTable()
    partition_table.find_source_disk()
    print('\nsources:')
    pprint(partition_table.sources)
    partition_table.find_dest_disk()
    print('\ndests')
    pprint(partition_table.dests)
    partition_table.mount_dest_disk()
    return partition_table


@pytest.mark.slow
def test_edit_files(partition_table) -> None:
    rsync(partition_table)
    new_name = {}
    print('\ntest_edit_files')
    for name in edit_file_names:
        new_name[name] = f'{partition_table.dest_root_mount}{name}'
        print(name, new_name[name])
        assert filecmp.cmp(name, new_name[name])
    edit_files(partition_table)
    for name in edit_file_names:
        print(name, new_name[name])
        assert not filecmp.cmp(name, new_name[name])
        with open(new_name[name], 'rb', 0) as f:
            s = f.read().decode("utf-8")
            for uuid in [p.uuid for p in partition_table.sources.values()]:
                print(uuid)
                assert uuid not in s


def test_chroot_mounts(partition_table) -> None:
    drm = partition_table.dest_root_mount
    right_type = {
            'dev': 'udev',
            'dev/pts': 'devpts',
            'proc': 'proc',
            'sys': 'sysfs'}
    with chroot_mounts(partition_table):
        lines = os_one_liner(f'mount | grep {drm}')
        del lines[-1]  # trailing newline
        mount_types = {}
        for l in lines:
            mount_types[l.split()[2]] = l.split()[0]
        print('mounted on dest:')
        pprint(mount_types)
        for m in ['sys', 'proc', 'dev', 'dev/pts']:
            path = f'{drm}/{m}'
            assert is_mounted(path)
            assert path in mount_types.keys()
            assert mount_types[path] == right_type[m]

    print('check unmounted')
    for m in ['sys', 'proc', 'dev', 'dev/pts']:
        assert not is_mounted(f'{drm}/{m}')


if __name__ == '__main__':

    partition_table = PartitionTable()
    partition_table.find_source_disk()
    print('\nsources:')
    pprint(partition_table.sources)
    partition_table.find_dest_disk()
    print('\ndests')
    pprint(partition_table.dests)
    partition_table.mount_dest_disk()
#    # rsync(partition_table)
#    edit_files(partition_table)
#    test_chroot_mounts(partition_table)
    test_edit_files(partition_table)
