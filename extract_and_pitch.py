import os
import json
import numpy as np
import librosa
from pydub import AudioSegment

# --- make sure ffmpeg paths are correct on Windows ---
AudioSegment.converter = r"ffmpeg.exe"
AudioSegment.ffprobe  = r"ffprobe.exe"

# ====== INPUT / CONFIG (tweak these) ======
audio_m4a = "sample.m4a"
audio_wav = "sample.wav"      # temp wav used for processing
duration_sec = 23             # analyze only first N seconds (None for whole file)
fmin = 80                     # min freq to detect (Hz)
fmax = 1000                   # max freq to detect (Hz)
hop_length = 512
print_every = 20
output_json = "pitch_output.json"

# ====== STEP 0: convert m4a -> wav (if not already) ======
if not os.path.exists(audio_wav):
    print("Converting m4a -> wav ...")
    audio = AudioSegment.from_file(audio_m4a, format="m4a")
    audio.export(audio_wav, format="wav")
else:
    print(f"{audio_wav} already exists, skipping convert.")

# ====== STEP 1: Vocal separation (try Spleeter, fallback to HPSS) ======
vocals_path = None
try:
    # Try to import spleeter
    from spleeter.separator import Separator
    print("Spleeter found — separating vocals (2 stems)...")
    separator = Separator('spleeter:2stems')  # vocals + accompaniment
    # Produce output in 'spleeter_output/<trackname>/vocals.wav'
    separator.separate_to_file(audio_wav, 'spleeter_output')
    base = os.path.splitext(os.path.basename(audio_wav))[0]
    vocals_path = os.path.join('spleeter_output', base, 'vocals.wav')
    if not os.path.exists(vocals_path):
        raise FileNotFoundError("Spleeter output vocals.wav not found.")
except Exception as e:
    print("Spleeter unavailable or failed — falling back to librosa HPSS (weaker).")
    # HPSS fallback: isolate harmonic part (contains vocals + harmonic instruments)
    y_full, sr_full = librosa.load(audio_wav, sr=None, mono=True)
    harmonic, percussive = librosa.effects.hpss(y_full)
    try:
        import soundfile as sf
        vocals_path = "vocals_estimate.wav"
        sf.write(vocals_path, harmonic, sr_full)
        print(f"Saved HPSS estimate to {vocals_path}")
    except Exception as e2:
        raise RuntimeError("Cannot write HPSS output. Install soundfile (pip install soundfile).") from e2

# ====== STEP 2: Load extracted vocals (trim to duration if requested) ======
print("Loading vocals for pitch detection:", vocals_path)
y, sr = librosa.load(vocals_path, sr=None, duration=duration_sec, mono=True)
print(f"Loaded {librosa.get_duration(y=y, sr=sr):.2f}s at {sr} Hz")

# ====== STEP 3: Pitch detection with pYIN (librosa.pyin) ======
# pyin returns: f0 (Hz array with NaNs for unvoiced), voiced_flag (bool array), voiced_prob (0..1)
f0, voiced_flag, voiced_prob = librosa.pyin(
    y,
    fmin=fmin,
    fmax=fmax,
    sr=sr,
    hop_length=hop_length
)

# ====== HELPER: freq -> note + cents ======
def freq_to_note(freq):
    if freq is None or np.isnan(freq) or freq <= 0:
        return None, None
    note_number = librosa.hz_to_midi(freq)
    note_name = librosa.midi_to_note(int(round(note_number)))
    cents_off = (note_number - round(note_number)) * 100
    return note_name, cents_off

# ====== STEP 4: collect results and save JSON ======
results = []
for i, freq in enumerate(f0):
    time_sec = round(i * hop_length / sr, 2)
    if np.isnan(freq):
        freq_val = None
        note_name = None
        cents = None
    else:
        freq_val = round(float(freq), 1)
        note_name, cents = freq_to_note(freq)
        if cents is not None:
            cents = round(float(cents), 1)
    row = {
        "time": time_sec,
        "freq": freq_val,
        "note": note_name,
        "cents": cents,
        "voiced": bool(voiced_flag[i]) if voiced_flag is not None else None,
        "voiced_prob": float(voiced_prob[i]) if voiced_prob is not None else None
    }
    results.append(row)
    if (i % print_every) == 0:
        print(f"{time_sec:>6.2f}s: freq={freq_val}Hz note={note_name} voiced_prob={row['voiced_prob']}")

with open(output_json, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Pitch detection complete. Results saved to {output_json}")
