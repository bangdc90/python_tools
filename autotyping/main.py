import tkinter as tk
from tkinter import messagebox
import pyautogui
import pygetwindow as gw
import time
import json
import os
import threading

# Đường dẫn file config
CONFIG_FILE = "config.json"

# Giá trị mặc định
DEFAULT_DELAY = 5  # Số giây delay mặc định
DEFAULT_SPEED = 100  # Tốc độ gõ chữ mặc định (ms)
SKIP_WINDOW_CHECK = False  # Có bỏ qua kiểm tra cửa sổ hay không

# Tải config từ file
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {"delay": DEFAULT_DELAY, "speed": DEFAULT_SPEED, "skip_window_check": SKIP_WINDOW_CHECK}

# Lưu config vào file
def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

# Hàm kiểm tra xem cửa sổ hiện tại có cho phép nhập liệu hay không
def is_editable_window():
    try:
        focused_window = gw.getActiveWindow()
        if focused_window:
            # In ra tiêu đề cửa sổ để kiểm tra
            window_title = focused_window.title
            print(f"Focused window title: {window_title}")
            
            # Kiểm tra các từ khóa phổ biến trong tiêu đề cửa sổ
            editable_keywords = [
                "vscode", "visual studio code", "code", 
                "notepad", "word", "document", "text", 
                ".py", ".txt", ".js", ".html", ".css", ".md",  # Các phần mở rộng file phổ biến
                "editor", "editing"
            ]
            
            window_title_lower = window_title.lower()
            for keyword in editable_keywords:
                if keyword in window_title_lower:
                    return True
                    
            # Luôn cho phép VS Code (kiểm tra thêm quy trình)
            if "code.exe" in window_title_lower or "vscode" in window_title_lower:
                return True
    except Exception as e:
        print(f"Error checking window: {e}")
    return False

# Hàm giả lập gõ chữ
def simulate_typing(content, speed):
    global running
    for char in content:
        if not running:  # Kiểm tra trạng thái để dừng ngay lập tức
            break
        if char == "\n":  # Xử lý xuống dòng
            pyautogui.press("enter")
            time.sleep(1)
            pyautogui.hotkey("shift", "home")
            time.sleep(1)  # Thêm một chút thời gian để tránh lỗi
        elif char == " ":  # Xử lý khoảng trắng
            pyautogui.press("space")
        else:
            pyautogui.typewrite(char)
        time.sleep(speed / 1000.0)  # Chuyển tốc độ từ ms sang giây

# Hàm xử lý khi nhấn nút Start/Stop
def toggle_start_stop():
    global running, typing_thread
    if running:
        running = False
        start_stop_button.config(text="Start")
    else:
        running = True
        start_stop_button.config(text="Stop")
        typing_thread = threading.Thread(target=start_typing)
        typing_thread.start()

def start_typing():
    global running
    try:
        delay = int(delay_entry.get()) if delay_entry.get().strip() else DEFAULT_DELAY
        speed = int(speed_entry.get()) if speed_entry.get().strip() else DEFAULT_SPEED
        skip_check = skip_check_var.get()

        # Lưu config
        save_config({"delay": delay, "speed": speed, "skip_window_check": skip_check})

        # Đợi số giây delay
        time.sleep(delay)
        if not running:  # Kiểm tra trạng thái để dừng ngay lập tức
            return

        # Kiểm tra cửa sổ hiện tại (nếu không bỏ qua kiểm tra)
        if not skip_check and not is_editable_window():
            messagebox.showerror("Error", "Không tìm thấy cửa sổ cho phép nhập liệu!\n\nNếu bạn chắc chắn đây là VS Code hoặc trình soạn thảo khác, hãy đánh dấu 'Bỏ qua kiểm tra cửa sổ'.")
            running = False
            start_stop_button.config(text="Start")
            return

        # Lấy nội dung từ ô text box
        content = text_box.get("1.0", tk.END).strip()
        if not content:
            messagebox.showerror("Error", "Nội dung không được để trống!")
            running = False
            start_stop_button.config(text="Start")
            return

        # Giả lập gõ chữ
        simulate_typing(content, speed)

        messagebox.showinfo("Success", "Đã hoàn thành việc gõ nội dung!")
        running = False
        start_stop_button.config(text="Start")
    except ValueError:
        messagebox.showerror("Error", "Vui lòng nhập giá trị hợp lệ cho delay và tốc độ gõ chữ!")
        running = False
        start_stop_button.config(text="Start")

# Tạo giao diện
root = tk.Tk()
root.title("Auto Typing Tool")

# Biến trạng thái
running = False
typing_thread = None

# Tải config
config = load_config()

# Ô text box lớn để nhập nội dung
text_box_label = tk.Label(root, text="Nội dung:")
text_box_label.pack(pady=5)
text_box = tk.Text(root, width=50, height=10)
text_box.pack(pady=5)

# Ô text nhỏ cho số giây delay
delay_label = tk.Label(root, text="Số giây delay:")
delay_label.pack(pady=5)
delay_entry = tk.Entry(root, width=10)
delay_entry.insert(0, str(config.get("delay", DEFAULT_DELAY)))
delay_entry.pack(pady=5)

# Ô text nhỏ cho tốc độ gõ chữ
speed_label = tk.Label(root, text="Tốc độ gõ chữ (ms):")
speed_label.pack(pady=5)
speed_entry = tk.Entry(root, width=10)
speed_entry.insert(0, str(config.get("speed", DEFAULT_SPEED)))
speed_entry.pack(pady=5)

# Nút Start/Stop
start_stop_button = tk.Button(root, text="Start", command=toggle_start_stop)
start_stop_button.pack(pady=10)

# Checkbox bỏ qua kiểm tra cửa sổ
skip_check_var = tk.BooleanVar()
skip_check_var.set(config.get("skip_window_check", SKIP_WINDOW_CHECK))
skip_check = tk.Checkbutton(root, text="Bỏ qua kiểm tra cửa sổ (Dùng nếu VS Code không được nhận diện)", variable=skip_check_var)
skip_check.pack(pady=5)

# Chạy giao diện
root.mainloop()