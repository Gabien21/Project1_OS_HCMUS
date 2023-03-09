from itertools import chain


class Entry:
    def __init__(self, data):
        self.subentry = self.deleted = self.empty = self.label = False
        self.size = 0
        self.ext = b""
        self.name = ""
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
            self.start_cluster = int.from_bytes(self.entry_data[26:28][::-1],
                                                byteorder='big')
            self.size = int.from_bytes(self.entry_data[28:32], byteorder='little')
        else:
            self.index = self.entry_data[0]
            self.name = b""
            for i in chain(range(1, 11), range(14, 26), range(28, 32)):
                self.name += int.to_bytes(self.entry_data[i], 1, byteorder='little')
                if self.name.endswith(b"\xff\xff"):
                    self.name = self.name[:-2]
                    break
            self.name = self.name.decode('utf-16le').strip('\x00')

    def is_main(self):
        if self.empty or self.subentry or self.deleted or self.label or (self.attribute == b"\x16"):
            return False
        return True


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
                    self.entries[-1].name = long_name
                else:
                    extend = self.entries[-1].ext.strip().decode()
                    if extend == "":
                        self.entries[-1].name = self.entries[-1].name.strip().decode()
                    else:
                        self.entries[-1].name = self.entries[-1].name.strip().decode() + "." + extend
                long_name = ""
            else:
                long_name = self.entries[-1].name + long_name

    def get_main_entries(self):
        entry_list = []
        for i in range(len(self.entries)):
            if self.entries[i].is_main():
                entry_list.append(self.entries[i])
        return entry_list

    def find_entry_by_name(self, name):
        for i in range(len(self.entries)):
            if self.entries[i].is_main() and self.entries[i].name.lower() == name.lower():
                return self.entries[i]
        return None
