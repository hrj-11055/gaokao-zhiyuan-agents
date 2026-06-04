#!/usr/bin/env python3

from pathlib import Path

from PIL import Image, ImageDraw


SIZE = 256
SCALE = 4
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "gaokao-miniprogram" / "src" / "static" / "avatars"


def box(values):
    return tuple(round(value * SCALE) for value in values)


def point(values):
    return tuple(round(value * SCALE) for value in values)


def ellipse(draw, values, fill, outline=None, width=1):
    draw.ellipse(box(values), fill=fill, outline=outline, width=round(width * SCALE))


def polygon(draw, values, fill):
    draw.polygon([point(value) for value in values], fill=fill)


def line(draw, values, fill, width=1):
    draw.line([point(value) for value in values], fill=fill, width=round(width * SCALE), joint="curve")


def eyes(draw, left, right, color="#273043", radius=7):
    for x, y in (left, right):
        ellipse(draw, (x - radius, y - radius, x + radius, y + radius), color)
        ellipse(draw, (x - 2, y - 3, x + 1, y), "#FFFFFF")


def cheeks(draw, left, right, color="#F6A6A6"):
    ellipse(draw, (left[0] - 10, left[1] - 5, left[0] + 10, left[1] + 5), color)
    ellipse(draw, (right[0] - 10, right[1] - 5, right[0] + 10, right[1] + 5), color)


def nose_and_smile(draw, nose_y=157, color="#273043"):
    polygon(draw, ((123, nose_y), (133, nose_y), (128, nose_y + 8)), color)
    line(draw, ((128, nose_y + 7), (128, nose_y + 15)), color, 2)
    line(draw, ((128, nose_y + 14), (119, nose_y + 18)), color, 2)
    line(draw, ((128, nose_y + 14), (137, nose_y + 18)), color, 2)


def canvas(background, halo):
    image = Image.new("RGB", (SIZE * SCALE, SIZE * SCALE), background)
    draw = ImageDraw.Draw(image)
    ellipse(draw, (16, 16, 240, 240), halo)
    ellipse(draw, (55, 210, 201, 244), "#D7B8A050")
    return image, draw


def save(image, name):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image.resize((SIZE, SIZE), Image.Resampling.LANCZOS).save(
        OUTPUT_DIR / f"{name}.png",
        optimize=True,
    )


def panda():
    image, draw = canvas("#FFF8F2", "#FFE3CF")
    ellipse(draw, (43, 173, 213, 270), "#263348")
    ellipse(draw, (42, 42, 101, 101), "#263348")
    ellipse(draw, (155, 42, 214, 101), "#263348")
    ellipse(draw, (50, 55, 206, 218), "#FFFDF8")
    ellipse(draw, (75, 102, 115, 151), "#263348")
    ellipse(draw, (141, 102, 181, 151), "#263348")
    eyes(draw, (97, 127), (159, 127), "#111827", 6)
    ellipse(draw, (100, 139, 156, 190), "#FFF1DF")
    cheeks(draw, (76, 158), (180, 158), "#F7B4B4")
    nose_and_smile(draw, 153)
    save(image, "panda")


def penguin():
    image, draw = canvas("#F4FAFF", "#DDEEFF")
    ellipse(draw, (46, 166, 210, 270), "#23314F")
    ellipse(draw, (51, 42, 205, 222), "#23314F")
    ellipse(draw, (70, 78, 132, 169), "#FFFDF8")
    ellipse(draw, (124, 78, 186, 169), "#FFFDF8")
    ellipse(draw, (69, 126, 187, 215), "#FFFDF8")
    eyes(draw, (100, 126), (156, 126), "#1A2235", 6)
    polygon(draw, ((113, 147), (143, 147), (128, 166)), "#F7A928")
    cheeks(draw, (82, 157), (174, 157), "#F4A9AF")
    save(image, "penguin")


def otter():
    image, draw = canvas("#FFF9F0", "#F6E0BD")
    ellipse(draw, (44, 174, 212, 270), "#79503A")
    ellipse(draw, (48, 55, 96, 103), "#79503A")
    ellipse(draw, (160, 55, 208, 103), "#79503A")
    ellipse(draw, (57, 62, 199, 220), "#98684A")
    ellipse(draw, (69, 73, 91, 95), "#D8A982")
    ellipse(draw, (165, 73, 187, 95), "#D8A982")
    eyes(draw, (100, 129), (156, 129), "#241B18", 6)
    ellipse(draw, (91, 139, 165, 193), "#E7C49D")
    cheeks(draw, (76, 158), (180, 158), "#ECA8A1")
    nose_and_smile(draw, 151, "#241B18")
    for y, end in ((158, 66), (167, 62), (158, 190), (167, 194)):
        line(draw, ((96 if end < 100 else 160, y), (end, y - 4 if y == 158 else y + 1)), "#5E3D2D", 2)
    save(image, "otter")


