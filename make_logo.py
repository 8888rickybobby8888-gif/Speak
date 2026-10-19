"""Draws the Speak logo: a speech bubble holding a sound wave.

Writes icons/speak.png (extension icon) and icons/speak-file.svg (icon for .speak files).
Run: python make_logo.py   (needs Pillow: pip install pillow)
"""
import os

from PIL import Image, ImageDraw

SIZE = 256
SCALE = 4  # draw big, then shrink for smooth edges
TOP, BOTTOM = (20, 184, 166), (37, 99, 235)  # teal to blue

BARS = [(88, 30), (108, 62), (128, 92), (148, 62), (168, 30)]  # (centre x, height)
BAR_WIDTH = 14
BAR_CENTRE_Y = 109
BUBBLE = (40, 50, 216, 168)
BUBBLE_RADIUS = 38
TAIL = [(84, 160), (84, 214), (134, 160)]
BACKGROUND_RADIUS = 52


def gradient(size):
    image = Image.new('RGB', (size, size))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            pixels[x, y] = tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
    return image


def draw_logo():
    big = SIZE * SCALE
    s = SCALE
    canvas = gradient(big).convert('RGBA')
    mask = Image.new('L', (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, big - 1, big - 1), BACKGROUND_RADIUS * s, fill=255)
    canvas.putalpha(mask)

    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = BUBBLE
    draw.rounded_rectangle((x0 * s, y0 * s, x1 * s, y1 * s), BUBBLE_RADIUS * s, fill='white')
    draw.polygon([(x * s, y * s) for x, y in TAIL], fill='white')

    bars = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    bar_draw = ImageDraw.Draw(bars)
    for centre, height in BARS:
        left, right = (centre - BAR_WIDTH / 2) * s, (centre + BAR_WIDTH / 2) * s
        top, bottom = (BAR_CENTRE_Y - height / 2) * s, (BAR_CENTRE_Y + height / 2) * s
        bar_draw.rounded_rectangle((left, top, right, bottom), BAR_WIDTH / 2 * s, fill='white')
    # colour the bars with the same gradient so they match the background
    tint = gradient(big).convert('RGBA')
    tint.putalpha(bars.getchannel('A'))
    canvas.alpha_composite(tint)
    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


def write_svg(path):
    bars = '\n    '.join(
        f'<rect x="{c - BAR_WIDTH / 2:g}" y="{BAR_CENTRE_Y - h / 2:g}" width="{BAR_WIDTH}" height="{h}" rx="{BAR_WIDTH / 2:g}"/>'
        for c, h in BARS)
    x0, y0, x1, y1 = BUBBLE
    tail = ' '.join(f'{x},{y}' for x, y in TAIL)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}">
  <rect x="40" y="50" width="{x1 - x0}" height="{y1 - y0}" rx="{BUBBLE_RADIUS}" fill="#14B8A6"/>
  <polygon points="{tail}" fill="#14B8A6"/>
  <g fill="#ffffff">
    {bars}
  </g>
</svg>
'''
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(svg)


if __name__ == '__main__':
    os.makedirs('icons', exist_ok=True)
    draw_logo().save('icons/speak.png')
    write_svg('icons/speak-file.svg')
    print('wrote icons/speak.png and icons/speak-file.svg')
