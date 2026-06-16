#!/usr/bin/env python3
"""Generate Fixaverse Direct ad image proposals (light backgrounds, site palette)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "landing" / "assets"
OUT = ASSETS / "ad-proposals"

WHITE = (255, 255, 255)
TEXT = (13, 27, 58)       # #0d1b3a
BLUE = (26, 111, 255)     # #1a6fff
BLUE_SOFT = (238, 243, 255)  # #eef3ff
GREEN = (69, 212, 131)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def gradient(w: int, h: int, top: tuple, bottom: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        row = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(w):
            px[x, y] = row
    return img


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def paste_rounded(base: Image.Image, im: Image.Image, xy: tuple[int, int], radius: int = 24) -> None:
    im = im.convert("RGBA")
    mask = rounded_mask(im.size, radius)
    base.paste(im, xy, mask)


def fit_cover(src: Image.Image, tw: int, th: int) -> Image.Image:
    src = src.convert("RGB")
    r = max(tw / src.width, th / src.height)
    nw, nh = int(src.width * r), int(src.height * r)
    im = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def add_shadow(card: Image.Image, blur: int = 18, offset: int = 8) -> Image.Image:
    w, h = card.size
    shadow = Image.new("RGBA", (w + offset * 2, h + offset * 2), (0, 0, 0, 0))
    alpha = Image.new("L", card.size, 40)
    sh = Image.new("RGBA", card.size, (13, 27, 58, 255))
    sh.putalpha(alpha)
    shadow.paste(sh, (offset, offset), sh)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
    out.paste(shadow, (0, 0), shadow)
    out.paste(card, (0, 0), card if card.mode == "RGBA" else None)
    return out


def draw_logo(draw: ImageDraw.ImageDraw, xy: tuple[int, int], max_w: int = 280) -> None:
    logo = Image.open(ASSETS / "logo-fixaverse.png").convert("RGBA")
    r = max_w / logo.width
    logo = logo.resize((max_w, int(logo.height * r)), Image.Resampling.LANCZOS)
    # logo pasted separately in callers


def paste_logo(canvas: Image.Image, xy: tuple[int, int], max_w: int = 280) -> None:
    logo = Image.open(ASSETS / "logo-fixaverse.png").convert("RGBA")
    r = max_w / logo.width
    logo = logo.resize((max_w, int(logo.height * r)), Image.Resampling.LANCZOS)
    canvas.paste(logo, xy, logo)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=fnt) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def save_square(name: str, canvas: Image.Image) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}-1080x1080.png"
    canvas.convert("RGB").save(path, "PNG", optimize=True)
    # wide crop from center
    wide = fit_cover(canvas, 1080, 607)
    wide_path = OUT / f"{name}-1080x607.png"
    wide.save(wide_path, "PNG", optimize=True)
    print(path)
    print(wide_path)
    return path


def proposal_a_site_light() -> None:
    """White canvas + hero UI card (как на лендинге), без чёрного фона."""
    w = h = 1080
    canvas = Image.new("RGB", (w, h), WHITE)
    draw = ImageDraw.Draw(canvas)

    paste_logo(canvas, (56, 48), 300)

    capture = Image.open(ASSETS / ".hero-capture.png").convert("RGB")
    card_w, card_h = 920, 620
    card = fit_cover(capture, card_w, card_h)
    card_rgba = Image.new("RGBA", (card_w, card_h))
    card_rgba.paste(card)
    card_rgba = add_shadow(card_rgba)
    ox = (w - card_rgba.width) // 2
    canvas.paste(card_rgba, (ox, 200), card_rgba)

    draw.text((56, 880), "СИСТЕМА ТОИР НА ОСНОВЕ ИИ", font=font(22, True), fill=BLUE)
    draw.text((56, 920), "Заказ-наряды · Copilot в цеху · On-premise", font=font(20), fill=TEXT)

    save_square("proposal-a-site-light", canvas)


def proposal_b_blue_gradient() -> None:
    """Мягкий градиент сайта + фото цеха на всю ширину."""
    w = h = 1080
    canvas = gradient(w, h, BLUE_SOFT, WHITE)
    draw = ImageDraw.Draw(canvas)

    hero = fit_cover(Image.open(ASSETS / "hero-bg.jpg"), w, 560)
    paste_rounded(canvas, hero, (40, 120), 28)

    paste_logo(canvas, (56, 40), 260)
    draw.rounded_rectangle((40, 720, w - 40, 1020), radius=24, fill=WHITE)
    draw.text((72, 752), "Первая система ТОиР", font=font(42, True), fill=TEXT)
    draw.text((72, 808), "на основе ИИ", font=font(42, True), fill=BLUE)
    draw.text((72, 880), "Учёт ремонтов и обслуживание оборудования", font=font(24), fill=(75, 85, 99))
    draw.rounded_rectangle((72, 940, 340, 990), radius=999, fill=BLUE)
    draw.text((108, 952), "Запросить демо", font=font(22, True), fill=WHITE)

    save_square("proposal-b-blue-gradient", canvas)


def proposal_c_copilot_field() -> None:
    """Техник у станка — светлый фон, акцент на «copilot в поле»."""
    w = h = 1080
    canvas = gradient(w, h, WHITE, BLUE_SOFT)
    draw = ImageDraw.Draw(canvas)

    paste_logo(canvas, (56, 48), 280)

    photo = fit_cover(Image.open(ASSETS / "hero-cmms.webp"), 720, 720)
    paste_rounded(canvas, photo, (w - 760, 160), 32)

    draw.rounded_rectangle((56, 200, 520, 620), radius=28, fill=WHITE)
    draw.text((88, 240), "Copilot", font=font(28, True), fill=BLUE)
    draw.text((88, 280), "для техников", font=font(28, True), fill=TEXT)
    lines = wrap_text(
        draw,
        "Диагностика у станка: симптом → причина → решение. Фото и отчёт в одном контуре.",
        font(22),
        400,
    )
    y = 340
    for line in lines:
        draw.text((88, y), line, font=font(22), fill=(75, 85, 99))
        y += 34

    for i, bullet in enumerate(["Заказ-наряды", "Память машины", "On-premise"]):
        by = 500 + i * 44
        draw.ellipse((88, by + 8, 104, by + 24), fill=GREEN)
        draw.text((120, by), bullet, font=font(22, True), fill=TEXT)

    draw.text((56, 980), "Автоматизация ТОиР на предприятии", font=font(20), fill=BLUE)

    save_square("proposal-c-copilot-field", canvas)


def proposal_d_minimal_card() -> None:
    """Минимализм: белый фон, одна карточка продукта, крупный заголовок."""
    w = h = 1080
    canvas = Image.new("RGB", (w, h), WHITE)
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((0, 0, w, 200), radius=0, fill=BLUE_SOFT)
    paste_logo(canvas, (56, 56), 320)

    capture = fit_cover(Image.open(ASSETS / ".hero-capture.png"), 880, 500)
    card = Image.new("RGBA", (880, 500))
    card.paste(capture)
    card = add_shadow(card.convert("RGBA"))
    canvas.paste(card, (100, 240), card)

    draw.text((100, 780), "Программа учёта ремонтов", font=font(48, True), fill=TEXT)
    draw.text((100, 848), "и автоматизация ТОиР", font=font(48, True), fill=BLUE)
    draw.text((100, 930), "Для заводов и сетей объектов", font=font(24), fill=(75, 85, 99))

    save_square("proposal-d-minimal-card", canvas)


def proposal_e_split_industrial() -> None:
    """Сплит: слева текст на белом, справа промышленное фото."""
    w = h = 1080
    canvas = Image.new("RGB", (w, h), WHITE)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, 520, h), fill=BLUE_SOFT)
    paste_logo(canvas, (48, 56), 260)

    lines_title = ["Система", "ТОиР", "на основе", "ИИ"]
    y = 220
    for i, line in enumerate(lines_title):
        draw.text((48, y), line, font=font(52 if i < 2 else 44, True), fill=BLUE if i == 1 else TEXT)
        y += 58 if i < 2 else 50

    draw.text((48, 500), "Управление обслуживанием", font=font(22), fill=TEXT)
    draw.text((48, 536), "и ремонтом оборудования", font=font(22), fill=TEXT)

    draw.rounded_rectangle((48, 600, 280, 650), radius=999, fill=BLUE)
    draw.text((78, 612), "fixaverse.ru", font=font(20, True), fill=WHITE)

    photo = fit_cover(Image.open(ASSETS / "hero-photo.png"), 560, h)
    canvas.paste(photo, (520, 0))

    overlay = Image.new("RGBA", (120, h), (238, 243, 255, 180))
    canvas.paste(overlay, (500, 0), overlay)

    save_square("proposal-e-split-industrial", canvas)


def main() -> None:
    for fn in (
        proposal_a_site_light,
        proposal_b_blue_gradient,
        proposal_c_copilot_field,
        proposal_d_minimal_card,
        proposal_e_split_industrial,
    ):
        fn()
    print(f"\nDone → {OUT}")


if __name__ == "__main__":
    main()
