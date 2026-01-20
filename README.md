# Wizardry 8 Portrait Swapper
Now you can swap the portraits in Wizardry 8 without the pain.

![ps2](https://github.com/user-attachments/assets/102ea1a6-89d4-4942-80b1-98dbd506153f)

# Installation
Download the executable from the release section and just run it. The .exe is obviously for windows, the binary without an extension is for linux.

They were compiled with `pyinstaller --onefile --hidden-import='PIL._tkinter_finder' --collect-all imagequant --noupx --noconsole main.py`

You can also download the source and run main.py directly with python.

<details>
  <summary>Info for running on python</summary>
  
- Python Version: 3.13+
- Dependencies:
  - pillow
  - numpy
- Optional Dependencies:
  - imagequant (**Strongly** recommended)
  - tkinterdnd2 (Drag & Drop)

</details>

# Usage

The program looks for your wizardry 8 game directory in it's current directory, up one directory and the default steam install locations on linux and windows.

- Create your portraits, save them as standard 24-bit PNGs
- Drag and drop or use the change portraits file dialog to import the images, preferably all in one go.
- Medium portrait animation frames can be imported one at a time, if one medium size image is imported, it will overwrite the currently selected frame.
- Press save and that's it.

![Demo](https://github.com/user-attachments/assets/5fdb8251-5093-417d-811a-de768aa65d44)


Portraits come in 3 sizes
- Large: 180x144
- Medium: 90x72
- Small: 45x36


More detailed guide:
https://steamcommunity.com/sharedfiles/filedetails/?id=3641128848

# Known issues

- MHUMM4 is broken
  - because it's structure is different from other STI files, no plans to fix it.
- Importing small portraits for RPCs is broken
  - Something is going wrong when repackaging it, might fix it someday but it doesn't really matter since you **never** see those pictures in-game anyways, they only appear in the main menu, during party creation I think.
- Drag & Drop can be wonky on wayland
  - Wayland is broken, who could have guessed? Just use the change portrait filedialog instead if you've got problems, this kind of scenario is what it's there for.

If you encounter a problem that's not one of the above, please report the issue.
