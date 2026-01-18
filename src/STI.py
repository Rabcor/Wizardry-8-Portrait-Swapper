import struct
from PIL import Image
import os
import numpy as np
from collections import Counter
from ETRLE import etrle_compress, etrle_decompress

class STI8:
    def __init__(self, source: Optional[Union[str, bytes]] = None):
        self.transparent, self.high, self.indexed, self.zlib, self.etrle = False, False, True, False, True
        self.size_real = self.size_uncompressed = self.size_compressed = 0
        self.height = 480
        self.width = 640
        self.num_colors = 256
        self.bit_depth = self.r_depth = self.g_depth = self.b_depth = 8
        self.num_images = 10
        self.palette = ((0,0,0)) * self.num_colors
        self.sub_header = self.images = []
        self.atlas = bytes()
        self.modified = False

        if source is not None:
            header_size = 64
            data = source if isinstance(source, bytes) else open(source, 'rb').read()
            if data[:4] != b'STCI':
                raise ValueError("Invalid STI file header")
            flags = struct.unpack('<I', data[16:20])[0]
            self.size_uncompressed = struct.unpack('<I', data[4:8])[0]
            self.size_compressed = struct.unpack('<I', data[8:12])[0]
            self.transparent, self.high, self.indexed, self.zlib, self.etrle = ((flags >> i) & 1 for i in (0, 2, 3, 4, 5))
            self.height, self.width = struct.unpack('<HH', data[20:24])
            self.num_colors = struct.unpack('<I', data[24:28])[0]
            self.r_depth, self.g_depth, self.b_depth = data[30], data[31], data[32]
            self.bit_depth = data[44]
            self.num_images = struct.unpack('<H', data[28:30])[0]
            p_size = self.num_colors * 3
            self.palette = tuple(tuple(data[64:64+p_size][i*3:i*3+3]) for i in range(256))
            sub_header_start = header_size + p_size
            img_start= sub_header_start + self.num_images * 16
            self.atlas = data[img_start:]
            if self.etrle: self.atlas = etrle_decompress(self.atlas,self.palette,self.width)
            for i in range(self.num_images):
                offset = sub_header_start + i * 16
                image_start = struct.unpack('<I', data[offset:offset+4])[0]
                size = struct.unpack('<I', data[offset+4:offset+8])[0]
                x = struct.unpack('<H', data[offset+8:offset+10])[0]
                y = struct.unpack('<H', data[offset+10:offset+12])[0]
                w = struct.unpack('<H', data[offset+14:offset+16])[0]
                h = struct.unpack('<H', data[offset+12:offset+14])[0]
                self.sub_header.append({'offset': image_start, 'size': size, 'x': x, 'y': y, 'height': h, 'width': w})
                self._split_atlas()
                
    def _split_atlas(self):
        self.images = []
        realsize = self.sub_header[0]['width'] * self.sub_header[0]['height'] * 4
        for i in range(self.num_images):
            self.images.append(self.atlas[realsize * i:realsize * i + realsize])
        
    def _join_atlas(self):
        realsize = self.sub_header[0]['width'] * self.sub_header[0]['height'] * 4
        new_atlas = bytearray()
        for image in self.images:
            new_atlas.extend(image)
        self.atlas = new_atlas  
             
        
    def _update_subheader(self, compressed_data):
        if self.etrle and self.indexed:
            current_pos = 0
            for i in range(self.num_images):
                self.sub_header[i]['offset'] = sum(self.sub_header[j]['size'] for j in range(i))
                pos = compressed_data.find(b'\xda\x00', current_pos)
                while pos + 4 <= len(compressed_data) and compressed_data[pos + 2:pos + 4] == b'\xda\x00':
                    pos += 2
                next_start = pos + 2
                lastsize = self.sub_header[i]['size']
                if i != 0: 
                    self.sub_header[i]['size'] = next_start - current_pos
                if i == 5: self.sub_header[i]['size'] = self.sub_header[i-1]['size'] # Ugly fix
                if i == 9: self.sub_header[i]['size'] = self.sub_header[i-1]['size'] # This is what regret looks like
                current_pos = next_start
        else:
            raise ValueError("Invalid File")
                
    def _fix_alpha(self): # Ensure transparent pixels are the correct color and black values are 1,1,1 instead of 0,0,0 because 0,0,0 is actually also alpha, which has lead to a great deal of grief...
        width = self.sub_header[0]['width']
        height = len(self.atlas) // (4 * width)
        buffer = np.frombuffer(self.atlas, dtype=np.uint8).reshape(height, width, 4)
        alpha_mask = (buffer[:, :, 3] == 0)
        buffer[alpha_mask, :3] = self.palette[0]
        black_mask = (buffer[:, :, 0] == 0) & (buffer[:, :, 1] == 0) & (buffer[:, :, 2] == 0)
        buffer[black_mask, :3] = [1, 1, 1]        
        self.atlas = buffer.tobytes()

    def _quantize_atlas(self):
        alpha = self.palette[0]
        end = self.palette[255]
        palette = [alpha]
        # extra = (0, 0, 0) if alpha == (255, 0, 0) else (255, 0, 0) if alpha == (0, 0, 255) else None # blue alpha images have (255,0,0) as palette[1] and red alpha images have (0,0,0) as palette[254] always in the game files. I doubt it matters.
        width = self.sub_header[0]['width']   
        height = len(self.atlas) // (4 * width)
        rgb_atlas = Image.frombytes('RGBA', (width, height), self.atlas).convert('RGB')
        
        img_array = np.array(rgb_atlas)
        pixels = img_array.reshape(-1, 3)
        unique_pixels = np.unique(pixels.view([('', pixels.dtype)] * pixels.shape[1])).view(pixels.dtype).reshape(-1, pixels.shape[1])
        
        # Remove alpha and end values if they exist in unique_pixels
        alpha_array = np.array(alpha)
        end_array = np.array(end)
        
        # Filter out alpha and end values if present
        mask = ~(np.all(unique_pixels == alpha_array, axis=1) | np.all(unique_pixels == end_array, axis=1))
        unique_pixels = unique_pixels[mask]
        
        # Check if we need padding
        color_count = len(unique_pixels)
    
        if color_count > 254: # Quantize
            print("\tInfo: Quantizing image")
            try: # To use libimagequant for quantization
                import libimagequant
            
                attr = libimagequant.Attr()
                attr.max_colors = 254
                attr.speed = 1
                attr.min_opacity = 0
                attr.last_index_transparent = True
                
                img = attr.create_rgba(self.atlas, width, height, gamma=1.0)
                result = img.quantize(attr)
                palette_colors = result.get_palette()
                palette = [(color.r, color.g, color.b) for color in palette_colors]
                remapped_indices = result.remap_image(img)
                                                             
                rgba_bytes = bytearray(width * height * 4)
                for i, index in enumerate(remapped_indices):
                    if index < len(palette):
                        r, g, b = palette[index]
                        rgba_bytes[i*4] = r
                        rgba_bytes[i*4+1] = g
                        rgba_bytes[i*4+2] = b
                        rgba_bytes[i*4+3] = 255
                    else:
                        rgba_bytes[i*4] = rgba_bytes[i*4+1] = rgba_bytes[i*4+2] = rgba_bytes[i*4+3] = 0
                
                for i in range(0, len(self.atlas), 4):
                    r, g, b, a = self.atlas[i], self.atlas[i+1], self.atlas[i+2], self.atlas[i+3]
                    if r == alpha[0]and g == alpha[1] and b == alpha[2] and a == 0:
                        rgba_bytes[i:i+4] = [alpha[0], alpha[1], alpha[2], 0]
                
                self.atlas = bytes(rgba_bytes)               
                            
                palette.insert(0, alpha)
                palette.append(end)
                self.palette = palette
                return
            except: # Fallback to pillow for quantization, not only is the quantization method worse, the code is also worse. Works tho, just generates suboptimal palettes.
                print("\tWarning: Quantizing with libimagequant failed, falling back to pillow...")
                palette_img = rgb_atlas.quantize(colors=254, method=1)
                palette = palette_img.getpalette()[:254*3]  # Get first 254*3 values (RGB triplets)
                palette = [tuple(palette[i:i+3]) for i in range(0, len(palette), 3)]
                palette.insert(0, alpha)
                palette[1] = (255,0,0)
                palette.append(end)
                self.atlas = palette_img.convert('RGBA').tobytes()
                
                # Make alpha color transparent
                atlas_list = list(self.atlas)
                for i in range(0, len(atlas_list), 4):
                    if (atlas_list[i], atlas_list[i+1], atlas_list[i+2]) == alpha:
                        atlas_list[i+3] = 0  # Set alpha to 0 (transparent)
                        
                self.atlas = bytes(atlas_list)
                self.palette = palette
                return
        else:
            # Add padding if needed to make it 254 colors before adding alpha and end
            padding_needed = 254 - color_count
            if padding_needed > 0:
                padding = np.zeros((padding_needed, 3), dtype=unique_pixels.dtype)
                unique_pixels = np.vstack([unique_pixels, padding]) 
        print("Info: Image was already quantized")                
        palette += [tuple(int(x) for x in pixel) for pixel in unique_pixels]
        palette.append(end)
        total_matches = sum((Counter(palette) & Counter(self.palette)).values())
        if total_matches < 254: # Use original palette if there were minimal changes. This allows the extract function in the GUI to extract the vanilla STI files unaltered.
            self.palette = palette 
                     
    def _update(self):
        self._join_atlas()
        self._fix_alpha()
        self._quantize_atlas()
        self._split_atlas()
               
        
    def save(self, filename: str = None):
        self._update()
        img_data = etrle_compress(self.atlas, self.palette, self.width, self.height, self.sub_header[0]['width'])
        self._update_subheader(img_data)
        self.size_uncompressed = self.width * self.height
        self.size_compressed = len(img_data)
        flags = (self.transparent | (self.high << 2) | (self.indexed << 3) | (self.zlib << 4) | (self.etrle << 5))

        header = (
            b'STCI' +
            struct.pack('<II', self.size_uncompressed, self.size_compressed) +
            b'\x00' * 4 +
            struct.pack('<IHHIHBBB', flags, self.height, self.width, self.num_colors, self.num_images, self.r_depth, self.g_depth, self.b_depth) +
            b'\x00' * 11 +
            struct.pack('<B', self.bit_depth) +
            b'\x00' * 19
        )
        if len(header) != 64: raise ValueError("Header must be 64 bytes.")
        
        palette = bytes([color for sublist in self.palette for color in sublist])
        if len(palette) != 768: raise ValueError("Palette contains ", len(palette) / 3, " colors, must contain 256.")
        
        sub_header = b''
        for entry in self.sub_header:
            sub_header += struct.pack('<IIHHHH', 
                                    entry['offset'], 
                                    entry['size'],    
                                    entry['x'],   
                                    entry['y'],    
                                    entry['height'],  
                                    entry['width'])  
    
        if len(sub_header) != self.num_images * 16: raise ValueError("Sub header size was not ", self.num_images * 16, " bytes.")
        
        data = header + palette + sub_header + img_data
        
        if filename is None:
            return data
        else:        
            with open(filename, 'wb') as f:
                f.write(data)
            
    def __str__(self):
        flags = []
        if self.transparent: flags.append("Transparent")
        if self.high: flags.append("High Color")
        if self.indexed: flags.append("Indexed")
        if self.zlib: flags.append("ZLIB")
        if self.etrle: flags.append("ETRLE")
        flags_str = "\n\t".join(flags) if flags else "None"
        
        if self.size_compressed == self.size_uncompressed:
            image_size_str = f"Image Size: {self.size_compressed}"
        else:
            image_size_str = f"Sizes:\n\tCompressed Atlas:    {self.size_compressed}\n\tUncompressed Atlas:  {self.size_uncompressed}\n\tUncompressed Images: {self.sub_header[0]['width'] * self.sub_header[0]['height'] * 3 * self.num_images}"
        
        return (
            f"STI8 File Information:\n"
            f"{'='*30}\n"
            f"Images: {len(self.images)}\n"
            f"Atlas Resolution: {self.width}x{self.height}\n"
            f"Image Resolution: {self.sub_header[0]['width']}x{self.sub_header[0]['height']}\n"
            f"Flags:\n\t{flags_str}\n"
            f"{image_size_str}\n\n"
            f"Color Information:\n\tColors: {self.num_colors}\n\tBit Depth: {self.bit_depth}\n\t\tR: {self.r_depth}\n\t\tG: {self.g_depth}\n\t\tB: {self.b_depth}\n"
            f"Palette:\n\t1:   {self.palette[0]} \n\t2:   {self.palette[1]}\n\t3:   {self.palette[2]} \n\t254: {self.palette[253]} \n\t255: {self.palette[254]} \n\t256: {self.palette[255]}\n\n"
            f"Compressed Atlas Header:\n{chr(10).join(f'\tImage {i+1:2} @{entry['offset']:04x}: {entry['x']},{entry['y']} {entry['width']}x{entry['height']}' + f' - {entry['size']} bytes' for i, entry in enumerate(self.sub_header))}"
        )


