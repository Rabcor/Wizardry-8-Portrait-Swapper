import os
import sys
import struct

class PATCH():
    def __init__(self, source: str | bytes | None = None):   
        # Header Init
        self.content = {}
        self.path = '' 			# This is not actually important.
        self.dataptr = 'Data\\' # This is important though.
        self.num_files = 0
        self.unknown = 33619967 #0200ffff LE, No idea what this is
        self.unknown2 = 1 		# No idea what this is
        self.footer = {}
        
        if source is not None:
            data = source if isinstance(source, bytes) else open(source, 'rb').read()
            self.path = data[:80].decode('ascii', errors='ignore').strip('\x00')
            self.num_files, self.num_files, self.unknown, self.unknown2 = struct.unpack_from("<IIII", data, 512)
            self._parse_footer(data)
            for entry in self.footer:
                self.content[entry['path']] = data[entry['offset']:entry['offset']+entry['size']]

    def _parse_footer(self, data):
        entry_bytes = []
        entry_size = 280
        
        for i in range(self.num_files):
            start_idx = len(data) - (self.num_files - i) * entry_size
            entry_bytes.append(data[start_idx:start_idx + entry_size])
        parsed_entries = []
        for entry in entry_bytes:
            path_end = entry.find(b'\x00')
            if path_end == -1:
                path = entry[:256].decode('utf-8', errors='ignore')
            else:
                path = entry[:path_end].decode('utf-8', errors='ignore')
            offset = int.from_bytes(entry[256:260], byteorder='little')
            size = int.from_bytes(entry[260:264], byteorder='little')
            
            parsed_entries.append({
                'path': path,
                'offset': offset,
                'size': size
            })
        
        self.footer = parsed_entries

    def _update_footer(self):
        self.footer = {}
        current_offset = 532
        for path, data in sorted(self.content.items()):
            self.footer[path] = { 
                'offset': current_offset,
                'size': len(data)
                }
            current_offset += len(data)
    
    def save(self, output_file=None):
               
        self.num_files = len(self.content)
        
        header = bytearray()
        
        header.extend(self.path.encode('ascii', errors='ignore')[:256])
        header.extend(b'\x00' * (256 - len(self.path)))

        header.extend(self.dataptr.encode('ascii', errors='ignore')[:256])
        header.extend(b'\x00' * (256 - len(self.dataptr)))

        header.extend(struct.pack("<I", self.num_files))
        header.extend(struct.pack("<I", self.num_files))

        header.extend(struct.pack("<I", self.unknown))
        header.extend(struct.pack("<I", self.unknown2))

        header.extend(b'\x00\x00\x00\x00')
        if len(header) != 532: raise ValueError("Header must be 532 bytes.")

        content_bytes = bytearray()
        for path, data in sorted(self.content.items()):
            content_bytes.extend(data)

        self._update_footer()
        footer_bytes = bytearray()
        for path in self.footer:
            entry = self.footer[path]
            path_bytes = path.encode('utf-8', errors='ignore')
            path_len = len(path_bytes)
            footer_bytes.extend(path_bytes)
            footer_bytes.extend(b'\x00' * (256 - path_len))
            footer_bytes.extend(struct.pack("<I", entry['offset']))
            footer_bytes.extend(struct.pack("<I", entry['size']))
            footer_bytes.extend(b'\x00' * 16) # Zero padding

        all_bytes = header + content_bytes + footer_bytes

        if output_file is None:
            output_file = self.path
         
        if len(self.content.keys()) == 0:
            try:
                if os.path.exists(output_file):
                    os.remove(output_file)
                    return ("Empty!", "Empty patch file deleted, defaults restored!")
                return ("Information", "Nothing to save.")
            except Exception as e:
                return ("Error!", f"Failed to delete empty file: {str(e)}")
                    
        with open(output_file, 'wb') as f:
            f.write(all_bytes)
        return ("Success!", "Patch saved successfully!")


    def __str__(self):
        footer_str = "\n".join([f"\tPath: {entry['path']}, Offset: {entry['offset']}, Size: {entry['size']}" for entry in self.footer])
        return (
            f"Path: {self.path}\n"
            f"Data Pointer: {self.dataptr}\n"
            f"File Count: {self.num_files}\n"
            f"Unkown: {self.unknown}\n"
            f"Unkown: {self.unknown2}\n"
            f"Footer: \n{footer_str}\n"
        )
