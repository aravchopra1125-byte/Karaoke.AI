import librosa
import numpy as np
import json
from pydub import AudioSegment

# Use the FFmpeg executables from the same folder as the script
AudioSegment.converter = r"ffmpeg.exe"
AudioSegment.ffprobe  = r"ffprobe.exe"

# ====== INPUT FILES ======
audio_m4a = "sample.m4a"   # Your M4A file in the same folder as this script
audio_wav = "sample.wav"   # Temporary WAV file for processing

# ====== CONVERT M4A → WAV ======
audio = AudioSegment.from_file(audio_m4a, format="m4a")
audio.export(audio_wav, format="wav")

# ====== CONFIG ======
duration_sec = 23          # Only analyze first 23 seconds
fmin = 80                  # Min frequency for singing
fmax = 1000                # Max frequency for singing
hop_length = 512           # Hop length for analysis
print_every = 20           # Print every N frames
output_json = "pitch_output.json"

# ====== LOAD AUDIO ======
y, sr = librosa.load(audio_wav, sr=None, duration=duration_sec)
print(f"Audio loaded: {librosa.get_duration(y=y, sr=sr):.2f}s, sample rate {sr}")

# ====== PITCH DETECTION ======
pitches = librosa.yin(y, fmin=fmin, fmax=fmax, sr=sr, hop_length=hop_length)

# ====== HELPER: FREQUENCY → NOTE + CENTS ======
def freq_to_note(freq):
    if freq <= 0 or np.isnan(freq):
        return None, None
    note_number = librosa.hz_to_midi(freq)
    note_name = librosa.midi_to_note(int(round(note_number)))
    cents_off = (note_number - round(note_number)) * 100
    return note_name, cents_off


# ====== PROCESS & SAVE RESULTS ======
results = []

for i, freq in enumerate(pitches):
    time_sec = i * hop_length / sr
    note_name, cents = freq_to_note(freq)
    data = {
        "time": round(time_sec, 2),
        "freq": round(float(freq), 1),
        "note": note_name,
        "cents": round(float(cents), 1) if cents is not None else None
    }
    results.append(data)

# ====== SAVE RESULTS TO JSON ======
with open(output_json, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Pitch detection complete. Results saved to {output_json}")


