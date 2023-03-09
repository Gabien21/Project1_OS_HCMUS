from FAT32 import FAT32
import re
import os


def do_ls(vol, arg):
    filelist = vol.get_dir(arg)
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


def do_tree(vol, arg):
    def print_tree(entry, prefix="", last=False):
        print(prefix + ("└─" if last else "├─") + entry["Name"])
        if entry["Flags"] == b"\x20":
            return

        vol.change_dir(entry["Name"])
        entries = vol.get_dir()
        l = len(entries)
        for i in range(l):
            if entries[i]["Name"] in (".", ".."):
                continue
            prefix_char = "   " if last else "│  "
            print_tree(entries[i], prefix + prefix_char, i == l - 1)
        vol.change_dir("..")

    cwd = vol.get_cwd()
    try:
        if arg != "":
            vol.change_dir(arg)
            print(vol.get_cwd())
        else:
            print(cwd)
        entries = vol.get_dir()
        l = len(entries)
        for i in range(l):
            if entries[i]["Name"] in (".", ".."):
                continue
            print_tree(entries[i], "", i == l - 1)
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        vol.change_dir(cwd)


if __name__ == "__main__":
    drives = [chr(x) + ":" for x in range(65, 91) if os.path.exists(chr(x) + ":")]
    print("Available volumes:")
    for i in range(len(drives)):
        print(f"{i + 1}/", drives[i])
    try:
        choice = int(input("Which volume to use: "))
    except Exception as e:
        print(f"[ERROR] {e}")
        exit()

    if 0 >= choice > len(drives):
        print("[ERROR] Invalid choice!")
        exit()
    vol = FAT32(drives[choice - 1])
    print(vol)
    do_tree(vol, "E:\\")
    arg = input("Nhập vị trí:")
    do_ls(vol, arg)