class STI16: # Needs some updating, test recreation of images with this.
    def __init__(self, source: Optional[Union[str, bytes]] = None):
        self.transparent, self.high, self.indexed, self.zlib, self.etrle = False, True, False, False, False
        self.size_uncompressed = self.size_compressed = self.height = self.width = 0
        self.num_colors, self.bit_depth = 63488, 16
        self.r_depth, self.g_depth, self.b_depth = 5, 6, 5
        self.r_mask, self.g_mask, self.b_mask = self.num_colors, 2016, 31
        self.image: bytes
        self.modified = False

        if source is not None:
            data = source if isinstance(source, bytes) else open(source, 'rb').read()
            if data[:4] != b'STCI':
                raise ValueError("Invalid STI file header")

            self.size_uncompressed = struct.unpack('<I', data[4:8])[0]
            self.size_compressed = struct.unpack('<I', data[8:12])[0]
            flags = struct.unpack('<I', data[16:20])[0]
            self.transparent, self.high, self.indexed, self.zlib, self.etrle = ((flags >> i) & 1 for i in (0, 2, 3, 4, 5))
            self.height, self.width = struct.unpack('<HH', data[20:24])
            self.num_colors = struct.unpack('<I', data[24:28])[0]
            self.r_mask, self.g_mask, self.b_mask = struct.unpack('<III', data[24:36])
            self.r_depth, self.g_depth, self.b_depth = data[40], data[41], data[42]
            self.bit_depth = data[44]
            # RGB 565 to RGB 888
            source = data[64:]
            rgb888 = bytearray(len(source) * 3 // 2)
            for i in range(0, len(source), 2):
                rgb565 = source[i] | (source[i+1] << 8)
                r, g, b = (rgb565 >> 11) & 0x1F, (rgb565 >> 5) & 0x3F, rgb565 & 0x1F
                rgb888[i*3//2:i*3//2+3] = (r << 3, g << 2, b << 3)
            self.image = bytes(rgb888)

    def save(self, filename: str = None):
        img_data = bytearray().join(struct.pack('<H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)) for i in range(0, len(self.image), 3) for r, g, b in [self.image[i:i+3]])
        self.size_uncompressed = self.size_compressed = len(img_data)
        flags = (self.transparent | (self.high << 2) | (self.indexed << 3) | (self.zlib << 4) | (self.etrle << 5))
        header = (
            b'STCI' +
            struct.pack('<II', self.size_uncompressed, self.size_compressed) +
            b'\x00' * 4 +
            struct.pack('<IHHIII', flags, self.height, self.width, self.num_colors, self.g_mask, self.b_mask) +
            b'\x00' * 4 +
            struct.pack('<BBBBB', self.r_depth, self.g_depth, self.b_depth, 0, self.bit_depth) +
            b'\x00' * 19
        )
        
        data = header + img_data
        
        if filename is None:
            return data
        else:
            with open(filename, 'wb') as f:
                f.write(data)
            
    def __str__(self):
        flags = []
        if self.transparent: flags.append("Transparent")
        if self.high: flags.append("High Color")
        if self.indexed: flags.append("Indexed")
        if self.zlib: flags.append("ZLIB")
        if self.etrle: flags.append("ETRLE")
        flags_str = "\n\t".join(flags) if flags else "None"
        
        if self.size_compressed == self.size_uncompressed:
            image_size_str = f"Sizes:\n\tCompressed:   {self.size_compressed}\n\tUncompressed: {self.size_uncompressed}"
        else:
            image_size_str = f"Sizes:\n\tCompressed: {self.size_compressed}\n\tUncompressed: {self.size_uncompressed}"
        
        return (
            f"STI16 File Information:\n"
            f"{'='*30}\n"
            f"Image Resolution: {self.width}x{self.height}\n"
            f"Flags:\n\t{flags_str}\n"
            f"{image_size_str}\n\n"
            f"Color Information:\n\tColors: {self.num_colors}\n\tBit Depth: {self.bit_depth} (Mask)\n\t\tR: {self.r_depth}  ({self.r_mask:04X})\n\t\tG: {self.g_depth}  ({self.g_mask:04X})\n\t\tB: {self.b_depth}  ({self.b_mask:04X})\n"
        )
