"""Gera og-image.png 1200x630 para o Descentralize. Estilo minimalista preto + laranja."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 1200, 630
BG = (10, 10, 10)
ACCENT = (255, 153, 0)
TEXT = (232, 232, 232)
DIM = (153, 153, 153)
BORDER = (42, 42, 42)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# Fontes — usa Consolas (Windows) com fallback Courier
def load(size):
    for path in [
        "C:/Windows/Fonts/consolab.ttf",   # Consolas Bold
        "C:/Windows/Fonts/consola.ttf",    # Consolas Regular
        "C:/Windows/Fonts/courbd.ttf",     # Courier New Bold
    ]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

f_big = load(140)        # Título principal
f_sub = load(40)          # Subtítulo
f_small = load(26)        # Chrome / metadados
f_tag = load(22)          # Pequenos detalhes

# Cantos: linha superior fina (border-hot)
d.line([(80, 80), (W - 80, 80)], fill=ACCENT, width=2)
d.line([(80, H - 80), (W - 80, H - 80)], fill=ACCENT, width=2)

# Top-left chrome: "[ descentralize.com.br ]"
chrome_top = "[ descentralize.com.br ]"
d.text((80, 105), chrome_top, font=f_small, fill=DIM)

# Top-right: status indicator
d.text((W - 80, 105), "● online", font=f_small, fill=ACCENT, anchor="ra")

# Centro: nome + subtítulo
title = "descentralize"
tw = d.textlength(title, font=f_big)
title_x = (W - tw) // 2
title_y = 220
d.text((title_x, title_y), title, font=f_big, fill=ACCENT)

# Underscore cursor pulse (estilo terminal)
underscore = "_"
uw = d.textlength(underscore, font=f_big)
d.text((title_x + tw + 4, title_y), underscore, font=f_big, fill=TEXT)

# Subtitle
sub = "> DeFi & cripto em português"
sw = d.textlength(sub, font=f_sub)
d.text(((W - sw) // 2, title_y + 160), sub, font=f_sub, fill=TEXT)

# Tags / categorias
tags = "bitcoin · ethereum · defi · segurança · regulação"
tw2 = d.textlength(tags, font=f_tag)
d.text(((W - tw2) // 2, title_y + 215), tags, font=f_tag, fill=DIM)

# Bottom: créditos
d.text((80, H - 60), "@jeffw3b", font=f_small, fill=TEXT)
d.text((W - 80, H - 60), "blog independente", font=f_small, fill=DIM, anchor="ra")

out = Path(__file__).parent / "og-image.png"
img.save(out, "PNG", optimize=True)
print(f"OK: {out} ({out.stat().st_size // 1024} KB)")
