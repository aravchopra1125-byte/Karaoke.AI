from faster_whisper import WhisperModel
import os
import torch
from tkinter import Tk, filedialog

def transcribe_to_lrc(audio_file, model_size="small"):
    # Auto-detect device (GPU if available, else CPU)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n⚡ Using device: {device.upper()}")

    # Load Whisper model
    model = WhisperModel(model_size, device=device)

    # Transcribe the audio file
    segments, info = model.transcribe(audio_file)

    # Generate output .lrc filename (same as input, just different extension)
    base_name = os.path.splitext(audio_file)[0]
    lrc_file = base_name + ".lrc"

    # Write LRC file
    with open(lrc_file, "w", encoding="utf-8") as f:
        for segment in segments:
            minutes = int(segment.start // 60)
            seconds = int(segment.start % 60)
            centiseconds = int((segment.start * 100) % 100)
            timestamp = f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]"
            f.write(f"{timestamp}{segment.text.strip()}\n")

    print("\n✅ Transcription completed!")
    print(f"🎵 Detected language: {info.language}")
    print(f"🕒 Audio duration: {info.duration:.2f} seconds")
    print(f"📂 LRC file saved as: {lrc_file}")


if __name__ == "__main__":
    # Open file chooser dialog
    Tk().withdraw()  # hide root window
    audio_file = filedialog.askopenfilename(
        title="Select an audio file",
        filetypes=[("Audio Files", "*.mp3 *.m4a *.wav *.flac *.ogg")]
    )

    if not audio_file:
        print("❌ No file selected. Exiting...")
    else:
        transcribe_to_lrc(audio_file)
