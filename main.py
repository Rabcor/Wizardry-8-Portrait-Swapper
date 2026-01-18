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
        if sys.platform != "win32":
            patch_file.path = f"Z:{gamedir.replace('/', '\\')}\\Patches\\PATCH.010" # Windows style path for linux/wine support
        else:
            patch_file.path = patch_path
    
    gui = GUI(slf.portraits, patch_file.content)
    gui.patch_file = patch_file
    slf = patch_file = None # Clear up some memory, think of the poor.
    gui.root.mainloop()

def find_wiz8_dir():
    possible_dirs = [
        ".",
        "..",
        os.path.expanduser("~/.local/share/Steam/steamapps/common/Wizardry8"),  # Linux Steam
        os.path.expanduser("%USERPROFILE%\\Steam\\steamapps\\common\\Wizardry8"),  # Windows Steam
    ]

    for dir in possible_dirs:
        if os.path.exists(os.path.join(dir, "Wiz8.exe")):
            return dir
            
    directory = tk.filedialog.askdirectory(title="Select Wizardry 8 Directory")
    return directory

if __name__ == "__main__":
    main()

