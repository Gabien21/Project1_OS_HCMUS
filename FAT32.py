import re
from RDET import RDET


class FAT32:
    info = [
        'Jump_Code',
        "OEM_ID",
        "Bytes Per Sector",
        "Sectors Per Cluster",
        "Reserved Sectors",
        "Number of Copies of FAT",
        "Media Descriptor",
        "Sectors Per Track",
        "Number of Heads",
        "Number of Hidden Sectors inPartition",
        "Number of Sectors inPartition",
        "Number of Sectors Per FAT",
        "Flags",
        "Version of FAT32 Drive",
        "Cluster Number of the Start of the Root Directory",
        "Sector Number of the FileSystem Information Sector",
        "Sector Number of the BackupBoot Sector",
        "Reserved",
        "Logical Drive Number of Partition",
        "Unused",
        "Extended Signature",
        "Serial Number of Partition",
        "Volume Name of Partition",
        "FAT Name",
        "Boot Record Signature",
    ]
    FAT_data = ""
    FAT_elements = []

    def __init__(self, name_of_volume):
        self.name = name_of_volume
        self.cwd = [self.name]
        self.fd = open(r'\\.\%s' % self.name, 'rb')
        self.boot_sector_raw = self.fd.read(0x200)
        with open('bootsector.dat', 'wb') as file:
            file.write(self.boot_sector_raw)
        self.boot_sector = {}
        self.__extract_boot_sector()
        self.SB = self.boot_sector["Reserved Sectors"]
        self.SF = self.boot_sector["Number of Sectors Per FAT"]
        self.NF = self.boot_sector["Number of Copies of FAT"]
        self.SC = self.boot_sector["Sectors Per Cluster"]
        self.BS = self.boot_sector["Bytes Per Sector"]
        self.boot_sector_reserved_raw = self.fd.read(self.BS * (self.SB - 1))
        with open('bootsector2.dat', 'wb') as file:
            file.write(self.boot_sector_reserved_raw)
        self.get_FAT_data()
        self.DET = {}

        start = self.boot_sector["Cluster Number of the Start of the Root Directory"]
        RDET_data = self.get_all_cluster_data(start)
        self.DET[start] = RDET(RDET_data)
        self.RDET = self.DET[start]
        with open('RDET.dat', 'wb') as file:
            file.write(RDET_data)

    def get_cluster_chain(self, index: int) -> 'list[int]':
        index_list = []
        while True:
            index_list.append(index)
            index = self.FAT_elements[index]
            if index == 0x0FFFFFFF or index == 0x0FFFFFF7:
                break
        return index_list

    def get_FAT_data(self):
        fat_size = self.SF * self.BS
        tmp = b""
        for _ in range(self.NF):
            tmp = self.fd.read(fat_size)
        self.FAT_data = tmp
        for i in range(0, len(self.FAT_data), 4):
            self.FAT_elements.append(int.from_bytes(self.FAT_data[i:i + 4], byteorder='little'))

    def __extract_boot_sector(self):
        self.boot_sector["Jump_Code"] = hex(int.from_bytes(self.boot_sector_raw[:3], byteorder='little'))
        self.boot_sector["OEM_ID"] = self.boot_sector_raw[3:0xB].decode()
        self.boot_sector["Bytes Per Sector"] = int.from_bytes(self.boot_sector_raw[0xB:0xD], byteorder='little')
        self.boot_sector["Sectors Per Cluster"] = int.from_bytes(self.boot_sector_raw[0xD:0xE], byteorder='little')
        self.boot_sector["Reserved Sectors"] = int.from_bytes(self.boot_sector_raw[0xE:0x10], byteorder='little')
        self.boot_sector["Number of Copies of FAT"] = int.from_bytes(self.boot_sector_raw[0x10:0x11], byteorder='little')
        self.boot_sector["Media Descriptor"] = hex(int.from_bytes(self.boot_sector_raw[0x15:0x16], byteorder='little'))
        self.boot_sector["Sectors Per Track"] = int.from_bytes(self.boot_sector_raw[0x18:0x1A], byteorder='little')
        self.boot_sector["Number of Heads"] = int.from_bytes(self.boot_sector_raw[0x1A:0x1C], byteorder='little')
        self.boot_sector["Number of Hidden Sectors inPartition"] = int.from_bytes(self.boot_sector_raw[0x1C:0x20], byteorder='little')
        self.boot_sector["Number of Sectors inPartition"] = int.from_bytes(self.boot_sector_raw[0x20:0x24], byteorder='little')
        self.boot_sector["Number of Sectors Per FAT"] = int.from_bytes(self.boot_sector_raw[0x24:0x28], byteorder='little')
        self.boot_sector["Flags"] = int.from_bytes(self.boot_sector_raw[0x28:0x2A], byteorder='little')
        self.boot_sector["Version of FAT32 Drive"] = int.from_bytes(self.boot_sector_raw[0x2A:0x2C], byteorder='little')
        self.boot_sector["Cluster Number of the Start of the Root Directory"] = int.from_bytes(self.boot_sector_raw[0x2C:0x30], byteorder='little')
        self.boot_sector["Sector Number of the FileSystem Information Sector"] = int.from_bytes(self.boot_sector_raw[0x30:0x32], byteorder='little')
        self.boot_sector["Sector Number of the BackupBoot Sector"] = int.from_bytes(self.boot_sector_raw[0x32:0x34], byteorder='little')
        self.boot_sector["Reserved"] = int.from_bytes(self.boot_sector_raw[0x34:0x40], byteorder='little')
        self.boot_sector["Logical Drive Number of Partition"] = hex(int.from_bytes(self.boot_sector_raw[0x40:0x41], byteorder='little'))
        self.boot_sector["Unused"] = int.from_bytes(self.boot_sector_raw[0x41:0x42], byteorder='little')
        self.boot_sector["Extended Signature"] = hex(int.from_bytes(self.boot_sector_raw[0x42:0x43], byteorder='little'))
        self.boot_sector["Serial Number of Partition"] = hex(int.from_bytes(self.boot_sector_raw[0x43:0x47], byteorder='little'))
        self.boot_sector["Volume Name of Partition"] = self.boot_sector_raw[0x47:0x52].decode()
        self.boot_sector["FAT Name"] = self.boot_sector_raw[0x52:0x5A].decode()
        self.boot_sector["Executable Code"] = self.boot_sector_raw[0x5A:0x1FE]
        self.boot_sector["Boot Record Signature"] = hex( int.from_bytes(self.boot_sector_raw[0x1FE:0x200], byteorder='little'))
        self.boot_sector['Starting Sector of Data'] = self.boot_sector["Reserved Sectors"] + self.boot_sector["Number of Copies of FAT"] * self.boot_sector["Number of Sectors Per FAT"]

    def get_all_cluster_data(self, cluster_index):
        index_list = self.get_cluster_chain(cluster_index)
        data = b""
        for i in index_list:
            off = self.SB + self.SF * self.NF + (i - 2) * self.SC
            self.fd.seek(off * self.BS)
            data += self.fd.read(self.SC * self.BS)
        with open('Dataa.dat', 'wb') as file:
            file.write(data)
        return data

    def move_directory(self, path=""):
        if path == "":
            raise Exception("Path to directory is required!")
        self.RDET = self.get_SDET(path)

        dirs = re.sub(r"[/\\]+", r"\\", path).strip("\\").split("\\")
        if dirs[0] == self.name:
            self.cwd.clear()
            self.cwd.append(self.name)
            dirs.pop(0)

    def get_SDET(self, dir) -> RDET:
        dirs = re.sub(r"[/\\]+", r"\\", dir).strip("\\").split("\\")
        if dirs[0] == self.name:
            cdet = self.DET[self.boot_sector["Cluster Number of the Start of the Root Directory"]]
            dirs.pop(0)
        else:
            cdet = self.RDET
        for d in dirs:
            entry = cdet.find_entry_by_name(d)
            if entry is None:
                raise Exception("Directory not found!")
            if entry.attribute == b"\x10":
                if entry.start_cluster == 0:
                    continue
                cdet = self.DET[entry.start_cluster] = RDET(self.get_all_cluster_data(entry.start_cluster))
            else:
                raise Exception("Not a directory")
        return cdet

    def get_directory_info(self, dir=""):
        try:
            if dir != "":
                cdet = self.get_SDET(dir)
                entry_list = cdet.get_main_entries()
            else:
                entry_list = self.RDET.get_main_entries()
            ret = []
            for entry in entry_list:
                obj = {}
                obj["Flags"] = entry.attribute
                obj["Size"] = entry.size
                obj["Name"] = entry.name
                if entry.start_cluster == 0:
                    obj["Sector"] = (entry.start_cluster + 2) * self.SC
                else:
                    obj["Sector"] = entry.start_cluster * self.SC
                ret.append(obj)
            return ret
        except Exception as e:
            raise (e)

    def get_data_txt_file(self, path: str) -> str:
        path = re.sub(r"[/\\]+", r"\\", path).strip("\\").split("\\")
        if len(path) > 1:
            name = path[-1]
            path = "\\".join(path[:-1])
            cdet = self.get_SDET(path)
            entry = cdet.find_entry_by_name(name)
        else:
            entry = self.RDET.find_entry_by_name(path[0])
        index_list = self.get_cluster_chain(entry.start_cluster)
        data = ""
        size_left = entry.size
        for i in index_list:
            if size_left <= 0:
                break
            off = self.SB + self.SF * self.NF + (i - 2) * self.SC
            self.fd.seek(off * self.BS)
            raw_data = self.fd.read(min(self.SC * self.BS, size_left))
            size_left -= self.SC * self.BS
            data += raw_data.decode()
        return data

    def __str__(self) -> str:
        s = ""
        s += "Volume name: " + self.name
        s += "\nVolume information:\n"
        for key in FAT32.info:
            s += f"{key}: {self.boot_sector[key]}\n"
        return s


