#!/usr/bin/env python3
"""Add small centered title text to a clean cover with explicit real fonts."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from fontTools.ttLib import TTFont


def fit_font(path, text, desired, max_width, minimum=8):
    for size in range(max(minimum, desired), minimum - 1, -1):
        font = ImageFont.truetype(str(path), size)
        box = font.getbbox(text)
        if box[2] - box[0] <= max_width:
            return font
    raise ValueError('Text cannot fit legibly; use multiline typesetting or a wider canvas without changing the words.')


def require_glyphs(path, text):
    with TTFont(path) as font:
        cmap = font.getBestCmap() or {}
    missing = sorted({char for char in text if not char.isspace() and ord(char) not in cmap})
    if missing:
        raise ValueError(f'Font {path.name} does not cover: {"".join(missing)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--blackletter-font', type=Path, required=True,
                        help='Real Fraktur/Blackletter font covering the supplied title glyphs.')
    parser.add_argument('--sans-font', type=Path, required=True)
    parser.add_argument('--title-font', type=Path,
                        help='Optional separate title font, e.g. Chinese Ming/Song for a Chinese title.')
    parser.add_argument('--title', default='The Last Wall')
    parser.add_argument('--subtitle', default='Original Soundtrack')
    parser.add_argument('--author', help='Author for the credit line; omit to render no credit line at all.')
    parser.add_argument('--credit-text', help='Exact full credit line; overrides the Music by + author convention.')
    parser.add_argument('--top', type=float, default=0.105)
    args = parser.parse_args()
    if not 0.04 <= args.top <= 0.20:
        parser.error('--top must be between 0.04 and 0.20')
    if args.image.resolve() == args.output.resolve() or args.output.exists():
        parser.error('Use a new output path; source and existing files are never overwritten.')
    for font_path in [args.blackletter_font, args.sans_font, args.title_font or args.blackletter_font]:
        if not font_path.is_file():
            parser.error(f'Font not found: {font_path}')
    credit = (args.credit_text if args.credit_text is not None else
              'Music by ' + args.author if args.author else '')
    rows = [
        (credit, args.sans_font, 0.015, '#eee8dc', 0.012),
        (args.title, args.title_font or args.blackletter_font, 0.032, '#fffaf0', 0.008),
        (args.subtitle, args.blackletter_font, 0.025, '#fffaf0', 0.0),
    ]
    for text, path, *_ in rows:
        require_glyphs(path, text)
    im = ImageOps.exif_transpose(Image.open(args.image)).convert('RGB')
    width, height = im.size
    draw = ImageDraw.Draw(im)
    y = int(height * args.top)
    for text, path, scale, color, gap in rows:
        if not text:
            continue
        font = fit_font(path, text, round(min(width, height) * scale), int(width * 0.70),
                        max(8, round(min(width, height) * 0.012)))
        box = font.getbbox(text)
        x = (width - (box[2] - box[0])) // 2 - box[0]
        draw.text((x, y - box[1]), text, font=font, fill=color,
                  stroke_width=max(1, round(min(im.size) / 1800)), stroke_fill='#5a5357')
        y += box[3] - box[1] + round(height * gap)
        if y > height * 0.95:
            parser.error('Text would overflow; use a different text position or multiline layout.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    im.save(args.output)
    print(args.output)


if __name__ == '__main__':
    main()
