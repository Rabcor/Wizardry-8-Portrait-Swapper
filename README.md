# Wizardry 8 Portrait Swapper
Now you can swap the portraits in Wizardry 8 without the pain.

![ps2](https://github.com/user-attachments/assets/102ea1a6-89d4-4942-80b1-98dbd506153f)

# Installation
Download the executable from the release section and just run it. The .exe is obviously for windows, the binary without an extension is for linux.

You can also download the source and run main.py directly with python.

<details>
  <summary>Info for running on python</summary>
  
- Python Version: 3.13+
- Dependencies:
  - pillow
  - numpy
- Optional Dependencies:
  - imagequant (high quality quantization, improves the final color quality of medium images after importing)
  - tkinterdnd2 (Drag & Drop)
- Compile Command:
  - `pyinstaller --onefile --hidden-import='PIL._tkinter_finder' --collect-all imagequant --noupx --noconsole main.py`

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

- Importing MHUMM4 is broken (Fixed in source)
  - Because it uses offsets instead of transparency to position the anim data:
  - Workaround:
    - Edit another portrait
    - Extract as STI
    - Import the STI to HUMM4.
- Drag & Drop can be wonky on wayland
  - Wayland is broken, who could have guessed? Just use the change portrait filedialog instead if you've got problems, this kind of scenario is what it's there for.

If you encounter a problem that's not one of the above, please report the issue.

# Extras

SLFEX is an SLF file parser, primarily geared towards reading SLF files and displaying info about it's contents, as well as extracting those contents. It's untested on windows.
<img width="1280" height="800" alt="image" src="https://github.com/user-attachments/assets/5d3a24c7-be1a-4981-aab1-faf3ae4749db" />
It's only partially complete, it can swap out the contents of most TGA files and to a limited degree STI files as well (STI16 fully supported, STI8 only properly supported if all images are the same size), it can display the contents of all those files properly though which can be a boon for modding when you are looking for a specific texture you want to replace. The utility isn't 100% complete, it relies on the other classes to function so run it from the same directory as you would main.py.
