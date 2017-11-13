#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 17:34:02 2017

@author: triley
"""


import errno
import os
import re
# import sys
# from subprocess import check_call, run
import subprocess
from pprint import pprint
from typing import Dict, List


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

        """

        :rtype: DiskPart
        """

        self.dev = dev
        self.disk = dev[5:8]
        self.part_num = dev[8]
        self.uuid = uuid
        self.ptype = ptype
        self.puuid = puuid
        self.mount_point = mount_point

    def __str__(self) -> str:
        s = ['  H']
        s += [self.dev if self.dev else ' '*9]
        s += [self.ptype[:4] if self.ptype else ' '*4]
        s += [self.uuid[:8] if self.uuid else ' '*8]
        s += [self.mount_point if self.mount_point else 'None']
        rstr = str(' '.join(s))
        return rstr

#    def __repr__(self):        return_str = str('\n'.join(s))
#        self.__str__()  # cheat


class PartitionTable(object):
    """ Abstract Partition Table
    """

    def __init__(
            self,
            partitions: Dict[str, DiskPart]=None,
            mounts: Dict[str, DiskPart]=None) -> None:
        """ Extract info from the OS:

            partitiona and mounts passed as parameters allow:
            o trial runs (not implemented yet).
            o non-root testing (maybe), and
            o testing configs not on my hardware
        """

        # one to one mapping {/dev/sd??:  partition}
        if partitions:
            self.partitions: Dict[str, DiskPart] = partitions
        else:
            self.partitions: Dict[str, DiskPart] = {}  # by dev (/dev/sdxx)
            self.update_blkids()
        for p in self.partitions:  # sanity check
            assert '/dev/' in p, f'partition table init on partition {p}'
        # potentially many to one: 1 partition can be mounted multiple times
        if mounts:
            self.mounts: Dict[str, DiskPart] = mounts
        else:
            self.mounts: Dict[str, DiskPart] = {}  # by mount_point
            self.update_mounts()

        self.sources: Dict[str, DiskPart] = {}  # by mount_point
        self.dests: Dict[str, DiskPart] = {}  # by mout_point
        # mount point relative to new root
        self.dests_relative: Dict[str, DiskPart] = {}

    def __str__(self):
        s = ['\nPartition Table:']
        for name, part in self.partitions.items():
            s += [part.__str__()]
        return str('\n'.join(s))

#    def __repr__(self):
#        self.__str__()

    def add_mock_partition(self):
        pass

    def update_blkids(self) -> None:
        """ Read partitions from os using blkid.

            This seems to work fine for non-root user, provided that you poke
            it first with a 'sudo blkid' at the command line once. Hmm ...
        """
        re_uuid = re.compile(b'UUID="(.*?)"')
        re_type = re.compile(b'TYPE="(.*?)"')
        re_puuid = re.compile(b'PARTUUID="(.*?)"')

        result = subprocess.run('blkid', stdout=subprocess.PIPE)
        result.check_returncode()
        lines = result.stdout.split(b'\n')
        for line in lines:
            if b'/dev/' in line:  # ignore empty lines
                p = line.split(b':')
                dev = p[0].strip().decode("utf-8")  # python3 string, no blanks
                uuid_m = re_uuid.search(p[1])  # re.match objects
                ptype_m = re_type.search(p[1])
                puuid_m = re_puuid.search(p[1])
                self.partitions[dev] = DiskPart(
                    dev=dev,  # keep dev info in the DiskPart instance
                    uuid=uuid_m.group(1).decode("utf-8") if uuid_m else None,
                    ptype=ptype_m.group(1).decode("utf-8") if ptype_m else None,
                    puuid=puuid_m.group(1).decode("utf-8") if puuid_m else None)

    def update_mounts(self) -> None:
        """ filter mounted for disks """
        with open('/proc/mounts') as f:
            lines = f.readlines()
        for line in lines:
            if '/dev/' in line[:5]:  # then it's a disk partition
                line = line.split()
                if line[0] in self.partitions:  # ignore stale mounts
                    self.mounts[line[1]] = self.partitions[line[0]]
                    self.partitions[line[0]].mount_point = line[1]

    @staticmethod
    def check_mount_point(mount_point: str) -> None:
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

    def _mount_partition(self, part: str, mount_point: str) -> None:
        """ /bin/mount requires root priveledge
        """

        self.check_mount_point(mount_point)

        # mounted allready ?
        cmd = ['/bin/mount', part, mount_point]
        msg = f'wtf mounting partition {part} at {mount_point}'
        if (part not in self.mounts) or (
                self.mounts[part] != mount_point):
            error_ret = subprocess.check_call(cmd)
            if error_ret:
                raise Exception(msg)
            self.mounts[part] = mount_point
            self.partitions[part].mount_point = mount_point
        if self.mounts[part] == mount_point:
            pass  # allready mounted
        else:
            raise Exception(msg)

    def mock_mount(self, part: str, mount_point: str) -> None:

        raise Exception(f'not implemented yet {mount_point}')

    def mount_partition(self, part: str, mount_point: str) -> None:
        if os.getuid() == 0:
            self._mount_partition(part, mount_point)
        else:
            self.mock_mount(part, mount_point)

    def find_source_disk(self) -> None:
        """ Find out where to copy from.

            Includes the non-universal assumption that both partitions are on
            the same disk.
        """

        for mount in ['/', '/boot/efi']:
            self.sources[mount] = self.mounts[mount]

        assert len(self.sources) == 2, 'wtf: Failed to find sources.'

    def find_dest_disk(self) -> None:

        all_parts: List[DiskPart] = [p for i, p in self.partitions.items()]

        # Find available vfat partitions for EFI.
        efi_candidates: List[DiskPart] = []
        for partition in all_parts:
            if partition.ptype == 'vfat' and (
                    '/boot/efi' != partition.mount_point):
                efi_candidates += [partition]

        # The new '/' is to be put on the same disk as the new EFI.
        install_candidates: List[Dict[str, DiskPart]] = []  # str is by mount
        for efi_part in efi_candidates:
            for p in all_parts:  # should be same disk as efi partition
                if p.ptype != 'vfat' and efi_part.disk in p.dev:
                    efi_mount = f'/mnt/{p.disk}{p.part_num}/boot/efi'
                    root_mount = f'/mnt/{p.disk}{p.part_num}'
                    install_candidate: Dict[str, DiskPart] = {
                        root_mount: p,
                        efi_mount: efi_part}
                    install_candidates += [install_candidate]
        if len(install_candidates) == 1:
            self.dests = install_candidates[0]
            self.dests_relative['/'] = install_candidates[0][root_mount]
            self.dests_relative['/boot/efi'] = install_candidates[0][efi_mount]
        elif len(install_candidates) == 0:
            raise Exception('No install candidates found')
        elif len(install_candidates) > 1:
            raise Exception('TODO fix later, choose from root_candidates')
        else:
            raise Exception('wtf in find_dest_disk')

    def mount_dest_disk(self):

        # '/mnt/sdxx' has to be mounted before '/mnt/sdxx/boot/efi'
        for m in  ['/', '/boot/efi']:  # mount root first, then EFI
            dev = self.dests_relative[m].dev
            mnt = self.dests_relative[m].
            self.mount_partition(dev, mnt)
#        for m in ['', '/boot/efi']:  # mount root first, then EFI
#            for dest in self.dests:
#                if re.search(f'/mnt/sd[a-z][1-9]({m}$)', dest):
#                    if dest not in self.mounts:
#                        self.mount_partition(self.dests[dest].dev, dest)


if __name__ == '__main__':
    # quick test for the most obvious case (for me right now)

    partition_table = PartitionTable()
    print('\n', partition_table)
    partition_table.find_source_disk()
    print('\nsources')
    pprint(partition_table.sources)

    partition_table.find_dest_disk()
    print('\ndests')
    pprint(partition_table.dests)

    partition_table.mount_dest_disk()
    print(partition_table)
    
    print('\nrel_mounts')
    pprint(partition_table.dests_relative)

