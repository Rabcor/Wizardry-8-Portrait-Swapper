class SLF:
    def __init__(self, source: str | bytes | None = None):   
        self.data = bytes()
        self.num_files = 0
        self.files = {}

        if source is not None:
            self.data = source if isinstance(source, bytes) else open(source, 'rb').read()
            self._parse()    
            
    def _parse(self):
        self.num_files = int.from_bytes(self.data[512:516], 'little')
        header_start = len(self.data) - (self.num_files * 280)
        files = {}
        
        for i in range(self.num_files):
            offset = header_start + i * 280
            name = self.data[offset:offset+256].decode('ascii', errors='ignore').rstrip('\x00')
            addr = int.from_bytes(self.data[offset+256:offset+260], 'little')
            size = int.from_bytes(self.data[offset+260:offset+264], 'little')
            files[name] = (addr, size)
        
        self.files = files
            
    def extract(self, filename: str, output_path: str | None = None) -> bytes | None:
        if filename not in self.files:
            raise IndexError(f"File {filename} not found")
        
        addr, size = self.files[filename]
        file_data = self.data[addr:addr + size]
        
        if output_path is not None:
            with open(output_path, 'wb') as f:
                f.write(file_data)
            return None
        else:
            return file_data



