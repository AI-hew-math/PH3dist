"""Render a cycle-sonification (from compose_stream) to audio using REAL geomungo
note samples (segmented from National Gugak Center Digitaleum recordings, KOGL-1)."""
import os, glob, subprocess
import numpy as np
import soundfile as sf
from scipy.signal import resample
from ph_music.compose import compose_stream

SR = 44100

def load_samples(sample_dir):
    samples = {}
    for f in glob.glob(os.path.join(sample_dir, "geo_*.wav")):
        midi = int(os.path.basename(f)[4:-4])
        y, sr = sf.read(f)
        if y.ndim > 1:
            y = y.mean(axis=1)
        if sr != SR:
            y = resample(y, int(len(y) * SR / sr))
        samples[midi] = y.astype(np.float32)
    return samples

def _pitch_shift(y, semitones):
    if semitones == 0:
        return y
    ratio = 2 ** (semitones / 12.0)          # raise pitch -> play faster -> fewer samples
    return resample(y, max(1, int(len(y) / ratio))).astype(np.float32)

def render_wav(res, distance_key, sample_dir, out_wav, tempo_bpm=96):
    samples = load_samples(sample_dir)
    keys = sorted(samples)
    qps = tempo_bpm / 60.0                    # quarter notes per second
    s = compose_stream(res, distance_key, tempo_bpm=tempo_bpm)
    events, t = [], 0.0
    for n in s.notesAndRests:
        dur = float(n.duration.quarterLength) / qps
        if n.isRest:
            t += dur
            continue
        events.append((t, int(round(n.pitch.midi)), dur))
        t += dur
    buf = np.zeros(int((t + 2.5) * SR) + 1, np.float32)
    for t0, midi, dur in events:
        sk = min(keys, key=lambda k: abs(k - midi))
        y = _pitch_shift(samples[sk], midi - sk)
        L = min(len(y), int((dur + 0.6) * SR))   # let the pluck ring past the note
        seg = y[:L].copy()
        fade = min(L, int(0.09 * SR))
        if fade > 0:
            seg[-fade:] *= np.linspace(1.0, 0.0, fade)
        i0 = int(t0 * SR)
        buf[i0:i0 + len(seg)] += seg
    peak = float(np.max(np.abs(buf))) or 1.0
    buf = (buf / peak * 0.92).astype(np.float32)
    sf.write(out_wav, buf, SR, subtype="PCM_16")
    return out_wav

def render_mp3(res, distance_key, sample_dir, out_mp3, tempo_bpm=96):
    wav = out_mp3[:-4] + ".wav"
    render_wav(res, distance_key, sample_dir, wav, tempo_bpm)
    subprocess.run(["ffmpeg", "-y", "-i", wav, "-codec:a", "libmp3lame", "-q:a", "4", out_mp3],
                   check=True, capture_output=True)
    os.remove(wav)
    return out_mp3
