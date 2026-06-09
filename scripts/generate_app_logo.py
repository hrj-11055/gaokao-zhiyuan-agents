from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "gaokao-miniprogram" / "src" / "static" / "logo.png"
SIZE = 256
SCALE = 3


def lerp(a, b, t):
    return int(a + (b - a) * t)


def gradient_rect(size, top, bottom):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = image.load()
    for y in range(size):
        t = y / max(size - 1, 1)
        for x in range(size):
            glow = max(0, 1 - ((x - size * 0.24) ** 2 + (y - size * 0.18) ** 2) ** 0.5 / (size * 0.9))
            tt = min(1, max(0, t - glow * 0.14))
            pixels[x, y] = (
                lerp(top[0], bottom[0], tt),
                lerp(top[1], bottom[1], tt),
                lerp(top[2], bottom[2], tt),
                255,
            )
    return image


def draw_logo():
    canvas_size = SIZE * SCALE
    radius = 56 * SCALE
    inset = 18 * SCALE

    image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [inset, inset + 10 * SCALE, canvas_size - inset, canvas_size - inset + 10 * SCALE],
        radius=radius,
        fill=(194, 65, 12, 58),
    )
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18 * SCALE)))

    mask = Image.new("L", (canvas_size, canvas_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mark_box = [inset, inset, canvas_size - inset, canvas_size - inset]
    mask_draw.rounded_rectangle(mark_box, radius=radius, fill=255)

    mark = gradient_rect(canvas_size, (255, 122, 58), (234, 88, 12))
    image.alpha_composite(Image.composite(mark, Image.new("RGBA", mark.size, (0, 0, 0, 0)), mask))

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        [34 * SCALE, 34 * SCALE, 222 * SCALE, 222 * SCALE],
        radius=44 * SCALE,
        outline=(255, 255, 255, 54),
        width=2 * SCALE,
    )

    white = (255, 255, 255, 244)
    cream = (255, 247, 237, 230)
    teal = (20, 184, 166, 238)
    navy = (17, 24, 39, 80)

    # Open guide book.
    left_page = [
        (64 * SCALE, 98 * SCALE),
        (121 * SCALE, 76 * SCALE),
        (121 * SCALE, 164 * SCALE),
        (64 * SCALE, 184 * SCALE),
    ]
    right_page = [
        (135 * SCALE, 76 * SCALE),
        (192 * SCALE, 98 * SCALE),
        (192 * SCALE, 184 * SCALE),
        (135 * SCALE, 164 * SCALE),
    ]
    draw.polygon(left_page, fill=cream)
    draw.polygon(right_page, fill=white)
    draw.line([121 * SCALE, 78 * SCALE, 121 * SCALE, 164 * SCALE], fill=navy, width=3 * SCALE)
    draw.line([135 * SCALE, 78 * SCALE, 135 * SCALE, 164 * SCALE], fill=navy, width=3 * SCALE)

    for offset in (0, 22):
        draw.line(
            [
                (78 * SCALE, (118 + offset) * SCALE),
                (105 * SCALE, (108 + offset) * SCALE),
            ],
            fill=(234, 88, 12, 92),
            width=4 * SCALE,
        )
        draw.line(
            [
                (151 * SCALE, (108 + offset) * SCALE),
                (178 * SCALE, (118 + offset) * SCALE),
            ],
            fill=(234, 88, 12, 72),
            width=4 * SCALE,
        )

    # Decision path.
    path = [
        (86 * SCALE, 170 * SCALE),
        (116 * SCALE, 142 * SCALE),
        (143 * SCALE, 158 * SCALE),
        (172 * SCALE, 126 * SCALE),
    ]
    draw.line(path, fill=teal, width=9 * SCALE, joint="curve")
    for x, y in path:
        draw.ellipse(
            [x - 8 * SCALE, y - 8 * SCALE, x + 8 * SCALE, y + 8 * SCALE],
            fill=(255, 255, 255, 252),
            outline=teal,
            width=4 * SCALE,
        )

    final = image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    final.save(OUTPUT)


if __name__ == "__main__":
    draw_logo()
    print(OUTPUT)
