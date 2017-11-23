#!/home/triley/anaconda3/bin/python

import re
from typing import List, Tuple
import subprocess
from pprint import pprint
from contextlib import contextmanager


from partitions import PartitionTable, os_one_liner


def rsync(partition_table: PartitionTable) -> None:
    excludes = {
            '/': '--exclude tmp/* --exclude var/log/* ',
            '/boot/efi/': '--exclude EFI/tools '}

    for src_path in ['/boot/efi/', '/']:
        dest_path = partition_table.dest_root_mount + src_path
        cmd = 'rsync -a --one-file-system --delete '
        cmd += excludes[src_path]
        cmd += src_path + ' ' + dest_path
        print('rsync: cmd =', cmd)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
        result.check_returncode()
        print(result.stdout.split(b'\n'))


def replace(
        replacements: List[Tuple[str, str]],
        file_name: str) -> None:
    """ Replace each first string with the second string.

        Assumes each replacement happens, at most, once per line.
        Any number of replacements can happen on each line
    """
    line_list = []
    with open(file_name) as f:
        for line in f:
            new_item = line
            for old_str, new_str in replacements:
                new_item = re.sub(old_str, new_str, new_item)
            line_list.append(new_item)

    with open(file_name, 'w') as f:
        for line in line_list:
            f.write("{}".format(line))


edit_file_names = [
    "/etc/grub.d/25_custom",
    "/etc/fstab"]


def edit_files(partition_table: PartitionTable) -> None:

    drm = partition_table.dest_root_mount
    src_root_uuid = partition_table.sources['/'].uuid
    dst_root_uuid = partition_table.mounts[drm].uuid
    src_uefi_uuid = partition_table.sources['/boot/efi'].uuid
    dst_uefi_uuid = partition_table.mounts[drm+'/boot/efi'].uuid
    replacement_uuids = [
        (src_root_uuid, dst_root_uuid),
        (src_uefi_uuid, dst_uefi_uuid)]
    # print('\nsubstitutions ...')
    # print(replacement_uuids)
    for file_name in edit_file_names:
        replace(replacement_uuids, f'{drm}/{file_name}')


def is_mounted(mnt):
    lines = os_one_liner('mount')
    # print(lines)
    for line in lines:
        # print(line.split())
        if len(line.split()) > 2:
            if line.split()[2]:
                # print('line:', line, 'm:', mnt, 'l:', line.split()[2])
                if mnt == line.split()[2]:
                    return True
    return False


@contextmanager
def chroot_mounts(partition_table: PartitionTable) -> None:
    for mnt in '/dev /dev/pts /proc /sys'.split():
        new_mnt = partition_table.dest_root_mount + mnt
        print(f'mounting {new_mnt}')
        if not is_mounted(new_mnt):
            cmd = f'mount --bind {mnt} {new_mnt}'
            # print(cmd)
            os_one_liner(cmd)
    yield
    for mnt in '/dev/pts /dev /proc /sys'.split():
        new_mnt = partition_table.dest_root_mount + mnt
        if is_mounted(new_mnt):
            umount = f'{partition_table.dest_root_mount}{mnt}'
            cmd = f'umount {umount}'
            # print(cmd)
            os_one_liner(cmd)


def grub_install(partition_table: PartitionTable) -> None:
    with chroot_mounts(partition_table):
        # print('mounted:', test)
        print('in context')
        pprint(os_one_liner('mount | grep sdc2'))
    print('out of context')
    pprint(os_one_liner('mount | grep sdc2'))


def update_grub(partition_table: PartitionTable) -> None:
    print(partition_table)


if __name__ == '__main__':
    pass
    partition_table = PartitionTable()
#    partition_table.find_source_disk()
#    print('\nsources:')
#    pprint(partition_table.sources)
    partition_table.find_dest_disk()
    print('\ndests')
    pprint(partition_table.dests)

    partition_table.mount_dest_disk()
    # rsync(partition_table)
#    edit_files(partition_table)
    grub_install(partition_table)
#    bind_mounts(partition_table)
#    grub_mounts = ['proc', 'sys', 'dev', 'dev/pts']

#    rsync(partition_table)
