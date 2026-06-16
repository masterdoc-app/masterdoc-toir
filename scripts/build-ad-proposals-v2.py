#!/usr/bin/env python3
"""Fixaverse ad proposals v2 — без баннеров, кнопок и stock-мусора на фото."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "landing" / "assets"
OUT = ASSETS / "ad-proposals-v2"

WHITE = (255, 255, 255)
TEXT = (13, 27, 58)
BLUE = (26, 111, 255)
BLUE_SOFT = (238, 243, 255)
BORDER = (229, 231, 235)
RADIUS = 20


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    )
    return ImageFont.truetype(path, size)


def gradient(w: int, h: int, a: tuple, b: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        row = tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))
        for x in range(w):
            px[x, y] = row
    return img


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return m


def paste_rounded(base: Image.Image, im: Image.Image, xy: tuple[int, int], radius: int = RADIUS) -> None:
    im = im.convert("RGBA")
    base.paste(im, xy, rounded_mask(im.size, radius))


def fit_cover(src: Image.Image, tw: int, th: int) -> Image.Image:
    src = src.convert("RGB")
    r = max(tw / src.width, th / src.height)
    nw, nh = int(src.width * r), int(src.height * r)
    im = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def drop_shadow(card: Image.Image, radius: int = RADIUS, blur: int = 28, offset: int = 10) -> Image.Image:
    w, h = card.size
    pad = blur + offset
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (w, h), (13, 27, 58, 55))
    shadow.putalpha(rounded_mask((w, h), radius))
    layer.paste(shadow, (pad + offset, pad + offset), shadow)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    layer.paste(card.convert("RGBA"), (pad, pad), rounded_mask((w, h), radius))
    return layer


def paste_logo(canvas: Image.Image, xy: tuple[int, int], max_w: int = 220) -> None:
    logo = Image.open(ASSETS / "logo-fixaverse.png").convert("RGBA")
    r = max_w / logo.width
    logo = logo.resize((max_w, int(logo.height * r)), Image.Resampling.LANCZOS)
    canvas.paste(logo, xy, logo)


def save_pair(name: str, square: Image.Image) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sq = OUT / f"{name}-1080x1080.png"
    square.convert("RGB").save(sq, "PNG", optimize=True)
    wide = fit_cover(square, 1080, 607)
    wp = OUT / f"{name}-1080x607.png"
    wide.save(wp, "PNG", optimize=True)
    print(sq)
    print(wp)


def g1_photo_frame() -> None:
    """Техник у щита — без текста и кнопок, только лого."""
    w = h = 1080
    canvas = Image.new("RGB", (w, h), WHITE)
    photo = fit_cover(Image.open(ASSETS / "hero-photo.png"), 920, 920)
    card = drop_shadow(photo, radius=24)
    ox, oy = (w - card.width) // 2, (h - card.height) // 2 + 20
    canvas.paste(card, (ox, oy), card)
    paste_logo(canvas, (56, 48), 200)
    save_pair("g1-photo-frame", canvas)


def g2_product_card() -> None:
    """Скрин продукта в карточке — как блок hero на сайте, на белом."""
    w = h = 1080
    canvas = Image.new("RGB", (w, h), WHITE)
    capture = fit_cover(Image.open(ASSETS / ".hero-capture.png"), 960, 780)
    card = drop_shadow(capture, radius=RADIUS)
    ox = (w - card.width) // 2
    canvas.paste(card, (ox, 140), card)
    paste_logo(canvas, (56, 48), 240)
    save_pair("g2-product-card", canvas)


def g3_copilot_scene() -> None:
    """Техник у станка — светлый фон, крупный кадр."""
    w = h = 1080
    canvas = gradient(w, h, WHITE, BLUE_SOFT)
    photo = fit_cover(Image.open(ASSETS / "hero-cmms.webp"), 1000, 880)
    card = drop_shadow(photo, radius=24)
    ox = (w - card.width) // 2
    canvas.paste(card, (ox, 120), card)
    paste_logo(canvas, (48, 44), 190)
    save_pair("g3-copilot-scene", canvas)


def g4_brand_minimal() -> None:
    """Только бренд — один логотип 1024px, без дубля иконки."""
    w = h = 1080
    canvas = gradient(w, h, BLUE_SOFT, WHITE)
    draw = ImageDraw.Draw(canvas)

    logo = Image.open(ASSETS / "logo-fixaverse.png").convert("RGBA")
    lw = 680
    lh = int(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
    canvas.paste(logo, ((w - lw) // 2, (h - lh) // 2 - 60), logo)

    tag = "ТОиР · учёт ремонтов · ИИ"
    tw = draw.textlength(tag, font=font(28))
    draw.text(((w - tw) // 2, (h + lh) // 2 + 20), tag, font=font(28), fill=(75, 85, 99))

    save_pair("g4-brand-minimal", canvas)


def g5_browser_mockup() -> None:
    """Мокап вкладки браузера со скрином — «живой» продукт."""
    w = h = 1080
    canvas = gradient(w, h, (248, 250, 252), WHITE)
    draw = ImageDraw.Draw(canvas)

    frame_w, frame_h = 920, 780
    fx, fy = (w - frame_w) // 2, 180
    draw.rounded_rectangle((fx, fy, fx + frame_w, fy + frame_h), radius=16, fill=WHITE, outline=BORDER, width=2)

    chrome_h = 48
    draw.rectangle((fx, fy, fx + frame_w, fy + chrome_h), fill=(243, 244, 246))
    for i, c in enumerate([(239, 68, 68), (250, 204, 21), (34, 197, 94)]):
        draw.ellipse((fx + 18 + i * 22, fy + 18, fx + 30 + i * 22, fy + 30), fill=c)
    draw.rounded_rectangle((fx + 120, fy + 12, fx + frame_w - 24, fy + 36), radius=8, fill=WHITE, outline=BORDER)
    draw.text((fx + 132, fy + 16), "fixaverse.ru", font=font(16), fill=(107, 114, 128))

    shot = fit_cover(Image.open(ASSETS / ".hero-capture.png"), frame_w - 4, frame_h - chrome_h - 4)
    paste_rounded(canvas, shot, (fx + 2, fy + chrome_h + 2), radius=0)

    paste_logo(canvas, (56, 56), 200)
    save_pair("g5-browser-mockup", canvas)


def main() -> None:
    g1_photo_frame()
    g2_product_card()
    g3_copilot_scene()
    g4_brand_minimal()
    g5_browser_mockup()
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    main()
