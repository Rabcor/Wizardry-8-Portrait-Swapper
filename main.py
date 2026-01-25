import tkinter as tk
from tkinter import filedialog
import os
import sys
from STI import STI8, STI16
from PATCH import PATCH
from SLF import SLF
from GUI import GUI


def main():
    gamedir = find_wiz8_dir()
    
    data_slf_path = os.path.join(gamedir, "Data", "DATA.SLF")
    slf = SLF(data_slf_path)
    
    patch_path = os.path.join(gamedir, "Patches", "PATCH.010")
    if os.path.exists(patch_path):
        patch_file = PATCH(patch_path)
    else:
        patch_file = PATCH()
    patch_file.path = patch_path
            
    
    gui = GUI(fetch_portraits(slf), patch_file.content)
    gui.patch_file = patch_file
    slf = patch_file = None # Clear up some memory, think of the poor.
    gui.root.mainloop()

def find_wiz8_dir():
    possible_dirs = [
        ".",
        "..",
        os.path.expanduser("~/.local/share/Steam/steamapps/common/Wizardry8"),
        os.path.expanduser("~/.wine/drive_c/GOG Games/Wizardry 8"),
        os.path.expanduser("%USERPROFILE%\\Steam\\steamapps\\common\\Wizardry8"),
        "C:\\GOG Games\\Wizardry 8",
        "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Wizardry8",
        "C:\\Program Files\\Steam\\steamapps\\common\\Wizardry8",
        "C:\\Steam\\steamapps\\common\\Wizardry8",
        "C:\\SteamLibrary\\steamapps\\common\\Wizardry8",
        "D:\\SteamLibrary\\steamapps\\common\\Wizardry8",
        "E:\\SteamLibrary\\steamapps\\common\\Wizardry8",
    ]

    for dir in possible_dirs:
        if os.path.exists(os.path.join(dir, "Wiz8.exe")):
            return dir
            
    directory = tk.filedialog.askdirectory(title="Select Wizardry 8 Directory")
    return directory

def fetch_portraits(slf):
    return {
        filename: slf.data[addr:addr+size]
        for filename, (addr, size) in slf.files.items()
        if filename.startswith("PORTRAITS")
    }

    
if __name__ == "__main__":
    main()

