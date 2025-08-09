#!/usr/bin/env python3
"""
Video to C Array Converter
Chuyển đổi video MP4 thành mảng C của các frame JPG
"""

import os
import sys
import re
import cv2
import tkinter as tk
from tkinter import filedialog, ttk
import threading
import zipfile
import tempfile
import shutil
from pathlib import Path
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    pass  # Sẽ xử lý lỗi này khi cần dùng đến


class VideoToC:
    """Lớp chính xử lý chuyển đổi video sang mảng C"""
    
    def __init__(self, master):
        """Khởi tạo giao diện người dùng"""
        self.master = master
        master.title("Video to C Array Converter")
        master.geometry("600x400")
        master.resizable(True, True)
        
        # Biến lưu trữ các thông số
        self.video_path = tk.StringVar()
        self.output_file = tk.StringVar(value="video01.h")
        self.resolution = tk.StringVar(value="128x128")
        self.fps = tk.StringVar(value="15")
        self.has_audio = tk.BooleanVar(value=True)  # Biến lưu trạng thái có audio hay không
        
        # Chuẩn bị các thành phần giao diện
        self.setup_ui()
        
        # Biến chạy ngầm
        self.running = False
        self.temp_dir = None
    
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        # Tạo frame chính
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File input
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="File Video:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(file_frame, textvariable=self.video_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)
        
        # Cài đặt
        settings_frame = ttk.LabelFrame(main_frame, text="Cài đặt", padding="5")
        settings_frame.pack(fill=tk.X, pady=10)
        
        # Độ phân giải
        ttk.Label(settings_frame, text="Độ phân giải:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        resolution_options = ["128x128", "160x80", "240x240", "320x240", "640x480", "Custom"]
        resolution_combo = ttk.Combobox(settings_frame, textvariable=self.resolution, values=resolution_options, width=15)
        resolution_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        resolution_combo.bind("<<ComboboxSelected>>", self.on_resolution_select)
        
        # FPS
        ttk.Label(settings_frame, text="FPS:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        fps_entry = ttk.Entry(settings_frame, textvariable=self.fps, width=10)
        fps_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Tên file đầu ra
        ttk.Label(settings_frame, text="Tên file đầu ra:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        output_entry = ttk.Entry(settings_frame, textvariable=self.output_file, width=20)
        output_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Checkbox có audio hay không
        audio_check = ttk.Checkbutton(settings_frame, text="Có audio", variable=self.has_audio)
        audio_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(progress_frame, text="Tiến trình:").pack(side=tk.LEFT, padx=5)
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Nút bấm
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_conversion)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        # Khu vực log
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=70, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Không cho phép chỉnh sửa log
        self.log_text.config(state=tk.DISABLED)
    
    def on_resolution_select(self, event):
        """Xử lý khi người dùng chọn độ phân giải"""
        if self.resolution.get() == "Custom":
            # Mở hộp thoại để nhập độ phân giải tùy chỉnh
            custom_dialog = tk.Toplevel(self.master)
            custom_dialog.title("Độ phân giải tùy chỉnh")
            custom_dialog.geometry("300x100")
            custom_dialog.resizable(False, False)
            custom_dialog.transient(self.master)
            custom_dialog.grab_set()
            
            ttk.Label(custom_dialog, text="Nhập độ phân giải (WxH):").pack(pady=5)
            custom_entry = ttk.Entry(custom_dialog, width=20)
            custom_entry.pack(pady=5)
            custom_entry.insert(0, "128x128")
            
            def apply_custom():
                value = custom_entry.get()
                if re.match(r'^\d+x\d+$', value):
                    self.resolution.set(value)
                    custom_dialog.destroy()
                else:
                    tk.messagebox.showerror("Lỗi", "Định dạng không hợp lệ. Vui lòng nhập theo dạng WxH (ví dụ: 128x128)")
            
            ttk.Button(custom_dialog, text="OK", command=apply_custom).pack(pady=5)
            
            # Đặt focus vào ô nhập liệu và chờ người dùng nhập
            custom_entry.focus_set()
            self.master.wait_window(custom_dialog)
    
    def browse_file(self):
        """Mở hộp thoại duyệt file"""
        file_path = filedialog.askopenfilename(
            title="Chọn file video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if file_path:
            self.video_path.set(file_path)
            self.log("Đã chọn file: " + file_path)
    
    def log(self, message):
        """Thêm thông báo vào khu vực log"""
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            # Cập nhật giao diện ngay lập tức
            self.master.update_idletasks()
        except Exception as e:
            print(f"Lỗi khi ghi log: {str(e)}")
    
    def update_progress(self, value):
        """Cập nhật giá trị của progress bar"""
        self.progress["value"] = value
        self.master.update_idletasks()
    
    def natural_sort_key(self, s):
        """Hàm hỗ trợ sắp xếp theo thứ tự tự nhiên (natural sorting)
        Ví dụ: ['1.jpg', '10.jpg', '2.jpg'] -> ['1.jpg', '2.jpg', '10.jpg']
        """
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]
    
    def sanitize_prefix(self, filename):
        """Lấy prefix từ tên file header, bỏ phần mở rộng"""
        return os.path.splitext(os.path.basename(filename))[0]
    
    def extract_number_from_filename(self, filename):
        """Trích xuất số từ tên file. Ví dụ: video01.h -> 1, video10.h -> 10"""
        basename = os.path.splitext(os.path.basename(filename))[0]
        # Tìm số cuối cùng trong tên file
        match = re.search(r'(\d+)$', basename)
        if match:
            return int(match.group(1))
        return 0  # Trả về 0 nếu không tìm thấy số
    
    def jpg_to_c_header(self, jpg_folder, output_file):
        """Chuyển đổi các ảnh JPG trong thư mục thành mảng C trong file header"""
        try:
            self.log("Chuyển đổi JPG thành mảng C...")
            
            # Tạo tên prefix và số video
            prefix = self.sanitize_prefix(output_file)
            video_number = self.extract_number_from_filename(output_file)
            
            # Lấy danh sách tất cả các file JPG trong thư mục
            jpg_files = [f for f in os.listdir(jpg_folder) if f.lower().endswith('.jpg')]
            jpg_files.sort(key=self.natural_sort_key)
            
            total_files = len(jpg_files)
            self.log(f"Tìm thấy {total_files} frame JPG")
        
            with open(output_file, 'w', encoding='utf-8') as header:
                frame_idx = 0
                jpg_names = []
                jpg_sizes = []
                
                # Xử lý từng file JPG
                for i, file in enumerate(jpg_files):
                    file_path = os.path.join(jpg_folder, file)
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    
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
                    
                    # Cập nhật tiến trình
                    progress = 70 + (i / total_files) * 30
                    self.update_progress(progress)
                
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
                
                # Gán vào struct VideoInfo
                header.write(f'VideoInfo {prefix} = {{\n')
                header.write(f'    {prefix}_frames,\n')
                header.write(f'    {prefix}_frame_sizes,\n')
                header.write(f'    {prefix}_NUM_FRAMES,\n')
                
                # Giá trị audio: nếu có audio thì giữ nguyên video_number, nếu không thì để là 0
                if self.has_audio.get():
                    header.write(f'    {video_number}\n')
                else:
                    header.write(f'    0\n')
    
                header.write(f'}};\n')
            
            self.log(f"Đã tạo file header: {output_file}")
            return True
            
        except Exception as e:
            self.log(f"Lỗi khi tạo C header: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return False
            
            # Xử lý từng file JPG
            for i, file in enumerate(jpg_files):
                file_path = os.path.join(jpg_folder, file)
                with open(file_path, 'rb') as f:
                    data = f.read()
                
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
                
                # Cập nhật tiến trình
                progress = 70 + (i / total_files) * 30
                self.update_progress(progress)
            
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
            
            # Gán vào struct VideoInfo
            header.write(f'VideoInfo {prefix} = {{\n')
            header.write(f'    {prefix}_frames,\n')
            header.write(f'    {prefix}_frame_sizes,\n')
            header.write(f'    {prefix}_NUM_FRAMES,\n')
            
            # Giá trị audio: nếu có audio thì giữ nguyên video_number, nếu không thì để là 0
            if self.has_audio.get():
                header.write(f'    {video_number}\n')
            else:
                header.write(f'    0\n')

            header.write(f'}};\n')
            
            # Không cần đóng #endif như cũ, để theo đúng mẫu
            
            self.log(f"Đã tạo file header: {output_file}")
            return True
            
        except Exception as e:
            self.log(f"Lỗi khi tạo C header: {str(e)}")
            return False
        
        self.log(f"Đã tạo file header: {output_file}")
        return True
    
    def extract_frames(self, video_path, output_folder, width, height, target_fps):
        """Trích xuất các frame từ video với độ phân giải và fps đã chọn"""
        self.log(f"Đang trích xuất frame từ video với độ phân giải {width}x{height}, FPS: {target_fps}...")
        
        # Mở video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.log("Lỗi: Không thể mở file video")
            return False
        
        # Lấy thông tin video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Tính toán frame cần trích xuất
        frame_interval = original_fps / target_fps
        
        # Tạo thư mục đầu ra nếu chưa tồn tại
        os.makedirs(output_folder, exist_ok=True)
        
        frame_count = 0
        saved_count = 0
        next_frame_to_save = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Kiểm tra xem frame này có cần lưu không
            if frame_count >= next_frame_to_save:
                # Thay đổi kích thước frame
                resized_frame = cv2.resize(frame, (width, height))
                
                # Lưu frame thành file JPG
                output_path = os.path.join(output_folder, f"frame_{saved_count:04d}.jpg")
                cv2.imwrite(output_path, resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                
                saved_count += 1
                next_frame_to_save += frame_interval
                
                # Cập nhật tiến trình
                progress = (frame_count / total_frames) * 70
                self.update_progress(progress)
            
            frame_count += 1
        
        cap.release()
        self.log(f"Đã trích xuất {saved_count} frame với FPS: {target_fps}")
        return True
    
    def extract_audio(self, video_path, output_name):
        """Trích xuất audio từ file video nếu người dùng tích vào ô có audio"""
        try:
            # Kiểm tra thư viện moviepy đã được cài đặt chưa
            if 'moviepy.editor' not in sys.modules:
                self.log("Đang cài đặt thư viện moviepy...")
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "moviepy"])
                from moviepy.editor import VideoFileClip
                self.log("Đã cài đặt thư viện moviepy thành công")
            else:
                from moviepy.editor import VideoFileClip
            
            self.log(f"Đang trích xuất audio từ video...")
            # Tải video clip
            video_clip = VideoFileClip(video_path)
            
            # Tạo tên file âm thanh đầu ra
            audio_output = f"{output_name}.mp3"
            
            # Trích xuất âm thanh
            if video_clip.audio is not None:
                audio_clip = video_clip.audio
                audio_clip.write_audiofile(
                    audio_output,
                    codec='mp3',
                    verbose=False,
                    logger=None
                )
                audio_clip.close()
                self.log(f"Đã trích xuất audio thành công: {audio_output}")
            else:
                self.log("Cảnh báo: Video không có âm thanh!")
            
            # Đóng video clip
            video_clip.close()
            return True
            
        except Exception as e:
            self.log(f"Lỗi khi trích xuất audio: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return False
    
    def start_conversion(self):
        """Bắt đầu quá trình chuyển đổi video"""
        if self.running:
            return
        
        # Kiểm tra file đầu vào
        video_path = self.video_path.get()
        if not video_path or not os.path.exists(video_path):
            self.log("Lỗi: Vui lòng chọn file video hợp lệ")
            return
        
        # Kiểm tra định dạng độ phân giải
        resolution = self.resolution.get()
        if not re.match(r'^\d+x\d+$', resolution):
            self.log("Lỗi: Định dạng độ phân giải không hợp lệ")
            return
        
        # Kiểm tra FPS
        try:
            fps = float(self.fps.get())
            if fps <= 0:
                raise ValueError("FPS phải lớn hơn 0")
        except ValueError:
            self.log("Lỗi: FPS không hợp lệ")
            return
        
        # Kiểm tra tên file đầu ra
        output_file = self.output_file.get()
        if not output_file:
            self.log("Lỗi: Vui lòng nhập tên file đầu ra")
            return
        
        # Thêm phần mở rộng .h nếu không có
        if not output_file.lower().endswith('.h'):
            output_file += '.h'
            self.output_file.set(output_file)
        
        # Hiển thị thông tin cài đặt
        self.log(f"Bắt đầu chuyển đổi với cài đặt:")
        self.log(f"- Độ phân giải: {resolution}")
        self.log(f"- FPS: {fps}")
        self.log(f"- Có audio: {'Có' if self.has_audio.get() else 'Không'}")
        self.log(f"- File đầu ra: {output_file}")
        
        # Vô hiệu hóa nút Start
        self.start_button.config(state=tk.DISABLED)
        self.running = True
        
        # Reset progress bar
        self.update_progress(0)
        
        # Tạo thư mục tạm để lưu các frame
        self.temp_dir = tempfile.mkdtemp()
        
        # Phân tích độ phân giải
        width, height = map(int, resolution.split('x'))
        
        # Chạy quá trình chuyển đổi trong thread riêng biệt
        threading.Thread(target=self.conversion_thread, args=(video_path, output_file, width, height, fps)).start()
    
    def conversion_thread(self, video_path, output_file, width, height, fps):
        """Thread xử lý quá trình chuyển đổi"""
        try:
            # Trích xuất các frame từ video
            if not self.extract_frames(video_path, self.temp_dir, width, height, fps):
                self.log("Lỗi: Không thể trích xuất frame từ video")
                return
            
            # Chuyển đổi các frame JPG thành mảng C
            if not self.jpg_to_c_header(self.temp_dir, output_file):
                self.log("Lỗi: Không thể chuyển đổi JPG thành mảng C")
                return
            
            # Trích xuất audio nếu người dùng tích vào ô có audio
            if self.has_audio.get():
                # Lấy tên file không có phần mở rộng để đặt tên cho file audio
                output_name = os.path.splitext(output_file)[0]
                if not self.extract_audio(video_path, output_name):
                    self.log("Cảnh báo: Không thể trích xuất audio từ video, nhưng quá trình chuyển đổi vẫn hoàn thành")
            
            self.update_progress(100)
            self.log("Hoàn thành! File đầu ra: " + output_file)
            
        except Exception as e:
            self.log(f"Lỗi: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            # Xóa thư mục tạm
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except Exception as e:
                    self.log(f"Lỗi khi xóa thư mục tạm: {str(e)}")
            
            # Kích hoạt lại nút Start
            self.start_button.config(state=tk.NORMAL)
            self.running = False


def main():
    """Hàm chính của chương trình"""
    root = tk.Tk()
    app = VideoToC(root)
    root.mainloop()


if __name__ == "__main__":
    main()
