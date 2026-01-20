import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from PIL import Image, ImageTk
from STI import STI8, STI16

class GUI:
    def __init__(self, default_portraits, modded_portraits):
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            self.root = TkinterDnD.Tk()
        except Exception as e:
            self.root = tk.Tk()

        # Initialize variables
        self.default_portraits = default_portraits
        self.modded_portraits = modded_portraits
        self.medium_image_index = 0
        self.patch_file = None
        self.current_selection = None
        self.cached_keys = ["", "", ""]
        self.loaded_sti = [b"", b"", b""]
        self.last_extract_dir = os.getcwd()
        self.extraction_format = 'PNG'

        # Theme colors
        self.bg_color = "#2c2c2c"
        self.fg_color = "#ffffff"
        self.button_bg = "#3a3a3a"
        self.highlight_color = "#5a5a5a"
        self.font_size = 13
        
        # Window setup
        root = self.root
        root.title("Wizardry 8 Portrait Swapper")
        if sys.platform == "win32":
            root.geometry("940x460")
        else:
            root.geometry("940x480")
        root.resizable(False, False)
        root.configure(bg=self.bg_color)
        self.center_window(root)
        
        try:
            root.drop_target_register(DND_FILES)
            root.dnd_bind('<<Drop>>', self.on_drop)
        except Exception as e:
            print("Drag & Drop Initialization Failed")      
                  
        # Main frame
        main_frame = ttk.Frame(root, padding="10", style="Dark.TFrame")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Styles
        style = ttk.Style()
        style.theme_use('alt')
        style.configure("Dark.TFrame", background=self.bg_color)
        style.configure("Dark.TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", self.font_size))

        
        # Listbox
        list_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.N, tk.S), pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.portrait_listbox = tk.Listbox(list_frame, width=12, height=12, 
                                         bg=self.button_bg, fg=self.fg_color,
                                         selectbackground=self.highlight_color,
                                         selectforeground=self.fg_color,
                                         relief=tk.FLAT,
                                         highlightthickness=0,
                                         selectborderwidth=4,  
                                         takefocus=False,
                                         activestyle=tk.NONE,
                                         font=("Segoe UI", self.font_size))
        self.portrait_listbox.grid(row=0, column=0, sticky=(tk.W, tk.N, tk.S, tk.E))
        self.portrait_listbox.bind('<<ListboxSelect>>', self.on_portrait_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.portrait_listbox.yview, style="Dark.Vertical.TScrollbar")
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.portrait_listbox.config(yscrollcommand=scrollbar.set)
        
        # Image display area
        image_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        image_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10, padx=(1,0))
        image_frame.columnconfigure(0, weight=1)
        image_frame.columnconfigure(1, weight=1)
        image_frame.columnconfigure(2, weight=1)
        
        # Canvas displays
        self.large_canvas = tk.Canvas(image_frame, width=360, height=288, bg='black', highlightthickness=0)
        self.large_canvas.grid(row=1, column=0, padx=2, pady=0, sticky=tk.N)
                
        self.medium_canvas = tk.Canvas(image_frame, width=180, height=144, bg='grey', highlightthickness=0)
        self.medium_canvas.grid(row=1, column=1, padx=2, pady=0, sticky=tk.N)
             
        # Medium slider
        self.slider_labels = ["Base Portrait", "Eyes Neutral", "Eyes Closed", "Eyes Lidded", "Eyes Angry", 
                        "Eyes Shocked", "Mouth Neutral", "Mouth Half Open", "Mouth Open", "Mouth Grimace"]
        
        self.medium_slider = tk.Scale(image_frame, from_=0, to=9, orient=tk.HORIZONTAL, 
                                    command=self.on_medium_slider_change, length=180,
                                    label=self.slider_labels[0], showvalue=False,
                                    bg=self.bg_color, activebackground=self.highlight_color, fg=self.fg_color, relief=tk.FLAT,
                                    troughcolor=self.button_bg, sliderrelief=tk.RAISED,
                                    highlightthickness=0, font=("Segoe UI", self.font_size))
        self.medium_slider.grid(row=1, column=1, padx=5, pady=140, sticky=tk.N)
        self.medium_slider.set(0)

        alpha_frame = tk.Frame(image_frame, bg=self.bg_color)
        alpha_frame.grid(row=1, column=1, padx=2, pady=100, sticky=tk.S)
        
        alpha_label = tk.Label(alpha_frame, text="Alpha Color:", bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", self.font_size))
        alpha_label.pack(side=tk.LEFT)

        self.alpha_value = tk.Label(alpha_frame, text="", bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", self.font_size))
        self.alpha_value.pack(side=tk.LEFT)
        
        self.small_canvas = tk.Canvas(image_frame, width=90, height=72, bg='black', highlightthickness=0)
        self.small_canvas.grid(row=1, column=2, padx=2, pady=0, sticky=tk.N)
        
        # Buttons
        self.save_button = ttk.Button(main_frame, text="Save", command=self.save)
        self.save_button.grid(row=1, column=0, columnspan=2, pady=10, padx=5, sticky=tk.SE)
        
        self.change_button = ttk.Button(main_frame, text="Change Portrait", command=self.change_portrait)
        self.change_button.grid(row=1, column=1, pady=10, sticky=tk.SE, padx=140)
        
        self.extract_button = ttk.Button(main_frame, text="Extract", command=self.extract)
        self.extract_button.grid(row=1, column=1, pady=10, sticky=tk.SW, padx=5)
        
        self.defaults_button = ttk.Button(main_frame, text="Restore Defaults", command=self.restore_defaults)
        self.defaults_button.grid(row=1, column=0, pady=10, sticky=tk.SW, padx=5)

        
        
        # Button styles
        style.configure('TButton', 
                        background=self.button_bg, 
                        foreground=self.fg_color, 
                        font=('TkDefaultFont', self.font_size),
                        relief='raised',
                        borderwidth=5)
        
        style.map('TButton', 
                background=[('active', self.highlight_color)],
                relief=[('pressed', 'sunken')])
 
        # Scrollbar style
        style.configure("Dark.Vertical.TScrollbar",
                        background=self.button_bg,
                        troughcolor=self.button_bg,
                        arrowcolor=self.fg_color,
                        bordercolor=self.bg_color,
                        lightcolor=self.button_bg,
                        darkcolor=self.button_bg,
                        width=15,
                        elementborderwidth=10)
        
        style.map("Dark.Vertical.TScrollbar",
                background=[('active', self.highlight_color)],
                arrowcolor=[('active', self.fg_color)])
        
        # Slider Style
        style.configure("Horizontal.TScale",
                        background=self.bg_color,
                        troughcolor=self.button_bg,
                        foreground=self.fg_color,
                        bordercolor=self.button_bg,
                        lightcolor=self.button_bg,
                        darkcolor=self.button_bg)
                        
        style.map("Horizontal.TScale",
                background=[('active', self.highlight_color)],
                troughcolor=[('active', self.highlight_color)])
                       



        # Populate listbox
        self.populate_portrait_listbox()    
        
       # Select first item if available
        if self.portrait_listbox.size() > 0:
            self.portrait_listbox.selection_set(0)
            self.current_selection = self.portrait_listbox.get(0)
            self.load_portraits(self.current_selection)
             
    def populate_portrait_listbox(self):
        portrait_names = set()
        for key in self.modded_portraits.keys():
            if key.startswith(("PORTRAITS\\LARGE\\", "PORTRAITS/LARGE/")):
                portrait_names.add(key[17:-4])
        for key in self.default_portraits.keys():
            if key.startswith(("PORTRAITS\\LARGE\\", "PORTRAITS/LARGE/")):
                portrait_names.add(key[17:-4])

        # Sort and populate listbox
        sorted_names = sorted(list(portrait_names))
        for name in sorted_names:
            self.portrait_listbox.insert(tk.END, name)
        
    def on_portrait_select(self, event=None):
        self.medium_image_index = 0
        self.medium_slider.set(0)
        selection = self.portrait_listbox.curselection()
        if selection:
            selected_name = self.portrait_listbox.get(selection[0])
            self.current_selection = selected_name
            self.load_portraits(selected_name)

    def on_medium_slider_change(self, value):
        self.medium_image_index = int(float(value))
        self.medium_slider.config(label=self.slider_labels[int(float(value))])
        
        if self.current_selection is not None:
            self.load_portraits(self.current_selection)

    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        
        self.change_portrait(files)
    
    def load_portraits(self, name):
        try:
            if self.cached_keys[0] != f"PORTRAITS\\LARGE\\L{name}.STI":
                special_names = {"DRAZIC", "GLUMPH", "MADRAS", "MYLES", "RFS-81", "RODAN", "SAXX", "SEXUS", "SPARKLE", "TANTRIS", "URQ", "VI"}
                
                self.cached_keys[0] = f"PORTRAITS\\LARGE\\L{name}.STI"
                
                self.cached_keys[1] = f"PORTRAITS\\MEDIUM\\A{name}.STI" if name in special_names else f"PORTRAITS\\MEDIUM\\M{name}.STI"
                
                self.cached_keys[2] = f"PORTRAITS\\SMALL\\S{name}.STI"
     
                # Large portrait                                                
                self.loaded_sti[0] = STI16(self.modded_portraits.get(self.cached_keys[0]) or self.default_portraits[self.cached_keys[0]])
                self.display_image(self.loaded_sti[0].image, self.large_canvas, self.loaded_sti[0].width, self.loaded_sti[0].height)
                
                # Medium portrait
                self.loaded_sti[1] = STI8(self.modded_portraits.get(self.cached_keys[1]) or self.default_portraits[self.cached_keys[1]])
                self.medium_image_count = self.loaded_sti[1].num_images
                self.display_image(self.loaded_sti[1].images, self.medium_canvas, self.loaded_sti[1].sub_header[self.medium_image_index]['width'], self.loaded_sti[1].sub_header[self.medium_image_index]['height'])
                self.alpha_value['text'] = '#{:02x}{:02x}{:02x}'.format(*self.loaded_sti[1].palette[0])
                self.alpha_value.config(fg=self.alpha_value['text'])
                # Small portrait
                if name in special_names:
                    self.loaded_sti[2] = STI8(self.modded_portraits.get(self.cached_keys[2]) or self.default_portraits[self.cached_keys[2]])
                    self.display_image(self.loaded_sti[2].images, self.small_canvas, self.loaded_sti[2].sub_header[0]['width'], self.loaded_sti[2].sub_header[0]['height'])
                else:
                    self.loaded_sti[2] = STI16(self.modded_portraits.get(self.cached_keys[2]) or self.default_portraits[self.cached_keys[2]])
                    self.display_image(self.loaded_sti[2].image, self.small_canvas, self.loaded_sti[2].width, self.loaded_sti[2].height)
            else:
                # Cycle medium portraits (when slider is moved)
                self.medium_image_count = self.loaded_sti[1].num_images
                self.medium_slider.config(to=self.medium_image_count-1)
                self.display_image(self.loaded_sti[1].images, self.medium_canvas, self.loaded_sti[1].sub_header[self.medium_image_index]['width'], self.loaded_sti[1].sub_header[self.medium_image_index]['height'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load portraits: {str(e)}")
    
    def display_image(self, image_data, canvas, width, height):
        try:
            canvas.delete("all")
            canvas.config(width=width * 2, height=height * 2)
            
            if isinstance(image_data, list):
                img = Image.new('RGBA', (width, height))
                index = min(self.medium_image_index, len(image_data) - 1)
                img.putdata([(r, g, b, a) for r, g, b, a in zip(image_data[index][::4], image_data[index][1::4], image_data[index][2::4], image_data[index][3::4])])
                if self.medium_image_index != 0: 
                    # Render the base portrait underneath the anims, like it would be in the game.
                    base_img = Image.new('RGBA', (width, height))
                    base_img.putdata([(r, g, b, a) for r, g, b, a in zip(image_data[0][::4], image_data[0][1::4], image_data[0][2::4], image_data[0][3::4])])
                    img = Image.alpha_composite(base_img, img)
            else:
                img = Image.new('RGB', (width, height))
                img.putdata([(r, g, b) for r, g, b in zip(image_data[::3], image_data[1::3], image_data[2::3])])
            
            img = img.resize((width * 2, height * 2), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            canvas.create_image(width, height, image=photo)
            canvas.image = photo
        except Exception as e:
            print(f"Error displaying image: {str(e)}")
            canvas.delete("all")
            canvas.create_text(width//2, height//2, text="Error loading image")

    def clear_canvas(self, canvas):
        canvas.delete("all")
        canvas.create_text(100, 100, text="No image")
        
    def refresh(self):
                self.cached_keys[0] = ''
                self.load_portraits(self.current_selection)
    def center_window(self, window):
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (window.winfo_width() // 2)
        y = (window.winfo_screenheight() // 2) - (window.winfo_height() // 2)
        window.geometry(f'+{x}+{y}')
         
    def change_portrait(self, files = None):        
        if not files:
            files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("All Supported Files", "*.png *.sti *.PNG *.STI"), ("PNG Files", "*.png"), ("PNG Files", "*.PNG"), ("STI Files", "*.sti"), ("STI Files", "*.STI")])
            if not files:return
        files = sorted(files)    
        index = 0
        
        # Process each file
        for file_path in files:
            filenamename, extension = os.path.splitext(file_path)
            if extension.lower() == '.png':
                try:
                    img = Image.open(file_path)
                    width, height = img.size
                    
                    # Handle large portraits (180x144)
                    if width == 180 and height == 144:
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                        raw_data = list(img.getdata())
                        self.loaded_sti[0].image = bytes(pixel for rgb in raw_data for pixel in rgb)
                        self.loaded_sti[0].modified = True
    
                    # Handle medium portraits (90x72)
                    elif width == 90 and height == 72:
                        if len(files) <= 3: index = self.medium_image_index
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        raw_data = list(img.getdata())
                        self.loaded_sti[1].images[index] = [pixel for rgb in raw_data for pixel in rgb]
                        self.loaded_sti[1].modified = True
                        index += 1
                        
                    # Handle small portraits (45x36 or 46x36)
                    elif height == 36 and width in [45, 46]:
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                        raw_data = list(img.getdata())
                        self.loaded_sti[2].image = bytes(pixel for rgb in raw_data for pixel in rgb)   
                        self.loaded_sti[2].width = width
                        self.loaded_sti[2].height = height
                        self.loaded_sti[2].modified = True
                    else:
                        messagebox.showerror("Error", f"Incompatible image resolution: {file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to process file {file_path}: {str(e)}")
            elif extension.lower() == '.sti':
                try:
                    buffer = STI16(file_path)
                    if buffer.width == 180 and buffer.height == 144:
                        self.loaded_sti[0] = buffer
                        self.loaded_sti[0].modified = True
                    elif buffer.high and buffer.height == 36 and buffer.width in [45, 46]:
                        self.loaded_sti[2] = buffer
                        self.loaded_sti[2].modified = True
                    else:
                        buffer = STI8(file_path)
                        if buffer.sub_header[0]['width'] == 90 and buffer.sub_header[0]['height'] == 72:
                            self.loaded_sti[1] = buffer
                            self.loaded_sti[1].modified = True
                        elif  buffer.sub_header[0]['height'] == 36 and buffer.sub_header[0]['width'] in [45, 46]:
                            self.loaded_sti[2] = buffer
                            self.loaded_sti[2].modified = True
                        else:
                            messagebox.showerror("Error", f"Incompatible image resolution: {file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to process file {file_path}: {str(e)}") 
            else:
                messagebox.showerror("Error", f"File is not PNG or STI: {file_path}")                        
                
        # Update display
        self.display_image(self.loaded_sti[0].image, self.large_canvas, self.loaded_sti[0].width, self.loaded_sti[0].height)
        self.display_image(self.loaded_sti[1].images, self.medium_canvas, self.loaded_sti[1].sub_header[self.medium_image_index]['width'], self.loaded_sti[1].sub_header[self.medium_image_index]['height'])
        if hasattr(self.loaded_sti[2], 'image'):
            self.display_image(self.loaded_sti[2].image, self.small_canvas, self.loaded_sti[2].width, self.loaded_sti[2].height)
        else:
            self.display_image(self.loaded_sti[2].images, self.small_canvas, self.loaded_sti[2].width, self.loaded_sti[2].height)

      
    def restore_defaults(self):
        # Create custom dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Restore Defaults")
        if sys.platform == "win32":
            dialog.geometry("430x100")
        else:
            dialog.geometry("430x110")
        dialog.configure(bg=self.bg_color)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        self.center_window(dialog)
        

        message_label = ttk.Label(dialog, text="Which portraits would you like to reset?", 
                                background=self.bg_color, foreground=self.fg_color, font=('SegoeUI', self.font_size + 2), wraplength=400)
        message_label.pack(pady=10)
        
        button_frame = ttk.Frame(dialog, style="Dark.TFrame")
        button_frame.pack(pady=10)
        
        def on_button_click(result):
            dialog.result = result
            dialog.destroy()
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda: on_button_click('cancel'))
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        this_portrait_button = ttk.Button(button_frame, text="This Portrait", 
                                        command=lambda: on_button_click('this_portrait'))
        this_portrait_button.pack(side=tk.LEFT, padx=5)
        
        yes_button = ttk.Button(button_frame, text="All Portraits", command=lambda: on_button_click('yes'))
        yes_button.pack(side=tk.LEFT, padx=5)
        
        self.root.wait_window(dialog)
        
        result = getattr(dialog, 'result', None)
        
        if result == 'yes':
            # Restore all portraits
            for key in list(self.modded_portraits.keys()):
                if key in self.default_portraits:
                    del self.modded_portraits[key]
            self.refresh()
        elif result == 'this_portrait':
            # Restore current portrait only
            keys = [ 
                f"PORTRAITS\\LARGE\\L{self.current_selection}.STI",
                f"PORTRAITS\\MEDIUM\\M{self.current_selection}.STI",
                f"PORTRAITS\\MEDIUM\\A{self.current_selection}.STI",
                f"PORTRAITS\\SMALL\\S{self.current_selection}.STI"
            ]
            for key in keys:
                if key in self.modded_portraits:
                    del self.modded_portraits[key]
            self.refresh()
        
    def extract(self):
        if not self.loaded_sti:
            print("No data loaded.")
            return
    
        # Create custom dialog for format selection
        dialog = tk.Toplevel(self.root)
        dialog.title("Extract As...")
        if sys.platform == "win32":
            dialog.geometry("500x190")
        else:
            dialog.geometry("500x200")
        dialog.configure(bg=self.bg_color)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog)
        
        # Format selection
        format_var = tk.StringVar(value="PNG")
        format_label = ttk.Label(dialog, text="Save As:", background=self.bg_color, foreground=self.fg_color)
        format_label.pack(pady=10)
    
        format_combo = ttk.Combobox(dialog, textvariable=format_var, values=["PNG", "STI"], state="readonly", width=10)
        format_combo.pack(pady=5)
        format_combo.set(self.extraction_format)
    
        # Directory selection
        save_dir = tk.StringVar()
        save_dir.set(self.last_extract_dir)
        def select_directory():
            dir_path = filedialog.askdirectory(title="Select Folder to Save Files")
            if dir_path:
                save_dir.set(dir_path)
    
        dir_frame = tk.Frame(dialog, bg=self.button_bg)
        dir_frame.pack(pady=10)
    
        dir_entry = tk.Entry(dir_frame, textvariable=save_dir, width=40)
        dir_entry.pack(side=tk.LEFT, padx=(0, 5))
        dir_entry.configure(bg=self.bg_color, fg=self.fg_color)
    
        dir_button = ttk.Button(dir_frame, text="Browse", command=select_directory)
        dir_button.pack(side=tk.LEFT)
        
        result = None
    
        def on_extract():
            nonlocal result
            if not save_dir.get():
                messagebox.showwarning("Warning", "Please select a directory.")
                return
            result = {
                'dir': save_dir.get(),
                'format': format_var.get()
            }
            dialog.destroy()
    
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.bg_color)
        button_frame.pack(pady=10)
    
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Extract", command=on_extract).pack(side=tk.RIGHT, padx=5)
            
        # Wait for user input
        self.root.wait_window(dialog)
    
        if not result:
            return
    
        save_dir = result['dir']
        self.last_extract_dir = result['dir']
        save_format = result['format']
        self.extraction_format = result['format']
    
        def clean_filename(key):
            base = key.split('\\')[-1]
            return base.replace('.STI', '')
    
        try:
            if save_format == "PNG":
                width = self.loaded_sti[0].width
                height = self.loaded_sti[0].height
                img_data = self.loaded_sti[0].image
                name = clean_filename(self.cached_keys[0])
                img = Image.frombytes('RGB', (width, height), img_data)
                img.save(os.path.join(save_dir, f"{name}.png"), 'PNG')
    

                base_name = clean_filename(self.cached_keys[1])
                is_medium = "MEDIUM" in self.cached_keys[1]
                for idx, img_data in enumerate(self.loaded_sti[1].images):
                    width = self.loaded_sti[1].sub_header[idx]['width']
                    height = self.loaded_sti[1].sub_header[idx]['height']
                    mode = 'RGBA'
                    suffix = str(idx) if is_medium else f"_{idx}"
                    name = f"{base_name}{suffix}"
                    img = Image.frombytes(mode, (width, height), img_data)
                    img.save(os.path.join(save_dir, f"{name}.png"), 'PNG')
    
                if hasattr(self.loaded_sti[2], 'image') and self.loaded_sti[2].image:
                    width = self.loaded_sti[2].width
                    height = self.loaded_sti[2].height
                    img_data = self.loaded_sti[2].image
                    mode = 'RGB' if len(img_data) == width * height * 3 else 'RGBA'
                    name = clean_filename(self.cached_keys[2])
                    img = Image.frombytes(mode, (width, height), img_data)
                    img.save(os.path.join(save_dir, f"{name}.png"), 'PNG')
                elif hasattr(self.loaded_sti[2], 'images') and self.loaded_sti[2].images:
                    img_data = self.loaded_sti[2].images[0]
                    width = self.loaded_sti[2].sub_header[0]['width']
                    height = self.loaded_sti[2].sub_header[0]['height']
                    mode = 'RGB' if len(img_data) == width * height * 3 else 'RGBA'
                    name = clean_filename(self.cached_keys[2])
                    img = Image.frombytes(mode, (width, height), img_data)
                    img.save(os.path.join(save_dir, f"{name}.png"), 'PNG')
    
            elif save_format == "STI":
                name = clean_filename(self.cached_keys[0])
                sti_path = os.path.join(save_dir, f"{name}.STI")
                self.loaded_sti[0].save(sti_path)
                name = clean_filename(self.cached_keys[1])
                sti_path = os.path.join(save_dir, f"{name}.STI")
                self.loaded_sti[1].save(sti_path)
                name = clean_filename(self.cached_keys[2])
                sti_path = os.path.join(save_dir, f"{name}.STI")
                self.loaded_sti[2].save(sti_path)
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract: {str(e)}")



    def save(self):
        if self.patch_file:
            try:
                # Large portrait
                if hasattr(self.loaded_sti[0], 'save') and self.loaded_sti[0].modified:
                    print(f"Info: Saving {self.cached_keys[0]}")
                    self.modded_portraits[self.cached_keys[0]] = self.loaded_sti[0].save()
                
                # Medium portrait
                if hasattr(self.loaded_sti[1], 'save') and self.loaded_sti[1].modified:
                    print(f"Info: Saving {self.cached_keys[1]}")
                    self.modded_portraits[self.cached_keys[1]] = self.loaded_sti[1].save()
           
                # Small portrait
                if hasattr(self.loaded_sti[2], 'save') and self.loaded_sti[2].modified:
                    print(f"Info: Saving {self.cached_keys[2]}")               
                    self.modded_portraits[self.cached_keys[2]] = self.loaded_sti[2].save()
                    
                # Save the patch file
                self.patch_file.content = self.modded_portraits
                result = self.patch_file.save()
                messagebox.showinfo(result[0], result[1])
                
                # Refresh display
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save patch: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No patch file to save!")
