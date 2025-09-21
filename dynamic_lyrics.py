import tkinter as tk
import time
import pygame
import re
import os
from pydub import AudioSegment

# -------- CONFIGURATION --------
AUDIO_FILE = r"C:\Users\manik\DEVJAMS_25\01 Counting Stars.m4a"
LRC_FILE =  r"C:\Users\manik\DEVJAMS_25\01 Counting Stars.lrc"
TREBLE_CLEF = "🎼"
FFMPEG_PATH = r".\ffmpeg.exe"

# -------- READ LRC FILE --------
word_list = []
line_list = []
current_line = []
timestamp_pattern = re.compile(r'\[(\d+):(\d+\.\d+)\](.*)')

with open(LRC_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        match = timestamp_pattern.match(line)
        if match:
            mins, secs, word = match.groups()
            timestamp = int(mins) * 60 + float(secs)
            word_list.append((timestamp, word))
            current_line.append((timestamp, word))
            if word.endswith(('.', '!', '?')):
                line_list.append(current_line)
                current_line = []
if current_line:
    line_list.append(current_line)

# -------- CONVERT M4A TO WAV --------
ext = os.path.splitext(AUDIO_FILE)[1].lower()
if ext == ".m4a":
    AudioSegment.converter = FFMPEG_PATH
    song = AudioSegment.from_file(AUDIO_FILE, format="m4a")
    temp_file = "temp_song.wav"
    song.export(temp_file, format="wav")
    AUDIO_FILE = temp_file

# -------- GUI SETUP --------
root = tk.Tk()
root.title("Karaoke Lyrics Player")
root.geometry("1000x400")
root.configure(bg="black")

canvas = tk.Canvas(root, bg="black", height=400)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(fill="both", expand=True)

font_name = "Helvetica"
font_size = 32
line_spacing = 60
canvas_font = (font_name, font_size, "bold")

# -------- AUDIO SETUP --------
pygame.mixer.init()
pygame.mixer.music.load(AUDIO_FILE)

# -------- PLAYBACK & SYNC FUNCTION --------
def play_song():
    pygame.mixer.music.play()
    start_time = time.time()
    current_word_index = 0
    current_line_index = 0

    while pygame.mixer.music.get_busy():
        now = time.time() - start_time

        canvas.delete("all")

        # Instrumental after all words
        if current_word_index >= len(word_list):
            canvas.create_text(500, 200, text=TREBLE_CLEF, fill="yellow", font=(font_name, 72))
            canvas.configure(scrollregion=canvas.bbox("all"))
            root.update()
            time.sleep(0.01)
            continue

        # Move to next word
        if now >= word_list[current_word_index][0]:
            # Determine current line
            while current_line_index < len(line_list) and word_list[current_word_index] not in line_list[current_line_index]:
                current_line_index += 1
            if current_line_index >= len(line_list):
                break

            # Draw multiple lines
            visible_lines = 5  # lines around current line
            start_line = max(0, current_line_index - visible_lines//2)
            y_pos = 50
            for idx in range(start_line, len(line_list)):
                line_words = line_list[idx]
                x = 50
                for i, (ts, w) in enumerate(line_words):
                    color = "white"
                    if idx == current_line_index and ts == word_list[current_word_index][0]:
                        # Highlight current word
                        # Progressive highlight
                        next_ts = line_words[i+1][0] if i+1 < len(line_words) else word_list[current_word_index][0]+0.5
                        progress = min(max((now - ts)/(next_ts - ts), 0), 1)
                        canvas.create_rectangle(x, y_pos-30, x+canvas.bbox(canvas.create_text(0,0,text=w+" ", font=canvas_font))[2]*progress, y_pos+10, fill="yellow", outline="")
                        color = "white"
                    canvas.create_text(x, y_pos, text=w+" ", font=canvas_font, fill=color, anchor="w")
                    x += canvas.bbox(canvas.create_text(0,0,text=w+" ", font=canvas_font))[2]
                y_pos += line_spacing
                if y_pos > 400:  # only draw visible canvas
                    break

            current_word_index += 1

        # Instrumental gap between words
        elif current_word_index < len(word_list):
            next_ts = word_list[current_word_index][0]
            prev_ts = word_list[current_word_index - 1][0] if current_word_index > 0 else 0
            if now < next_ts and now > prev_ts:
                canvas.create_text(500, 200, text=TREBLE_CLEF, fill="yellow", font=(font_name, 72))

        canvas.configure(scrollregion=canvas.bbox("all"))
        root.update()
        time.sleep(0.01)

# -------- START BUTTON --------
start_btn = tk.Button(root, text="Play Song", command=play_song, font=(font_name, 20))
start_btn.pack()

root.mainloop()
