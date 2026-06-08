import os, qrcode
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "poster", "figures")
os.makedirs(OUT, exist_ok=True)
TARGETS = {
    "qr_arxiv": "https://arxiv.org/abs/2506.13595",
    "qr_project": "https://ai-hew-math.github.io/PH3dist/",  # project page (Plan 3)
}
for name, url in TARGETS.items():
    qr = qrcode.QRCode(box_size=12, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url); qr.make(fit=True)
    img = qr.make_image(fill_color="#1A2238", back_color="#FAF7F0")
    img.save(os.path.join(OUT, name + ".png"))
    print("wrote", name, "->", url)
