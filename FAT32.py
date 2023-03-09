from itertools import chain
import re


class Entry:
    def __init__(self, data):
        self.subentry = self.deleted = self.empty = self.label = False
        self.size = 0
        self.ext = b""
        self.long_name = ""
        self.entry_data = data
        self.attribute = data[11:12]
        if self.attribute == b'\x0f':
            self.subentry = True
        if not self.subentry:
            self.name = self.entry_data[:8]
            self.ext = self.entry_data[8:11]
            first_byte = self.name[:1]
            if first_byte == b'\xe5':
                self.deleted = True
            else:
                if first_byte == b'\x00':
                    self.empty = True
                    self.name = ""
                    return
            if self.attribute == b"\x08":
                self.label = True
                return
            self.start_cluster = int.from_bytes(self.entry_data[0x1A:0x1C][::-1],
                                                byteorder='big')
            self.size = int.from_bytes(self.entry_data[0x1C:0x20], byteorder='little')
        else:
            self.index = self.entry_data[0]
            self.name = b""
            for i in chain(range(1, 11), range(14, 26), range(28, 32)):
                self.name += int.to_bytes(self.entry_data[i], 1, byteorder='little')
                if self.name.endswith(b"\xff\xff"):
                    self.name = self.name[:-2]
                    break
            self.name = self.name.decode('utf-16le').strip('\x00')

    def is_active_entry(self):
        if self.empty or self.subentry or self.deleted or self.label or (self.attribute == b"\x16"):
            return False
        return True

    def is_directory(self):
        if self.attribute == b"\x10":
            return True
        return False

    def is_archive(self):
        if self.attribute == b"0x20":
            return True
        return False