def print_tree(vol, entry, prefix="", last=False):
    print(prefix + ("|_" if last else "|") + entry["Name"])
    if entry["Flags"] == b"\x20":
        return

    vol.move_directory(entry["Name"])
    entries = vol.get_directory_info()
    l = len(entries)
    for i in range(l):
        if entries[i]["Name"] in (".", ".."):
            continue
        prefix_char = "   " if last else "|  "
        print_tree(vol, entries[i], prefix + prefix_char, i == l - 1)
    vol.move_directory("..")


def display_tree(vol, arg):
    cwd = (vol.cwd[0] + "\\") if len(vol.cwd) == 1 else "\\".join(vol.cwd)
    try:
        if arg != "":
            vol.move_directory(arg)
            print((vol.cwd[0] + "\\") if len(vol.cwd) == 1 else "\\".join(vol.cwd))
        else:
            print(cwd)
        entries = vol.get_directory_info()
        l = len(entries)
        for i in range(l):
            if entries[i]["Name"] in (".", ".."):
                continue
            print_tree(vol, entries[i], "", i == l - 1)
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        vol.move_directory(cwd)


def get_folder_info(vol, arg):
    if ".txt" in arg:
        print(vol.get_data_txt_file(arg))
        return
    filelist = vol.get_directory_info(arg)
    print("Mode" + "\t\t" + "Sector" + "\t" + "Length" + "\t" + "Name")
    for file in filelist:
        flags = file['Flags']
        flagstr = ""
        if flags == b"\x01":
            flagstr = 'ReadOnly'
        if flags == b"\x02":
            flagstr = 'Hidden'
        if flags == b"\x04":
            flagstr = 'System'
        if flags == b"\x08":
            flagstr = 'VolLable'
        if flags == b"\x10":
            flagstr = 'Directory'
        if flags == b"\x20":
            flagstr = 'Archive'
        flagstr = "".join(flagstr)
        s = "\t"
        print(
            f"{flagstr} \t {file['Sector']} \t {file['Size'] if file['Size'] != 0 else s} \t {file['Name']}")