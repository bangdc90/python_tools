import cv2
import os
import sys

def cut_video_grid(input_path, output_dir, rows, cols):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("Cannot open video file.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cell_w = width // cols
    cell_h = height // rows

    os.makedirs(output_dir, exist_ok=True)
    writers = []
    for r in range(rows):
        for c in range(cols):
            out_path = os.path.join(output_dir, f"cell_{r}_{c}.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(out_path, fourcc, fps, (cell_w, cell_h))
            writers.append(writer)

    for frame_idx in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break
        idx = 0
        for r in range(rows):
            for c in range(cols):
                x1 = c * cell_w
                y1 = r * cell_h
                cell = frame[y1:y1+cell_h, x1:x1+cell_w]
                writers[idx].write(cell)
                idx += 1

    cap.release()
    for writer in writers:
        writer.release()
    print("Done cutting video.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Cách dùng: python main.py <đường_dẫn_video> <folder_output>")
    else:
        input_video = sys.argv[1]
        output_folder = sys.argv[2]
        cut_video_grid(input_video, output_folder, rows=5, cols=2)