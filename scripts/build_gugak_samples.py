"""Build gugak note-sample sets for the in-browser player from the National Gugak Center
Digitaleum (KOGL Type-1).  For each wind/string instrument, download the basic-scale
recording(s), segment by onset, estimate each note's pitch, and write per-pitch samples to
assets/<inst>_samples/<inst>_<midi>.wav, copy them to web/audio/<inst>/, and write the
manifest web/audio/instruments.json (instrument -> available MIDIs).  Geomungo is mirrored
from the existing assets/geomungo_samples/geo_*.wav (already validated).

Scale-recording IDs (Digitaleum monotone, "기본음계", loud/plain take):
  geomungo 2589+2595 (대현/유현 강) · gayageum 2538 · daegeum 2557 · piri(향피리) 2505 · haegeum 2482
Source: https://www.gugak.go.kr/digitaleum/  — KOGL Type-1.  Requires librosa, soundfile, internet.
"""
import os, json, time, glob, shutil, urllib.request, http.cookiejar
import numpy as np, soundfile as sf, librosa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = "https://www.gugak.go.kr/digitaleum"
WEB = os.path.join(ROOT, "web", "audio")

NEW = {  # instruments to download + segment (pyin range + sane MIDI window to reject octave errors)
    # sustained=True for blown/bowed tones (no natural decay) -> the player gates them to note length.
    "gayageum": dict(label="가야금 Gayageum", seqs=[2538], fmin="C2", fmax="C6", lo=36, hi=78, sustained=False),
    "daegeum":  dict(label="대금 Daegeum",    seqs=[2557], fmin="A3", fmax="C7", lo=60, hi=96, sustained=True),
    "piri":     dict(label="피리 Piri",       seqs=[2505], fmin="G3", fmax="C7", lo=55, hi=92, sustained=True),
    "haegeum":  dict(label="해금 Haegeum",    seqs=[2482], fmin="C3", fmax="C7", lo=50, hi=96, sustained=True),
}

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def _get(url, tries=15):
    last = None
    for _ in range(tries):
        try:
            return op.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read()
        except Exception as e:
            last = e; time.sleep(0.5)
    raise last

try: _get(B + "/front/monotone/list.do")          # establish a session
except Exception: pass

manifest = {}

# --- geomungo: mirror the already-validated samples (uniform naming for the web) ---
geo_src = os.path.join(ROOT, "assets", "geomungo_samples")
geo_web = os.path.join(WEB, "geomungo"); os.makedirs(geo_web, exist_ok=True)
for old in glob.glob(os.path.join(geo_web, "geo_*.wav")): os.remove(old)  # drop legacy geo_ names
geo_midis = sorted(int(os.path.basename(f)[4:-4]) for f in glob.glob(os.path.join(geo_src, "geo_*.wav")))
for m in geo_midis:
    shutil.copyfile(os.path.join(geo_src, f"geo_{m}.wav"), os.path.join(geo_web, f"geomungo_{m}.wav"))
manifest["geomungo"] = dict(label="거문고 Geomungo", midis=geo_midis, sustained=False)
print(f"geomungo: {len(geo_midis)} samples (mirrored)  midis={geo_midis}")

# --- the 4 new instruments: download + segment ---
for name, cfg in NEW.items():
    outdir = os.path.join(ROOT, "assets", f"{name}_samples"); os.makedirs(outdir, exist_ok=True)
    found = {}
    for seq in cfg["seqs"]:
        mp3 = os.path.join(outdir, f"_scale_{seq}.mp3")
        with open(mp3, "wb") as f: f.write(_get(f"{B}/front/preSound/monotone/play.do?mntn_seq={seq}"))
        y, sr = librosa.load(mp3, sr=44100, mono=True)
        onsets = list(librosa.onset.onset_detect(y=y, sr=sr, backtrack=True, units="samples")) + [len(y)]
        for i in range(len(onsets) - 1):
            seg = y[onsets[i]:onsets[i + 1]]
            if len(seg) < sr * 0.18: continue
            seg = seg[:int(sr * 2.2)]                               # cap length (web-friendly; player only uses note_dur+ring)
            if float(np.max(np.abs(seg))) < 0.04: continue          # skip near-silent gaps
            f0, _, _ = librosa.pyin(seg, fmin=librosa.note_to_hz(cfg["fmin"]), fmax=librosa.note_to_hz(cfg["fmax"]), sr=sr)
            f0v = f0[~np.isnan(f0)]
            if len(f0v) < 3: continue
            mtrack = librosa.hz_to_midi(f0v)
            if np.percentile(mtrack, 90) - np.percentile(mtrack, 10) > 1.2: continue   # reject unstable / 2-pitch segments
            midi = int(round(np.median(mtrack)))
            if not (cfg["lo"] <= midi <= cfg["hi"]): continue
            if (midi not in found) or len(seg) > found[midi]:
                sf.write(os.path.join(outdir, f"{name}_{midi}.wav"), seg.astype(np.float32), 44100, subtype="PCM_16")
                found[midi] = len(seg)
        os.remove(mp3)
    midis = sorted(found)
    webdir = os.path.join(WEB, name); os.makedirs(webdir, exist_ok=True)
    for old in glob.glob(os.path.join(webdir, "*.wav")): os.remove(old)
    for m in midis:
        shutil.copyfile(os.path.join(outdir, f"{name}_{m}.wav"), os.path.join(webdir, f"{name}_{m}.wav"))
    manifest[name] = dict(label=cfg["label"], midis=midis, sustained=cfg["sustained"])
    print(f"{name}: {len(midis)} samples  midis={midis}")

json.dump(manifest, open(os.path.join(WEB, "instruments.json"), "w"), ensure_ascii=False)
print("manifest -> web/audio/instruments.json")
