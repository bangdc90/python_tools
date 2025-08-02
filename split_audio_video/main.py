#!/usr/bin/env python3
"""
Chương trình tách video và âm thanh từ file MP4
Sử dụng: python main.py video_input.mp4 video_output_name
"""

import sys
import os
from pathlib import Path

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    print("Lỗi: Thư viện moviepy chưa được cài đặt!")
    print("Vui lòng cài đặt bằng lệnh: pip install moviepy")
    sys.exit(1)


def split_audio_video(input_file, output_name):
    """
    Tách video và âm thanh từ file đầu vào
    
    Args:
        input_file (str): Đường dẫn đến file video đầu vào
        output_name (str): Tên file đầu ra (không có phần mở rộng)
    """
    
    # Kiểm tra file đầu vào có tồn tại không
    if not os.path.exists(input_file):
        print(f"Lỗi: File '{input_file}' không tồn tại!")
        return False
    
    try:
        print(f"Đang xử lý file: {input_file}")
        
        # Tải video clip
        video_clip = VideoFileClip(input_file)
        
        # Tạo tên file đầu ra
        video_output = f"{output_name}.mp4"
        audio_output = f"{output_name}.mp3"
        
        print(f"Đang tách video...")
        # Tách video (không có âm thanh)
        video_only = video_clip.without_audio()
        video_only.write_videofile(
            video_output,
            codec='libx264',
            audio_codec=None,
            verbose=False,
            logger=None
        )
        video_only.close()
        
        print(f"Đang tách âm thanh...")
        # Tách âm thanh
        if video_clip.audio is not None:
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(
                audio_output,
                codec='mp3',
                verbose=False,
                logger=None
            )
            audio_clip.close()
        else:
            print("Cảnh báo: Video không có âm thanh!")
            # Tạo file âm thanh trống
            with open(audio_output, 'w') as f:
                f.write("")
        
        # Đóng video clip
        video_clip.close()
        
        print(f"Hoàn thành!")
        print(f"Video đã được lưu: {video_output}")
        print(f"Âm thanh đã được lưu: {audio_output}")
        
        return True
        
    except Exception as e:
        print(f"Lỗi khi xử lý video: {str(e)}")
        return False


def main():
    """Hàm chính của chương trình"""
    
    # Kiểm tra số lượng tham số
    if len(sys.argv) != 3:
        print("Cách sử dụng: python main.py video_input.mp4 video_output_name")
        print("Ví dụ: python main.py myvideo.mp4 output")
        print("Kết quả sẽ tạo ra: output.mp4 (video) và output.mp3 (âm thanh)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_name = sys.argv[2]
    
    # Kiểm tra phần mở rộng file đầu vào
    if not input_file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
        print("Cảnh báo: File đầu vào có thể không phải là file video hợp lệ")
    
    # Thực hiện tách video và âm thanh
    success = split_audio_video(input_file, output_name)
    
    if success:
        print("\n✅ Tách video và âm thanh thành công!")
    else:
        print("\n❌ Có lỗi xảy ra trong quá trình xử lý!")
        sys.exit(1)


if __name__ == "__main__":
    main()