class RDET:
    def __init__(self, data: bytes) -> None:
        self.REDET_data: bytes = data
        self.entries = []
        long_name = ""
        for i in range(0, len(data), 32):
            one_entry = self.REDET_data[i: i + 32]
            self.entries.append(Entry(one_entry))
            if self.entries[-1].empty or self.entries[-1].deleted:
                long_name = ""
                continue
            if not self.entries[-1].subentry:
                if long_name != "":
                    self.entries[-1].long_name = long_name
                else:
                    extend = self.entries[-1].ext.strip().decode()
                    if extend == "":
                        self.entries[-1].long_name = self.entries[-1].name.strip().decode()
                    else:
                        self.entries[-1].long_name = self.entries[-1].name.strip().decode() + "." + extend
                long_name = ""
            else:
                long_name = self.entries[-1].name + long_name

    def get_active_entries(self) -> 'list[Entry]':
        entry_list = []
        for i in range(len(self.entries)):
            if self.entries[i].is_active_entry():
                entry_list.append(self.entries[i])
        return entry_list

    def find_entry(self, name) -> Entry:
        for i in range(len(self.entries)):
            if self.entries[i].is_active_entry() and self.entries[i].long_name.lower() == name.lower():
                return self.entries[i]
        return None


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

    def __init__(self, name_of_volume) -> None:
        self.name = name_of_volume
        self.cwd = [self.name]
        self.fd = open(r'\\.\%s' % self.name, 'rb')
        self.boot_sector_raw = self.fd.read(0x200)
        with open('bootsector.dat', 'wb') as file:
            file.write(self.boot_sector_raw)
        self.boot_sector = {}
        self.__extract_boot_sector()
        if self.boot_sector["FAT Name"] != b"FAT32   ":
            raise Exception("Not FAT32")
        self.boot_sector["FAT Name"] = self.boot_sector["FAT Name"].decode()
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
        self.boot_sector["Logical Drive Number of Partition"] = hex( int.from_bytes(self.boot_sector_raw[0x40:0x41], byteorder='little'))
        self.boot_sector["Unused"] = int.from_bytes(self.boot_sector_raw[0x41:0x42], byteorder='little')
        self.boot_sector["Extended Signature"] = hex(int.from_bytes(self.boot_sector_raw[0x42:0x43], byteorder='little'))
        self.boot_sector["Serial Number of Partition"] = hex(int.from_bytes(self.boot_sector_raw[0x43:0x47], byteorder='little'))
        self.boot_sector["Volume Name of Partition"] = self.boot_sector_raw[0x47:0x52].decode()
        self.boot_sector["FAT Name"] = self.boot_sector_raw[0x52:0x5A]
        self.boot_sector["Executable Code"] = self.boot_sector_raw[0x5A:0x1FE]
        self.boot_sector["Boot Record Signature"] = hex( int.from_bytes(self.boot_sector_raw[0x1FE:0x200], byteorder='little'))
        self.boot_sector['Starting Sector of Data'] = self.boot_sector["Reserved Sectors"] + self.boot_sector["Number of Copies of FAT"] * self.boot_sector["Number of Sectors Per FAT"]

    def __offset_from_cluster(self, index):
        return self.SB + self.SF * self.NF + (index - 2) * self.SC

    def get_all_cluster_data(self, cluster_index):
        index_list = self.get_cluster_chain(cluster_index)
        data = b""
        for i in index_list:
            off = self.__offset_from_cluster(i)
            self.fd.seek(off * self.BS)
            data += self.fd.read(self.SC * self.BS)
        with open('Dataa.dat', 'wb') as file:
            file.write(data)
        return data

    def __str__(self) -> str:
        s = ""
        s += "Volume name: " + self.name
        s += "\nVolume information:\n"
        for key in FAT32.info:
            s += f"{key}: {self.boot_sector[key]}\n"
        return s

    def get_cwd(self):
        if len(self.cwd) == 1:
            return self.cwd[0] + "\\"
        return "\\".join(self.cwd)

    def change_dir(self, path=""):
        if path == "":
            raise Exception("Path to directory is required!")
        cdet = self.visit_dir(path)
        self.RDET = cdet

        dirs = self.__parse_path(path)
        if dirs[0] == self.name:
            self.cwd.clear()
            self.cwd.append(self.name)
            dirs.pop(0)
        for d in dirs:
            if d == "..":
                self.cwd.pop()
            elif d != ".":
                self.cwd.append(d)

    def visit_dir(self, dir) -> RDET:
        if dir == "":
            raise Exception("Directory name is required!")
        dirs = self.__parse_path(dir)

        if dirs[0] == self.name:
            cdet = self.DET[self.boot_sector["Cluster Number of the Start of the Root Directory"]]
            dirs.pop(0)
        else:
            cdet = self.RDET

        for d in dirs:
            entry = cdet.find_entry(d)
            if entry is None:
                raise Exception("Directory not found!")
            if entry.is_directory():
                if entry.start_cluster == 0:
                    continue
                if entry.start_cluster in self.DET:
                    cdet = self.DET[entry.start_cluster]
                    continue
                self.DET[entry.start_cluster] = RDET(self.get_all_cluster_data(entry.start_cluster))
                cdet = self.DET[entry.start_cluster]
            else:
                raise Exception("Not a directory")
        return cdet

    def __parse_path(self, path):
        dirs = re.sub(r"[/\\]+", r"\\", path).strip("\\").split("\\")
        return dirs

    def get_dir(self, dir=""):
        try:
            if dir != "":
                cdet = self.visit_dir(dir)
                entry_list = cdet.get_active_entries()
            else:
                entry_list = self.RDET.get_active_entries()
            ret = []
            for entry in entry_list:
                obj = {}
                obj["Flags"] = entry.attribute
                obj["Size"] = entry.size
                obj["Name"] = entry.long_name
                if entry.start_cluster == 0:
                    obj["Sector"] = (entry.start_cluster + 2) * self.SC
                else:
                    obj["Sector"] = entry.start_cluster * self.SC
                ret.append(obj)
            return ret
        except Exception as e:
            raise (e)

    def __del__(self):
        if getattr(self, "fd", None):
            print("Closing Volume...")
            self.fd.close()