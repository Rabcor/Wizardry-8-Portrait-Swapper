def etrle_decompress(compressed_image, palette, header):
    ptr = bytearray(compressed_image)
    alpha_mask = bytes(palette[0] + (0,))
    image = bytearray()
    index = 0

    for header_entry in header:
        width = header_entry['width']
        height = header_entry['height']
        
        for row in range(height):
            row_width = 0
            while row_width < width and index < len(ptr):
                run = ptr[index]
                index += 1
                run_len = run & 0x7F

                if run & 0x80:
                    image.extend(alpha_mask * run_len)
                    row_width += run_len
                else:
                    fill_data = bytearray()
                    for _ in range(run_len):
                        if index >= len(ptr):
                            break
                        idx = ptr[index]
                        index += 1
                        fill_data.extend(palette[idx] + (255,))
                    image.extend(fill_data)
                    row_width += run_len

    return bytes(image)

def etrle_compress(image, palette, header):
    palette_lookup = {}
    for idx, (r, g, b) in enumerate(palette):
        palette_lookup[(r, g, b)] = idx
    
    compressed = bytearray()
    
    for header_entry in header:
        width = header_entry['width']
        height = header_entry['height']
        
        pixel_idx = 0
        col = 0
        
        for row in range(height):
            row_width = 0
            while row_width < width and pixel_idx < len(image):
                if image[pixel_idx + 3] == 0:
                    count = 0
                    temp_idx = pixel_idx
                    while temp_idx < len(image) and image[temp_idx + 3] == 0:
                        count += 1
                        temp_idx += 4
                        
                    while count > 0:
                        run_len = min(count, width - col)
                        compressed.append(0x80 | run_len)
                        col += run_len
                        count -= run_len
                        if col >= width:
                            compressed.append(0x00)
                            col = 0

                    pixel_idx = temp_idx
                else:
                    literal_count = 0
                    temp_idx = pixel_idx
                    while (temp_idx < len(image) and 
                        image[temp_idx + 3] != 0 and
                        literal_count < (width - col)):
                        literal_count += 1
                        temp_idx += 4

                    compressed.append(literal_count)
                    col += literal_count

                    temp_idx = pixel_idx
                    for j in range(literal_count):
                        r, g, b = image[temp_idx], image[temp_idx + 1], image[temp_idx + 2]
                        best_idx = palette_lookup.get((r, g, b), 0)
                        compressed.append(best_idx)
                        temp_idx += 4

                    pixel_idx = temp_idx
                    if col >= width:
                        compressed.append(0x00)
                        col = 0

        if col > 0:
            compressed.append(0x00)
            col = 0

    return compressed
