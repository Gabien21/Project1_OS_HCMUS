from FAT32 import FAT32, display_tree, get_folder_info
import os

if __name__ == "__main__":
    list_volume = []
    for volume in range(ord('A'), ord('Z')):
        if os.path.exists(chr(volume) + ":"):
            list_volume.append(chr(volume) + ":")
    print("Volume list:")
    for i in range(len(list_volume)):
        print(f"{i + 1}/", list_volume[i])
    try:
        choice = int(input("Choose: "))
    except Exception as e:
        print(f"[ERROR] {e}")
        exit()

    if 0 >= choice > len(list_volume):
        print("[ERROR] Invalid choice!")
        exit()
    vol = FAT32(list_volume[choice - 1])
    print("-----------------------------------------------------------------------------------------------------------")
    print(vol)
    print("-----------------------------------------------------------------------------------------------------------")
    display_tree(vol, "E:\\")
    print("-----------------------------------------------------------------------------------------------------------")
    arg = input("Input path of the folder to check information:")
    get_folder_info(vol, arg)
    print("-----------------------------------------------------------------------------------------------------------")
    arg = input("Input path of the text file:")
    get_folder_info(vol, arg)


