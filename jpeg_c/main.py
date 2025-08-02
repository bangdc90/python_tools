import zipfile
import sys
import os
import re

def natural_sort_key(s):
    """Hàm hỗ trợ sắp xếp theo thứ tự tự nhiên (natural sorting)
    Ví dụ: ['1.jpg', '10.jpg', '2.jpg'] -> ['1.jpg', '2.jpg', '10.jpg']
    """
    # Trích xuất các số từ chuỗi và chuyển thành số nguyên để sắp xếp
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

def sanitize_prefix(filename):
    """Lấy prefix từ tên file header, bỏ phần mở rộng"""
    return os.path.splitext(os.path.basename(filename))[0]

def extract_number_from_filename(filename):
    """Trích xuất số từ tên file. Ví dụ: video01.h -> 1, video10.h -> 10"""
    basename = os.path.splitext(os.path.basename(filename))[0]
    # Tìm số cuối cùng trong tên file
    match = re.search(r'(\d+)$', basename)
    if match:
        return int(match.group(1))
    return 0  # Trả về 0 nếu không tìm thấy số

def process_zip_to_jpg_bytes(zip_path, header_path):
    prefix = sanitize_prefix(header_path)  # Ví dụ: "video1"
    video_number = extract_number_from_filename(header_path)  # Trích xuất số từ tên file
    with zipfile.ZipFile(zip_path, 'r') as zipf, open(header_path, 'w') as header:
        frame_idx = 0
        jpg_names = []
        jpg_sizes = []
        
        # Lọc ra các file jpg và sắp xếp theo thứ tự tự nhiên
        jpg_files = [file for file in zipf.namelist() if file.lower().endswith('.jpg')]
        jpg_files.sort(key=natural_sort_key)
        
        for file in jpg_files:
            if file.lower().endswith('.jpg'):
                data = zipf.read(file)
                array_name = f'{prefix}_jpg_frame_{frame_idx}'
                jpg_names.append(array_name)
                jpg_sizes.append(len(data))

                header.write(f'// Frame {frame_idx}: JPG image, size: {len(data)} bytes\n')
                header.write(f'const uint8_t {array_name}[] PROGMEM = {{\n')

                for i, byte in enumerate(data):
                    header.write(f'0x{byte:02X}, ')
                    if (i + 1) % 16 == 0:
                        header.write('\n')
                header.write('\n};\n\n')
                frame_idx += 1

        # Viết danh sách con trỏ đến các frame
        header.write(f'const uint8_t* const {prefix}_frames[] PROGMEM = {{\n')
        for name in jpg_names:
            header.write(f'  {name},\n')
        header.write('};\n\n')

        # Viết danh sách kích thước frame
        header.write(f'const uint16_t {prefix}_frame_sizes[] PROGMEM = {{\n')
        for size in jpg_sizes:
            header.write(f'  {size},\n')
        header.write('};\n\n')

        # Tổng số frame
        header.write(f'const uint16_t {prefix}_NUM_FRAMES = {len(jpg_names)};\n\n')

        # Gán vào struct VideoInfor
        header.write(f'VideoInfo {prefix} = {{\n')
        header.write(f'    {prefix}_frames,\n')
        header.write(f'    {prefix}_frame_sizes,\n')
        header.write(f'    {prefix}_NUM_FRAMES,\n')
        header.write(f'    {video_number}\n')
        header.write(f'}};\n')

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Cách dùng: python jpg_zip_to_c_array.py <zip_file> <output_header.h>")
    else:
        process_zip_to_jpg_bytes(sys.argv[1], sys.argv[2])
