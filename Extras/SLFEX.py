import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
from PIL import Image, ImageTk
import io
from SLF import SLF
from STI import STI8, STI16

'''
TGAs that can't be saved, all of them are in SPELLS/BITMAPS except for TRIGGER and WOOD_1 who are ITEMS3D/BITMAPS
Type 10: 27 files (FLASH-RED, SNOWBALL, VAPOR)
Type 1:  3 files (FIREBALL, TRIGGER, WOOD_1)
Type 3:  1 file (LUNA2)
Broken:  1 file (SKULL)
'''

class SLFExtractor:
    def __init__(self, root):
        self.root = root
        root.title("SLF Extractor")
        root.geometry("1280x780")
        self.gamedir = self._find_wiz8_dir()
        self.slf_file = os.path.join(self.gamedir, "Data", "DATA.SLF") if self.gamedir is not None else None
        self.slf = None
        self.current_image_index = 0
        self.create_widgets()
        self.load_slf_entries()
        self.modified_file = None

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        canvas_frame = tk.Frame(main_frame, width=200)
        canvas_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        canvas_frame.pack_propagate(False)
        
        self.canvas = tk.Canvas(canvas_frame, width=200, height=200, bg='grey')
        self.canvas.pack(expand=False)
        
        self.nav_frame = tk.Frame(canvas_frame)
        self.index_label = tk.Label(self.nav_frame, text=f"0/0")
        self.nav_frame.pack_forget()
        
        self.info_label = tk.Label(canvas_frame, text="", fg='black', justify=tk.LEFT, anchor=tk.NW)
                
        f = tk.Frame(main_frame)
        f.pack(fill=tk.X)
        tk.Button(f, text="Select SLF File", command=self.select_slf_file).pack(side=tk.LEFT)
        self.file_label = tk.Label(f, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=(10,0))
    
        t = tk.Frame(main_frame)
        t.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(t, columns=("Name", "Type", "Offset", "Size"), show="headings")        
        self.tree.column("Name", width=700, stretch=True)
        self.tree.column("Type", width=80)
        self.tree.column("Offset", width=100)
        self.tree.column("Size", width=100)
        for c in ("Name", "Type", "Offset", "Size"): 
            self.tree.heading(c, text=c, command=lambda col=c: self.sort_treeview(col))
        self.tree.pack(side=tk.LEFT,fill=tk.BOTH, expand=True)
        s = ttk.Scrollbar(t, orient=tk.VERTICAL, command=self.tree.yview)
        s.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=s.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
    
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)
        self.modify_button = tk.Button(button_frame, text="Modify", command=self.modify_file)
        self.modify_button.pack(side=tk.LEFT)
        self.extract_button = tk.Button(button_frame, text="Extract Selected Files", command=self.extract_files)
        self.extract_button.pack(side=tk.LEFT)
        
        self.save_modified_button = tk.Button(button_frame, text="Save Modified File", command=self.save_modified)
        
        self.save_patch_button = tk.Button(button_frame, text="Save As Patch", command=self.save_patch)

        self.status = tk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _update_info(self, text):
        self.info_label.pack_forget()
        self.info_label.pack_propagate(False)   
        self.info_label.config(text=text)
        self.info_label.pack(side=tk.TOP, fill=tk.BOTH)

    def sort_treeview(self, col):
        items = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        if col == "Offset" or col == "Size":
            items.sort(key=lambda x: int(x[0], 16) if x[0].startswith('0x') else int(x[0]))
        else:
            items.sort()
        
        for index, (val, child) in enumerate(items):
            self.tree.move(child, '', index)

    def on_tree_select(self, event):
        selection = self.tree.selection()
        self.modified_file = None
        self.save_modified_button.pack_forget()
        self.save_patch_button.pack_forget()
        self.modify_button.pack(side=tk.LEFT)
        self.modify_button.config(state='disabled')
        self.extract_button.pack(side=tk.LEFT)
        self.info_label.config(text="")
        if selection:
            item = selection[0]
            name, type, addr_hex, size = self.tree.item(item, 'values')
            self.nav_frame.pack_forget()
            self.current_image_index = 0 
            self.display_file(name)
    
    def next_img(self):
        if hasattr(self, 'current_image_index') and hasattr(self, 'nav_frame'):
            self.current_image_index += 1
            # Get the currently selected item
            selection = self.tree.selection()
            if selection:
                item = selection[0]
                name, type, addr_hex, size = self.tree.item(item, 'values')
                self.display_file(name)
    
    def prev_img(self):
        if hasattr(self, 'current_image_index') and hasattr(self, 'nav_frame'):
            self.current_image_index -= 1
            # Get the currently selected item
            selection = self.tree.selection()
            if selection:
                item = selection[0]
                name, type, addr_hex, size = self.tree.item(item, 'values')
                self.display_file(name)

    def _scale_resolution(self,width, height, target=(200, 200)):
        scale_factor = min(target[0]/width, target[1]/height)
        return (int(width*scale_factor), int(height*scale_factor))
    
    def display_file(self, name):
        try:
            if self.modified_file is not None:
                file_bytes = self.modified_file
            else:
                file_bytes = self.slf.extract(name)
            if name.endswith('.TGA'):
                tga = TGA(file_bytes)    
                self._update_info(tga)
                width = tga.header['width']
                height = tga.header['height']  
                if tga.header['bits_per_pixel'] == 32:          
                    image = Image.frombuffer('RGBA', (width, height), tga.image, 'raw', 'BGRA', 0, 1)
                elif tga.header['bits_per_pixel'] == 24:
                    image = Image.frombuffer('RGBA', (width, height), tga.image, 'raw', 'BGR', 0, 1)
                elif tga.header['bits_per_pixel'] == 8:
                    image = Image.frombuffer('RGBA', (width, height), tga.image, 'raw', 'BGRA', 0, 1)
                if tga.header['descriptor']['origin'] == "bottom": image = image.transpose(Image.FLIP_TOP_BOTTOM)
                resized = image.resize(self._scale_resolution(width,height), Image.LANCZOS)
                photo = ImageTk.PhotoImage(resized)
                self.canvas.delete("all")
                self.canvas.create_image(100, 100, image=photo)
                self.canvas.image = photo
                if tga.header['image_type'] == 2: self.modify_button.config(state='normal')
            elif name.endswith('.STI'):
                image = self.load_sti(file_bytes)
                if image is None: 
                    return
                resized = image.resize(self._scale_resolution(image.size[0],image.size[1]), Image.LANCZOS)
                photo = ImageTk.PhotoImage(resized)
                self.canvas.delete("all")
                self.canvas.create_image(100, 100, image=photo)
                self.canvas.image = photo
                self.modify_button.config(state='normal')
            elif name.endswith('.TXT'):
                content = file_bytes.decode('utf-8')
                self._update_info(f"Text File: {name.split('/')[-1]}\nContent:\n{content}")
                self.canvas.delete("all")
                self.canvas.create_text(100, 100, text=f"{name.split('/')[-1]}", fill="white")
                
            else:
                self.canvas.delete("all")
                self.canvas.create_text(100, 100, text=f"{name.split('/')[-1]}", fill="white")
        except Exception as e:
            self.canvas.delete("all")
            self.canvas.create_text(100, 100, text="Error loading file", fill="white")
    
    def load_sti(self, file_bytes):
        flags = int.from_bytes(file_bytes[16:20], 'little')
        transparent, high, indexed, zlib, etrle = ((flags >> i) & 1 for i in (0, 2, 3, 4, 5))      
        if high:          
            sti = STI16(file_bytes)
            img = Image.frombytes('RGB', (sti.width, sti.height), sti.image)
        elif indexed:
            sti = STI8(file_bytes)
            if sti.num_images > 1:
                self.current_image_index = max(0, min(self.current_image_index, sti.num_images - 1))
                sti.index = self.current_image_index
                if hasattr(self, 'nav_frame') and self.nav_frame:
                    for widget in self.nav_frame.winfo_children():
                        widget.destroy()
                    prev_btn = tk.Button(self.nav_frame, text="Previous", command=self.prev_img)
                    prev_btn.pack(side=tk.LEFT, padx=5)
                    
                    self.index_label = tk.Label(self.nav_frame, text=f"{self.current_image_index + 1}/{sti.num_images}")
                    self.index_label.pack(side=tk.LEFT, padx=5)
                    
                    next_btn = tk.Button(self.nav_frame, text="Next", command=self.next_img)
                    next_btn.pack(side=tk.LEFT, padx=5)
                    self.nav_frame.pack(side=tk.TOP)
                    
                    img = Image.frombytes('RGBA', (sti.sub_header[self.current_image_index]['width'], sti.sub_header[self.current_image_index]['height']), sti.images[self.current_image_index])           
                else:
                    img = Image.frombytes('RGBA', (sti.sub_header[0]['width'], sti.sub_header[0]['height']), sti.images[0])
            else:
                self.nav_frame.pack_forget()
                img = Image.frombytes('RGBA', (sti.sub_header[0]['width'], sti.sub_header[0]['height']), sti.images[0])
        else:
            self.canvas.delete("all")
            self.canvas.create_text(100, 100, text="Unsupported STI", fill="white")
            return None
        self._update_info(sti)  
        return img


    def select_slf_file(self):
        path = filedialog.askopenfilename(title="Select SLF File", filetypes=[("SLF files", "*.SLF"), ("All files", "*.*")])
        if path:
            self.slf_file = path
            self.file_label.config(text=os.path.basename(path))
            self.load_slf_entries()

    def load_slf_entries(self):
        try:
            self.slf = SLF(self.slf_file)
            self.tree.delete(*self.tree.get_children())
            for name, (addr, size) in self.slf.files.items():
                file_type = name[-3:]
                self.tree.insert("", tk.END, values=(name, file_type, f"0x{addr:08X}", size))
            self.status.config(text=f"Loaded {len(self.slf.files)} files")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read SLF file:\n{str(e)}")
            self.status.config(text="Error loading file")
        
    def modify_file(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "No file selected for modification")
            return
        
        item = selection[0]
        name, type, addr_hex, size = self.tree.item(item, 'values')

        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tga")]
        )        
        if type == "TGA":     
            if file_path:      
                try:
                    tga = TGA(self.slf.extract(name)) 
                    selected_img = Image.open(file_path)
                    width = tga.header['width']
                    height = tga.header['height']
                    resized_img = selected_img.resize((width, height), Image.LANCZOS)
                    
                    if tga.header['bits_per_pixel'] == 32:
                        if resized_img.mode != 'RGBA':
                            resized_img = resized_img.convert('RGBA')
                        tga.image = resized_img.tobytes()
                    elif tga.header['bits_per_pixel'] == 24:
                        if resized_img.mode != 'RGB':
                            resized_img = resized_img.convert('RGB')
                        bgr_data = resized_img.tobytes('raw', 'BGR')
                        tga.image = bgr_data
                    elif tga.header['bits_per_pixel'] == 8:
                        if resized_img.mode != 'RGBA':
                            resized_img = resized_img.convert('RGBA')
                        tga.image = resized_img.tobytes()
                        
                    if tga.header['descriptor']['origin'] == "bottom":
                        if tga.header['bits_per_pixel'] == 32 or tga.header['bits_per_pixel'] == 8:
                            flipped_data = Image.frombytes('RGBA', (width, height), tga.image)
                            flipped_data = flipped_data.transpose(Image.FLIP_TOP_BOTTOM)
                            tga.image = flipped_data.tobytes('raw', 'BGRA')         
                        elif tga.header['bits_per_pixel'] == 24:      
                            flipped_data = Image.frombytes('RGB', (width, height), tga.image)
                            flipped_data = flipped_data.transpose(Image.FLIP_TOP_BOTTOM)
                            tga.image = flipped_data.tobytes()                                
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to replace TGA image: {str(e)}")
            self.modified_file = tga.save()
            self.display_file(name)
            self.extract_button.pack_forget()
            self.save_modified_button.pack(side=tk.LEFT)
            self.save_patch_button.pack(side=tk.LEFT)
        elif type == "STI":
            if file_path:
                try:
                    selected_img = Image.open(file_path)  
                    file_bytes = self.slf.extract(name)
                    flags = int.from_bytes(file_bytes[16:20], 'little')
                    transparent, high, indexed, zlib, etrle = ((flags >> i) & 1 for i in (0, 2, 3, 4, 5))          
                    if high:
                        sti = STI16(self.slf.extract(name))
                        width = sti.width
                        height = sti.height
                        resized_img = selected_img.resize((width, height), Image.LANCZOS)
                        sti.image = resized_img.convert('RGB').tobytes()
                        self.modified_file = sti.save()
                        self.display_file(name)
                        self.extract_button.pack_forget()
                        self.save_modified_button.pack(side=tk.LEFT)
                        self.save_patch_button.pack(side=tk.LEFT)         
                    elif indexed:
                        if self.modified_file is not None:
                            sti = STI8(self.modified_file)
                        else:
                            sti = STI8(self.slf.extract(name))
                        width = sti.sub_header[self.current_image_index]['width']
                        height = sti.sub_header[self.current_image_index]['height']
                        resized_img = selected_img.resize((width, height), Image.LANCZOS)
                        sti.images[self.current_image_index] = resized_img.convert('RGBA').tobytes()
                        self.modified_file = sti.save()
                        self.display_file(name)
                        self.extract_button.pack_forget()
                        self.save_modified_button.pack(side=tk.LEFT)
                        self.save_patch_button.pack(side=tk.LEFT)        
                    else:
                        messagebox.showwarning("Warning", "Unsupported STI format for modification")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to replace STI image: {str(e)}")   
        else:
            messagebox.showwarning("Warning", "Only TGA and STI files can be modified")


    def extract_files(self):
        items = self.tree.selection()
        if not items:
            messagebox.showwarning("Warning", "No files selected for extraction")
            return
        extract_dir = filedialog.askdirectory(title="Select Extraction Directory")
        if not extract_dir: return
        try:
            for item in items:
                name, type, addr_hex, size = self.tree.item(item, 'values')
                addr = int(addr_hex, 16)
                size = int(size)
                full_path = os.path.join(extract_dir, name.split('\\')[-1])
                dir_path = os.path.dirname(full_path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                self.slf.extract(name, full_path)
            messagebox.showinfo("Success", f"Successfully extracted {len(items)} files")
            self.status.config(text=f"Extracted {len(items)} files to {extract_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract files:\n{str(e)}")
            self.status.config(text="Extraction failed")
    
    def save_modified(self):
        name, type, addr_hex, size = self.tree.item(self.tree.selection()[0], 'values')
        if type == "TGA":
            TGA(self.modified_file).save(name.split('\\')[-1])
        if type == "STI":
            flags = int.from_bytes(self.modified_file[16:20], 'little')
            transparent, high, indexed, zlib, etrle = ((flags >> i) & 1 for i in (0, 2, 3, 4, 5))
            if high:
                STI16(self.modified_file).save(name.split('\\')[-1])
            elif indexed:
                STI8(self.modified_file).save(name.split('\\')[-1])    
            else:
                messagebox.showerror("Error", f"Failed to save STI, file not valid.")   
                    
    
    def save_patch(self):
         messagebox.showinfo("Failed", "Not implemented")
        
    def _find_wiz8_dir(self):
        try:
            possible_dirs = [
                ".",
                "..",
                os.path.expanduser("~/.local/share/Steam/steamapps/common/Wizardry8"),  # Linux Steam
                os.path.expanduser("%USERPROFILE%\\Steam\\steamapps\\common\\Wizardry8"),  # Windows Steam
                "C:\\Steam\\steamapps\\common\\Wizardry8",
                "C:\\SteamLibrary\\steamapps\\common\\Wizardry8",
                "D:\\SteamLibrary\\steamapps\\common\\Wizardry8",
                "E:\\SteamLibrary\\steamapps\\common\\Wizardry8",
            ]
            
            for dir in possible_dirs:
                if os.path.exists(os.path.join(dir, "Wiz8.exe")):
                    return dir
            return None
        except Exception as e:
            print(f"Error finding Wizardry 8 directory: {e}")
            return None
        
class TGA:
    def __init__(self, data=None):
        self.header = self.footer = self.image = None
        if data is not None:
            raw_data = open(data, 'rb').read() if isinstance(data, str) else data
            self._parse_tga(raw_data)

    def _parse_tga(self, data):
        if len(data) < 18:
            raise ValueError("Invalid TGA file: too short")
            
        h = data[:18]
        self.header = {
            "id_length": h[0], "color_map_type": h[1], "image_type": h[2],
            "color_map_origin": h[3] + (h[4] << 8), "color_map_length": h[5] + (h[6] << 8),
            "color_map_depth": h[7], "x_origin": h[8] + (h[9] << 8), "y_origin": h[10] + (h[11] << 8),
            "width": h[12] + (h[13] << 8), "height": h[14] + (h[15] << 8),
            "bits_per_pixel": h[16],
            "descriptor": {
                "alpha_bits": h[17] & 0x0F,
                "origin": "top" if h[17] & 0x20 else "bottom"
            }
        }

        offset = 18 + self.header["id_length"]
        if self.header["color_map_type"]:
            offset += self.header["color_map_length"] * ((self.header["color_map_depth"] + 7) // 8)

        pixel_size = self.header["bits_per_pixel"] // 8
        img_size = self.header["width"] * self.header["height"] * pixel_size
        
        try:
            if self.header["image_type"] == 1:  # Type 1: Uncompressed color-mapped
                pixel_indices = data[offset:offset + img_size]
                
                color_map_size = self.header["color_map_length"] * (self.header["color_map_depth"] // 8)
                color_map_data = data[18:18 + color_map_size]
                
                color_map = []
                color_depth = self.header["color_map_depth"]
                bytes_per_color = (color_depth + 7) // 8
                
                for i in range(self.header["color_map_length"]):
                    color_start = i * bytes_per_color
                    if color_start + bytes_per_color <= len(color_map_data):
                        if bytes_per_color == 3:
                            r, g, b = color_map_data[color_start:color_start + 3]
                            color_map.append((r, g, b, 255))
                        elif bytes_per_color == 4:
                            r, g, b, a = color_map_data[color_start:color_start + 4]
                            color_map.append((r, g, b, a))
                
                pixel_data = []
                for index in pixel_indices:
                    if index < len(color_map):
                        pixel_data.extend(color_map[index])
                    else:
                        pixel_data.extend((0, 0, 0, 255))
                
                self.image = bytes(pixel_data)

            elif self.header["image_type"] == 2:  # Type 2: Uncompressed RGB
                self.image = data[offset:offset + img_size]
            elif self.header["image_type"] == 3:  # Type 3: Uncompressed Greyscale
                pixel_data = []
                pixel_count = self.header["width"] * self.header["height"]
                gray_bytes = data[offset:offset + pixel_count * pixel_size]
            
                for i in range(pixel_count):
                    if pixel_size == 1:
                        # 8-bit greyscale
                        gray = gray_bytes[i]
                    elif pixel_size == 2:
                        # 16-bit greyscale (rare, use LSB or full value scaled down)
                        gray = gray_bytes[i * 2 + 1]  # Little-endian LSB
                    else:
                        raise ValueError(f"Invalid pixel size for greyscale: {pixel_size}")
                    pixel_data.extend([gray, gray, gray, 255])
            
                self.image = bytes(pixel_data)   
            elif self.header["image_type"] == 10:  # Type 10: Run-Length Encoded RGB
                pixel_data = []
                pixel_count = self.header["width"] * self.header["height"]
                i = offset
                
                while len(pixel_data) < pixel_count * pixel_size:
                    if i >= len(data):
                        raise ValueError("Invalid RLE data: unexpected end of file")
                        
                    header = data[i]
                    i += 1
                    
                    if header & 0x80:  # Run-length packet
                        packet_length = (header & 0x7F) + 1
                        if i + pixel_size > len(data):
                            raise ValueError("Invalid RLE data: incomplete packet")
                        pixel = data[i:i + pixel_size]
                        i += pixel_size
                        pixel_data.extend(pixel * packet_length)
                    else:  # Raw packet
                        packet_length = header + 1
                        if i + packet_length * pixel_size > len(data):
                            raise ValueError("Invalid RLE data: incomplete packet")
                        pixel_data.extend(data[i:i + packet_length * pixel_size])
                        i += packet_length * pixel_size
                
                self.image = bytes(pixel_data)
            else:
                raise ValueError(f"Unsupported TGA image type: {self.header['image_type']}")

            if len(data) >= 26:
                f = data[-26:]
                sig = f[8:24].rstrip(b'\x00').decode('ascii', errors='ignore')
                self.footer = {
                    "extension_offset": int.from_bytes(f[:4], 'little'),
                    "developer_offset": int.from_bytes(f[4:8], 'little'),
                    "signature": sig + chr(f[24]),
                    "valid": sig == "TRUEVISION-XFILE" and f[25] == 0
                }
        except Exception as e:
            raise ValueError(f"Error parsing TGA: {str(e)}")

    def save(self, filename=None):
        if self.header["image_type"] != 2:
            raise ValueError(f"Saving not supported for TGA image type: {self.header['image_type']}")
        
        # Create the TGA data in memory
        data = bytearray()
        h = self.header
        desc = h["descriptor"]
        data.extend(bytes([
            h["id_length"], h["color_map_type"], h["image_type"],
            h["color_map_origin"], h["color_map_origin"] >> 8,
            h["color_map_length"], h["color_map_length"] >> 8,
            h["color_map_depth"],
            h["x_origin"], h["x_origin"] >> 8,
            h["y_origin"], h["y_origin"] >> 8,
            h["width"], h["width"] >> 8,
            h["height"], h["height"] >> 8,
            h["bits_per_pixel"],
            desc["alpha_bits"] | (0x20 if desc["origin"] == "top" else 0)
        ]))
        data.extend(self.image)
        if self.footer and self.footer["valid"]:
            fb = bytearray(26)
            fb[:4] = self.footer["extension_offset"].to_bytes(4, 'little')
            fb[4:8] = self.footer["developer_offset"].to_bytes(4, 'little')
            sig = self.footer["signature"].rstrip('\x00').encode('ascii')[:17]
            fb[8:25] = sig.ljust(17, b'\x00')
            fb[25] = 0
            data.extend(fb)
        
        # Return bytes if no filename provided, otherwise save to file
        if filename is None:
            return bytes(data)
        else:
            with open(filename, 'wb') as f:
                f.write(data)

    def __str__(self):
        def format_key(key):
            return ' '.join(word.capitalize() for word in key.replace('_', ' ').split())
        
        header_info = "\n".join([f"  {format_key(k)}: {v}" for k, v in self.header.items() if k != 'descriptor'])
        descriptor_info = ""
        if self.header.get('descriptor'):
            descriptor = self.header['descriptor']
            descriptor_info = "\n\t" + "\n\t".join(f"  {format_key(k)}: {v}" for k, v in descriptor.items())
        
        footer_info = "\n".join([f"  {format_key(k)}: {v}" for k, v in (self.footer or {}).items()]) if self.footer else "  None"
        
        return f"TGA Info\n"\
            f"Resolution: {self.header['width']}x{self.header['height']}\n" \
            f"Type: {self.header['image_type']}\n" \
            f"BitsPerPixel: {self.header['bits_per_pixel']}\n" \
            f"HasColorMap: {bool(self.header['color_map_type'])}\n" \
            f"Header:\n{header_info}\n" \
            f"Descriptor:{descriptor_info}\n" \
            f"Footer:\n{footer_info}"






if __name__ == "__main__":
    root = tk.Tk()
    app = SLFExtractor(root)  
    root.mainloop()