def fox():
    image, draw = canvas("#FFF7F0", "#FFD9C5")
    ellipse(draw, (43, 176, 213, 270), "#C96333")
    polygon(draw, ((61, 119), (63, 42), (112, 74)), "#D96D35")
    polygon(draw, ((195, 119), (193, 42), (144, 74)), "#D96D35")
    polygon(draw, ((70, 91), (72, 59), (99, 80)), "#F4B0A1")
    polygon(draw, ((186, 91), (184, 59), (157, 80)), "#F4B0A1")
    ellipse(draw, (60, 66, 196, 218), "#D96D35")
    polygon(draw, ((65, 139), (128, 216), (128, 126)), "#FFF1DF")
    polygon(draw, ((191, 139), (128, 216), (128, 126)), "#FFF1DF")
    eyes(draw, (101, 127), (155, 127), "#3B2723", 6)
    cheeks(draw, (81, 156), (175, 156), "#EE9E94")
    nose_and_smile(draw, 151, "#3B2723")
    save(image, "fox")


def rabbit():
    image, draw = canvas("#FFF7FB", "#F7DBEC")
    ellipse(draw, (47, 177, 209, 270), "#F4E5E8")
    ellipse(draw, (68, 18, 112, 127), "#F4E5E8")
    ellipse(draw, (144, 18, 188, 127), "#F4E5E8")
    ellipse(draw, (79, 30, 101, 111), "#EFAFC4")
    ellipse(draw, (155, 30, 177, 111), "#EFAFC4")
    ellipse(draw, (56, 72, 200, 222), "#FFF9F7")
    eyes(draw, (101, 132), (155, 132), "#463641", 6)
    ellipse(draw, (105, 144, 151, 190), "#FFF0E9")
    cheeks(draw, (79, 159), (177, 159), "#F2A6BA")
    polygon(draw, ((122, 151), (134, 151), (128, 160)), "#D9839D")
    line(draw, ((128, 159), (128, 171)), "#674A58", 2)
    line(draw, ((128, 170), (120, 175)), "#674A58", 2)
    line(draw, ((128, 170), (136, 175)), "#674A58", 2)
    save(image, "rabbit")


def owl():
    image, draw = canvas("#F8F6FF", "#E4DEFA")
    ellipse(draw, (47, 172, 209, 270), "#735A83")
    polygon(draw, ((65, 104), (73, 45), (115, 75)), "#80668F")
    polygon(draw, ((191, 104), (183, 45), (141, 75)), "#80668F")
    ellipse(draw, (57, 65, 199, 222), "#80668F")
    ellipse(draw, (72, 101, 132, 164), "#F4EBDD")
    ellipse(draw, (124, 101, 184, 164), "#F4EBDD")
    eyes(draw, (102, 132), (154, 132), "#2D2634", 8)
    polygon(draw, ((117, 154), (139, 154), (128, 172)), "#E9A23B")
    polygon(draw, ((82, 177), (128, 212), (128, 172)), "#C4A8CC")
    polygon(draw, ((174, 177), (128, 212), (128, 172)), "#C4A8CC")
    save(image, "owl")


def bear():
    image, draw = canvas("#FFF8ED", "#F3DEB9")
    ellipse(draw, (43, 174, 213, 270), "#8B6041")
    ellipse(draw, (45, 48, 101, 104), "#8B6041")
    ellipse(draw, (155, 48, 211, 104), "#8B6041")
    ellipse(draw, (59, 65, 197, 222), "#A77752")
    ellipse(draw, (61, 64, 87, 90), "#D1A47C")
    ellipse(draw, (169, 64, 195, 90), "#D1A47C")
    eyes(draw, (101, 130), (155, 130), "#2F241F", 6)
    ellipse(draw, (95, 139, 161, 194), "#E4BF95")
    cheeks(draw, (78, 158), (178, 158), "#E7A49B")
    nose_and_smile(draw, 152, "#2F241F")
    save(image, "bear")


def shiba():
    image, draw = canvas("#FFF8EF", "#FFE0B8")
    ellipse(draw, (43, 176, 213, 270), "#C87536")
    polygon(draw, ((61, 117), (68, 39), (116, 77)), "#D48440")
    polygon(draw, ((195, 117), (188, 39), (140, 77)), "#D48440")
    polygon(draw, ((72, 84), (76, 57), (98, 76)), "#E9A08C")
    polygon(draw, ((184, 84), (180, 57), (158, 76)), "#E9A08C")
    ellipse(draw, (58, 67, 198, 221), "#D48440")
    polygon(draw, ((65, 139), (128, 217), (128, 130)), "#FFF0DB")
    polygon(draw, ((191, 139), (128, 217), (128, 130)), "#FFF0DB")
    eyes(draw, (101, 129), (155, 129), "#36261E", 6)
    cheeks(draw, (80, 157), (176, 157), "#EEA299")
    nose_and_smile(draw, 151, "#36261E")
    save(image, "shiba")


def main():
    for render in (panda, penguin, otter, fox, rabbit, owl, bear, shiba):
        render()


if __name__ == "__main__":
    main()
