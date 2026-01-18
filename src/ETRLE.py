def etrle_decompress(compressed_image, palette, width=90, height=720):
    ptr = compressed_image
    alpha_mask = bytes(palette[0] + (0,))
    image = bytearray()
    row_width = 0
    current_row_pos = 0
    current_row = 0
    
    while current_row < height and ptr:
        run = ptr[0]
        run_len = run & 0x7F
        ptr = ptr[1:]
        
        if run & 0x80:
            image.extend(alpha_mask * run_len)
            current_row_pos += run_len
        else:
            for _ in range(run_len):
                if not ptr:
                    break
                idx = ptr[0]
                ptr = ptr[1:]
                image.extend(palette[idx] + (255,))
                current_row_pos += 1 
                
        if current_row_pos >= width:
            current_row += 1
            current_row_pos = 0    
            
    return image  

def etrle_compress(image, palette, width=640, height=480, sub_width=90):
    compressed = bytearray()
    pixel_idx = 0
    col = 0
    while pixel_idx < len(image):
    
        if image[pixel_idx + 3] == 0:
            count = 0
            temp_idx = pixel_idx
            while temp_idx < len(image) and image[temp_idx + 3] == 0:
                count += 1
                temp_idx += 4
                
            while count > 0:
                run_len = min(count, sub_width - col)
                compressed.append(0x80 | run_len)
                col += run_len
                count -= run_len
                if col >= sub_width:
                    compressed.append(0x00)
                    col = 0

            pixel_idx = temp_idx
        else:
            literal_count = 0
            temp_idx = pixel_idx
            while (temp_idx < len(image) and 
                image[temp_idx + 3] != 0 and
                literal_count < (sub_width - col)):
                literal_count += 1
                temp_idx += 4

            compressed.append(literal_count)
            col += literal_count

            temp_idx = pixel_idx
            for j in range(literal_count):
                r, g, b = image[temp_idx:temp_idx+3]
                best_idx = 0
                best_dist = float('inf')
                for idx, (pr, pg, pb) in enumerate(palette):
                    dist = (r - pr)**2 + (g - pg)**2 + (b - pb)**2
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = idx
                compressed.append(best_idx)
                temp_idx += 4

            pixel_idx = temp_idx
            if col >= sub_width:
                compressed.append(0x00)
                col = 0

    if col > 0:
        compressed.append(0x00)

    return compressed 
