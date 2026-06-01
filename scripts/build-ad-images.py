#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

BG = (10, 22, 40)
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'landing' / 'assets' / '.hero-capture.png'
OUT = ROOT / 'landing' / 'assets'


def compose(out_w: int, out_h: int, path: Path) -> None:
    hero = Image.open(SRC).convert('RGB')
    canvas = Image.new('RGB', (out_w, out_h), BG)
    margin = int(min(out_w, out_h) * 0.06)
    max_h = out_h - 2 * margin
    max_w = out_w - 2 * margin
    r = hero.width / hero.height
    nh = max_h
    nw = int(nh * r)
    if nw > max_w:
        nw = max_w
        nh = int(nw / r)
    im = hero.resize((nw, nh), Image.Resampling.LANCZOS)
    x, y = (out_w - nw) // 2, (out_h - nh) // 2
    canvas.paste(im, (x, y))
    canvas.save(path, 'PNG', optimize=True)
    print(path)


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f'Missing {SRC}. Run: node scripts/capture-ad-hero.mjs')
    compose(1080, 1080, OUT / 'ad-direct-1080x1080.png')
    compose(1080, 607, OUT / 'ad-direct-1080x607.png')
    compose(450, 450, OUT / 'ad-direct-450x450.png')


if __name__ == '__main__':
    main()
