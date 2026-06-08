"""Rebuild the geomungo note samples from the National Gugak Center Digitaleum.

Downloads the 정악거문고 (instrCd 19988) loud basic-scale recordings for the 대현/유현
strings, segments them by onset, estimates each note's pitch, and writes per-pitch
samples to assets/geomungo_samples/geo_<midi>.wav.

Source: National Gugak Center, Digitaleum (https://www.gugak.go.kr/digitaleum/) — KOGL Type-1.
Requires: librosa, soundfile, internet access.
"""
import os, urllib.request, http.cookiejar
import numpy as np, soundfile as sf, librosa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "geomungo_samples")
os.makedirs(OUT, exist_ok=True)
B = "https://www.gugak.go.kr/digitaleum"
SCALES = [2589, 2595]  # 대현(daehyeon) 강, 유현(yuhyeon) 강 — loud basic scales

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return op.open(req, timeout=45).read()

_get(B + "/front/monotone/list.do")  # establish a session
for seq in SCALES:
    mp3 = os.path.join(OUT, f"_scale_{seq}.mp3")
    with open(mp3, "wb") as f:
        f.write(_get(f"{B}/front/preSound/monotone/play.do?mntn_seq={seq}"))
    y, sr = librosa.load(mp3, sr=44100, mono=True)
    onsets = list(librosa.onset.onset_detect(y=y, sr=sr, backtrack=True, units="samples")) + [len(y)]
    for i in range(len(onsets) - 1):
        seg = y[onsets[i]:onsets[i + 1]]
        if len(seg) < sr * 0.15:
            continue
        f0, _, _ = librosa.pyin(seg, fmin=librosa.note_to_hz("C2"),
                                fmax=librosa.note_to_hz("C5"), sr=sr)
        f0v = f0[~np.isnan(f0)]
        if len(f0v) < 3:
            continue
        midi = int(round(librosa.hz_to_midi(np.median(f0v))))
        path = os.path.join(OUT, f"geo_{midi}.wav")
        if (not os.path.exists(path)) or len(seg) > len(sf.read(path)[0]):
            sf.write(path, seg.astype(np.float32), 44100, subtype="PCM_16")
    os.remove(mp3)
print("geomungo samples ->", OUT)
