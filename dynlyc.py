import tkinter as tk
import time
import pygame
import re
import os
import ffmpeg  # ffmpeg-python

# -------- CONFIG --------
AUDIO_FILE = r"/Users/hardikchona/lyrics_env/venv/cs.m4a"
LRC_FILE = r"/Users/hardikchona/lyrics_env/venv/cs.lrc"
TEMP_FILE = "temp_song.wav"

# -------- READ LRC FILE --------
word_list = []
timestamp_pattern = re.compile(r'\[(\d+):(\d+\.\d+)\](.*)')

with open(LRC_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        match = timestamp_pattern.match(line)
        if match:
            mins, secs, word = match.groups()
            timestamp = int(mins)*60 + float(secs)
            # Clean the word text - remove any remaining timestamp artifacts
            word = re.sub(r'\[\d+:\d+\.\d+\]', '', word).strip()
            if word:  # Only add non-empty words
                word_list.append((timestamp, word))

# -------- CONVERT M4A TO WAV --------
ext = os.path.splitext(AUDIO_FILE)[1].lower()
if ext == ".m4a":
    try:
        ffmpeg.input(AUDIO_FILE).output(TEMP_FILE).run(overwrite_output=True, quiet=True)
        AUDIO_FILE = TEMP_FILE
    except ffmpeg.Error as e:
        print("Error converting audio:", e.stderr.decode())
        exit(1)

# -------- GUI SETUP --------
root = tk.Tk()
root.title("Karaoke Lyrics Player")
root.geometry("1200x800")
root.configure(bg="black")

# Create main frame for better layout
main_frame = tk.Frame(root, bg="black")
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Canvas for lyrics display
canvas = tk.Canvas(main_frame, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Font settings
font_name = "Helvetica"
font_size = 32
line_height = 80  # Height for each line
canvas_font = (font_name, font_size, "bold")

# -------- AUDIO SETUP --------
pygame.mixer.init()
pygame.mixer.music.load(AUDIO_FILE)

# -------- PLAYBACK & SYNC --------
def find_current_word_index(current_time):
    """Find the current word index based on timestamp - highlights word as it's being sung"""
    current_word_index = -1  # Start with no word highlighted
    for i, (timestamp, word) in enumerate(word_list):
        if current_time >= timestamp:
            current_word_index = i
        else:
            break
    return current_word_index

def smooth_scroll_animation(target_offset, current_offset, speed=0.15):
    """Smooth scrolling animation"""
    diff = target_offset - current_offset
    if abs(diff) > 2:
        return current_offset + (diff * speed)
    return target_offset

# Global variable for pause/resume functionality
is_paused = False
pause_start_time = 0
total_pause_duration = 0

def play_song():
    global is_paused, pause_start_time, total_pause_duration
    
    # Reset pause state
    is_paused = False
    total_pause_duration = 0
    update_pause_button()
    
    pygame.mixer.music.play()
    start_time = time.time()
    scroll_offset = 0
    target_scroll_offset = 0
    
    while pygame.mixer.music.get_busy():
        # Handle pause state
        if is_paused:
            time.sleep(0.1)
            root.update()
            continue
            
        # Calculate current time accounting for pauses
        current_time = time.time() - start_time - total_pause_duration
        
        # Find current word - now highlights exactly as singer sings each word
        current_word_index = find_current_word_index(current_time)
        
        # Clear canvas
        canvas.delete("all")
        
        # Calculate which words to display (9 total: 4 past + 1 current + 4 future)
        total_lines = 9
        past_lines = 4
        future_lines = 4
        
        start_word_index = max(0, current_word_index - past_lines)
        end_word_index = min(len(word_list), current_word_index + future_lines + 1)
        
        # Get canvas dimensions
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        # Calculate starting Y position to center the current word
        center_y = canvas_height // 2
        current_line_offset = past_lines * line_height
        start_y = center_y - current_line_offset + scroll_offset
        
        # Draw each word as a separate line
        for i, word_index in enumerate(range(start_word_index, end_word_index)):
            if word_index >= len(word_list):
                break
                
            timestamp, word = word_list[word_index]
            y_position = start_y + (i * line_height)
            
            # Determine color - now follows exact word timing
            if word_index < current_word_index:
                # Words already sung - dimmed
                color = "#555555"  # Dark gray
            elif word_index == current_word_index:
                # Current word being sung RIGHT NOW
                color = "#FFD700"  # Bright gold
            elif word_index == current_word_index + 1:
                # Next word coming up
                color = "#FF6B6B"  # Soft red
            else:
                # Future words - neutral
                color = "#CCCCCC"  # Light gray
            
            # Create text centered horizontally
            canvas.create_text(canvas_width // 2, y_position, text=word, 
                             font=canvas_font, fill=color, anchor="center")
        
        # Smooth scrolling logic - keep current word centered
        ideal_current_word_y = center_y
        actual_current_word_y = start_y + (past_lines * line_height)
        target_scroll_offset = ideal_current_word_y - actual_current_word_y
        
        # Apply smooth scrolling
        scroll_offset = smooth_scroll_animation(target_scroll_offset, scroll_offset)
        
        # Update display
        root.update()
        time.sleep(0.03)  # ~33 FPS for smooth animation
        
        # Check if user closed the window
        try:
            root.winfo_exists()
        except tk.TclError:
            pygame.mixer.music.stop()
            break

def stop_song():
    global is_paused
    is_paused = False
    pygame.mixer.music.stop()
    update_pause_button()

def toggle_pause():
    global is_paused, pause_start_time, total_pause_duration
    
    if is_paused:
        # Resume
        is_paused = False
        total_pause_duration += time.time() - pause_start_time
        pygame.mixer.music.unpause()
    else:
        # Pause
        is_paused = True
        pause_start_time = time.time()
        pygame.mixer.music.pause()
    
    update_pause_button()

def update_pause_button():
    if is_paused:
        pause_btn.config(text="⏵ Resume", bg="#2196F3")
    else:
        pause_btn.config(text="⏸ Pause", bg="#FF9800")

# -------- CONTROL BUTTONS --------
button_frame = tk.Frame(root, bg="black")
button_frame.pack(pady=20)

play_btn = tk.Button(button_frame, text="▶ Play", command=play_song, 
                    font=(font_name, 14), bg="#4CAF50", fg="white", 
                    padx=20, pady=10, relief="raised", bd=2)
play_btn.pack(side="left", padx=5)

pause_btn = tk.Button(button_frame, text="⏸ Pause", command=toggle_pause,
                     font=(font_name, 14), bg="#FF9800", fg="white",
                     padx=20, pady=10, relief="raised", bd=2)
pause_btn.pack(side="left", padx=5)

stop_btn = tk.Button(button_frame, text="⏹ Stop", command=stop_song,
                    font=(font_name, 14), bg="#F44336", fg="white",
                    padx=20, pady=10, relief="raised", bd=2)
stop_btn.pack(side="left", padx=5)

# -------- INSTRUCTIONS --------
info_frame = tk.Frame(root, bg="black")
info_frame.pack(pady=10)

info_label = tk.Label(info_frame, text="🎤 Word-by-word karaoke player - Gold highlights current word", 
                    font=(font_name, 12), bg="black", fg="#CCCCCC")
info_label.pack()

# -------- START APPLICATION --------
root.mainloop()

# Clean up temp file if created
if os.path.exists(TEMP_FILE):
    os.remove(TEMP_FILE)