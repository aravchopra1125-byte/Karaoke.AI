from faster_whisper import WhisperModel

# Load the model
model_size = "small"
model = WhisperModel(model_size, device="cpu")  # keep CPU

# Path to your audio file
audio_file = r"C:\Users\manik\DEVJAMS_25\01 Counting Stars.m4a"

# Transcribe with word-level timestamps
segments, info = model.transcribe(audio_file, word_timestamps=True)

# Prepare .lrc file
lrc_filename = "01 Counting Stars.lrc"

def format_timestamp(seconds):
    """Convert seconds to [mm:ss.xx] format for LRC."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    hundredths = int((seconds - int(seconds)) * 100)
    return f"[{minutes:02}:{secs:02}.{hundredths:02}]"

with open(lrc_filename, "w", encoding="utf-8") as f:
    # Optionally add metadata
    f.write(f"[ar:Unknown Artist]\n")
    f.write(f"[ti:Counting Stars]\n")
    f.write(f"[al:Unknown Album]\n")
    f.write(f"[length:{int(info.duration)}]\n\n")

    # Write each word with its timestamp
    for segment in segments:
        for word_info in segment.words:
            timestamp = format_timestamp(word_info.start)
            f.write(f"{timestamp}{word_info.word} ")

        f.write("\n")  # New line after each segment

print(f".lrc file saved as: {lrc_filename}")
