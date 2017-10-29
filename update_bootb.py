#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 17:34:02 2017

@author: triley
"""


import re
# import sys
# from subprocess import check_call, run
import subprocess
from pprint import pprint

import os
import errno


class DiskPart(object):
    """  isolate hardware from everything else, abstract partitions
    """

    def __init__(
            self,
            dev='',
            uuid='',
            ptype='',
            puuid='',
            mount_point='',
            fake_data=None):

        self.dev = dev
        self.disk = dev[5:8],
        self.part_num = dev[8],
        self.uuid = uuid
        self.ptype = ptype
        self.puuid = puuid
        self.mount_point = mount_point
        self.fake_data = fake_data

    def __str__(self):
        s = []
        s += ['  H']
        s += [self.dev if self.dev else ' '*9]
        s += [self.ptype[:4] if self.ptype else ' '*4]
        s += [self.uuid[:8] if self.uuid else ' '*8]
        s += [self.mount_point if self.mount_point else 'None']
        return ' '.join(s)

    def __repr__(self):
        self.__str__()  # cheat


class PartitionTable(object):
    """ Abstract Partition Table

        really info about table and maybe setup for MagicMock?
    """

    def __init__(self):
        # mount points, partitions indexed by '/dev/sdxx'
        self.mounts = {}
        self.partitions = self.get_blkids()

    def __str__(self):
        s = ['Partition Table:']
        for name, part in self.partitions.items():
            s += [part.__str__()]
        return '\n'.join(s)

    def __repr__(self):
        self.__str__()

    def add_mok_partition():
        pass

    def get_blkids(self):
        """ This seems to work fine for non-root user, provided that you poke
            it first with a 'sudo blkid' at the command line once. Hmm ...
        """
        re_uuid = re.compile(b'UUID="(.*?)"')
        re_type = re.compile(b'TYPE="(.*?)"')
        re_puuid = re.compile(b'PARTUUID="(.*?)"')

        mounts = self.get_proc_mounts()
        blkids = {}  # device info indexed by '/dev/sdxx'
        result = subprocess.run('blkid', stdout=subprocess.PIPE)
        result.check_returncode()
        lines = result.stdout.split(b'\n')
        for line in lines:
            if b'/dev/' in line:  # ignore empty lines
                p = line.split(b':')
                dev = p[0].strip().decode("utf-8")  # python3 string, no blanks
                uuid_m = re_uuid.search(p[1])
                ptype_m = re_type.search(p[1])
                puuid_m = re_puuid.search(p[1])
                if dev in mounts.keys():
                    mount = mounts[dev]
                else:
                    mount = None
                blkids[dev] = DiskPart(
                    dev=dev,  # keep dev info in the DiskPart instance
                    uuid=uuid_m.group(1).decode("utf-8") if uuid_m else None,
                    ptype=ptype_m.group(1).decode("utf-8") if ptype_m else None,
                    puuid=puuid_m.group(1).decode("utf-8") if puuid_m else None,
                    mount_point=mount,
                    fake_data=None)
                # print(blkids[dev])
        return blkids

    def get_proc_mounts(self):
        """ filter mounted for disks """
        with open('/proc/mounts') as f:
            lines = f.readlines()
        for line in lines:
            if '/dev/' in line[:5]:  # then it's a disk device
                line = line.split()
                self.mounts[line[0]] = line[1]
        return self.mounts

    def check_mount_point(self, mount_point):
        if not os.path.isdir(mount_point):
            try:
                os.mkdir(mount_point)
            except OSError as e:
                if e.errno == errno.EEXIST:  # seems impossible
                    pass
                elif e.errno == errno.EACCES:
                    raise Exception('Must be run as root user')
                elif e.errno == 2:  # TODO look up non-numeric
                    # because we got crap for mount_point ?
                    raise Exception(
                            f'{mount_point} not found making mount_point')
                else:
                    pprint(e)
                    raise Exception(f'wtf checking mount_point {mount_point}')
            # print(f'created mount point {mount_point}')
            return
        else:
            pass

    def _mount_partition(self, mount_point):
        """ /bin/mount requires root priveledge
        """

        self.check_mount_point(mount_point)

        # mounted allready ?
        proc_mounts = self.get_proc_mounts()
        cmd = ['/bin/mount', self.name, self.mount_point]
        msg = f'wtf mounting partition {partition} at {mount_point}'
        if self.name not in proc_mounts:
            error_ret = subprocess.check_call(cmd)
        if proc_mounts[self.name] != mount_point:
            error_ret = subprocess.check_call(cmd)
            if error_ret:
                raise Exception(msg)
        if self.get_proc_mounts()[self.name] == mount_point:
            self.mount_point = mount_point  # update data
        else:
            raise Exception(msg)

    def mok_mount(self, mount_point):

        raise Exception('not implemented yet')

    def mount_partition(self, mount_point):   # desired mount point
        if os.getuid() == 0:
            self._mount_partition(self, mount_point)
        else:
            self.mok_mount(mount_point)


def find_source_disk(partition_table):
    """ Find out where to copy from and return a reverse lookup, sources. """
    mounts = partition_table.mounts  # indexed by '/dev/sdxx/
    all_parts = partition_table.partitions  # indexed by '/dev/sdxx/
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


def find_dest_disk(potentials):
    # potentials = all_partitions.values()  # [DiskPart] list
    # [DiskPart] list
    efi_candidates = []  # [DiskPart] list

    # Find available vfat partitions for EFI.

    for partition in potentials:  # exclude mounted EFI
        if partition.ptype == 'vfat' and (
                '/boot/efi' not in [partition.mount_point]):
            efi_candidates += [partition]

    # The new '/' has to be put on the same disk as the new EFI.
    for efi_part in efi_candidates:
        efi_disk = partition.dev[5:8]  # 'sd?'

        root_candidates = []
        for p in potentials:
            if p.ptype != 'vfat' and efi_disk in p.dev:
                root_candidates += [(efi_part, partition)]
    if len(root_candidates) == 1:
        return {'/boot/efi': efi_part[0], '/': partition[0]}
    elif len(root_candidates) == 0:
        raise Exception('No install candidates found')
    elif len(root_candidates) > 1:
        raise Exception('TODO fix later, choose from root_candidates')
    else:
        raise Exception('wtf in find_dest_disk')


partition_table = PartitionTable()

if __name__ == '__main__':

    print(partition_table)

    # print(find_source_disk(part_table))
    source_disk = find_source_disk(partition_table)
    # pprint(source_disk)
    dest_disk = partition_table.get_blkids().values()
    # print(dest_disk)

    pass
