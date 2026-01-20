class SLF:
    def __init__(self, source: str | bytes | None = None):   
        self.data = bytes()
        self.num_files = 0
        self.files = []
        self.portraits = {}

        if source is not None:
            self.data = source if isinstance(source, bytes) else open(source, 'rb').read()
            self.num_files = int.from_bytes(self.data[512:516], 'little')
            self._parse()
            self._fetch_portraits()

            
            
    def _parse(self):
        header_start = len(self.data) - (self.num_files * 280)
        for i in range(self.num_files):
            offset = header_start + i * 280
            name = self.data[offset:offset+40].decode('ascii', errors='ignore').rstrip('\x00')
            addr = int.from_bytes(self.data[offset+256:offset+260], 'little')
            size = int.from_bytes(self.data[offset+260:offset+264], 'little')
            self.files.append((name, addr, size))

    def _fetch_portraits(self):
        for i in range(1671, 1933):
            path, address, size = self.files[i]
            self.portraits[path] = self.data[address:address+size]
            
    def extract_file(self, index: int, output_path: bool | str | None = False) -> bytes | None:    # Accepts file index, and bool or string, True bool saves as original file-name, string is manual save path.
        if index < 0 or index >= len(self.files):
            raise IndexError(f"File index {index} out of range")        
        name, addr, size = self.files[index]
        file_data = self.data[addr:addr + size]
        
        if isinstance(output_path, bool):
            if output_path:
                output_path = name
                with open(output_path, 'wb') as f:
                    f.write(file_data)
                return None
            else:
                return file_data
        else:
            with open(output_path, 'wb') as f:
                f.write(file_data)
            return None
