import re


class NTFS:
    info = [
        "JMP instruction",
        "OEM ID",
        "Bytes per sector",
        "Sectors per Cluster",
        "Reserved sectors",
        "Media descriptor",
        "Sectors per track",
        "Number of heads",
        "Hidden sectors",
        "Total sectors",
        "$MFT cluster number",
        "$MFTMirr cluster number",
        "Clusters per File Record Segment",
        "Clusters per Index Block",
        "Volume serial number",
        "MFT record size",
    ]
    MFT_data = b""

    def __init__(self, name_of_volume):
        self.name = name_of_volume
        self.cwd = [self.name]
        self.fd = open(r'\\.\%s' % self.name, 'rb')
        self.boot_sector_raw = self.fd.read(0x200)
        with open('PBS.dat', 'wb') as file:
            file.write(self.boot_sector_raw)
        self.VBR = {}
        self.extract_VBR()
        self.SC = self.VBR["Sectors per Cluster"]
        self.BS = self.VBR["Bytes per sector"]

        self.record_size = self.VBR["MFT record size"]
        self.mft_offset = self.VBR["$MFT cluster number"]
        self.get_MFT_data()

    def get_MFT_data(self):
        MFT_size = self.record_size
        self.fd.seek(self.mft_offset * self.SC * self.BS)
        tmp = self.fd.read(MFT_size)
        self.MFT_data = tmp
        with open("MFT.dat", 'wb') as file:
            file.write(tmp)


    def extract_VBR(self):
        self.VBR["JMP instruction"] = hex(int.from_bytes(self.boot_sector_raw[:3], byteorder='little'))
        self.VBR["OEM ID"] = self.boot_sector_raw[3:0xB].decode()
        self.VBR["Bytes per sector"] = int.from_bytes(self.boot_sector_raw[0xB:0xD], byteorder='little')
        self.VBR["Sectors per Cluster"] = int.from_bytes(self.boot_sector_raw[0xD:0xE], byteorder='little')
        self.VBR["Reserved sectors"] = int.from_bytes(self.boot_sector_raw[0xE:0x10], byteorder='little')
        self.VBR["Media descriptor"] = hex(int.from_bytes(self.boot_sector_raw[0x15:0x16], byteorder='little'))
        self.VBR["Sectors per track"] = int.from_bytes(self.boot_sector_raw[0x18:0x1A], byteorder='little')
        self.VBR["Number of heads"] = int.from_bytes(self.boot_sector_raw[0x1A:0x1C], byteorder='little')
        self.VBR["Hidden sectors"] = int.from_bytes(self.boot_sector_raw[0x1C:0x20], byteorder='little')
        self.VBR["Total sectors"] = int.from_bytes(self.boot_sector_raw[0x28:0x30], byteorder='little')
        self.VBR["$MFT cluster number"] = int.from_bytes(self.boot_sector_raw[0x30:0x38], byteorder='little')
        self.VBR["$MFTMirr cluster number"] = int.from_bytes(self.boot_sector_raw[0x38:0x40], byteorder='little')
        self.VBR["Clusters per File Record Segment"] = int.from_bytes(self.boot_sector_raw[0x40:0x41], byteorder='little', signed=True)
        self.VBR["Clusters per Index Block"] = int.from_bytes(self.boot_sector_raw[0x44:0x45], byteorder='little')
        self.VBR["Volume serial number"] = hex(int.from_bytes(self.boot_sector_raw[0x48:0x50], byteorder='little'))
        self.VBR["MFT record size"] = 2 ** abs(self.VBR["Clusters per File Record Segment"])

    def __str__(self) -> str:
        s = ""
        s += "Volume name: " + self.name
        s += "\nVolume information:\n"
        for key in NTFS.info:
            s += f"{key}: {self.VBR[key]}\n"
        return s