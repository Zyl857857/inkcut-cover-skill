#!/usr/bin/env python3
"""Prepare three cover prompts, including a source-faithful edit when supplied."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def typography(args, preserve=False):
    if args.no_text:
        return ('No typography, lettering or placeholder words anywhere. Do not add text, do not '
                'reserve sky or clear space for it, and do not change the composition for '
                'typesetting; keep the scene exactly as specified, sky or no sky.'
                + (' Preserve the existing scene layout; do not clear or move objects for text.'
                   if preserve else ''))
    position = ('Use existing clear background space, preferably upper center, without moving '
                'any source subject or major object.' if preserve else
                'Place a small centered group within the upper 9–25 percent of the canvas.')
    credit = (args.credit_text if args.credit_text is not None else
              'Music by ' + args.author if args.author else '')
    rows = []
    if credit:
        rows.append(f'Credit: {json.dumps(credit, ensure_ascii=False)} in tiny thin sans-serif; '
                    'use this exact literal text, never a name copied from a style example.')
    else:
        rows.append('No author-credit line.')
    for label, value in [('Main title', args.title), ('Subtitle', args.subtitle)]:
        rows.append(f'{label}: {json.dumps(value, ensure_ascii=False)} in restrained pale-white '
                    'Blackletter / Fraktur.' if value else f'No {label.lower()} line.')
    return (f'Typography: {position} ' + ' '.join(rows) +
            ' No other new lettering. For Chinese/Japanese use a fine Ming/Mincho/Song font; '
            'keep English title and subtitle in Fraktur. Preserve every word verbatim.')


def build(args):
    presets = json.loads((ROOT / 'references/presets.json').read_text(encoding='utf-8'))
    preset = presets[args.preset]
    template = (ROOT / 'references/prompt-template.txt').read_text(encoding='utf-8')
    preserve_template = (ROOT / 'references/preserve-source-template.txt').read_text(encoding='utf-8')
    source = args.source_image.resolve() if args.source_image else None
    source_ratio = None
    if source:
        from PIL import Image, ImageOps
        with Image.open(source) as im:
            oriented = ImageOps.exif_transpose(im)
            width, height = oriented.size
        source_ratio = f'{width}:{height}'
    count = args.people_count
    count_instruction = (
        'There are NO people. Do not add figures, faces or human silhouettes.' if count == 0 else
        f'Exactly {count} distinct people, with {count} heads and {count} bodies. Preserve every person; '
        'do not omit, merge, duplicate or add anyone. Check all rows and occlusions.' if count is not None else
        'Preserve the exact source person count, including all rows; add no new people.' if source else
        'Use exactly the figure count described by the subject specification.'
    )
    default_people = (
        'no people; the existing foreground scenery only' if count == 0 else
        'the same people, number and scene roles as Image 1, retaining their identities and basic '
        'clothing concept; do not import people from style references' if source else
        f'exactly {count} original figures in calm poses with simple unmarked clothing' if count is not None else
        preset['people']
    )
    variables = {
        'people': args.people or (
            default_people),
        'scene': args.scene or ('the existing setting and principal objects shown in Image 1'
                                if source else preset['scene']),
        'time': args.time or ('the same time of day and basic light palette as Image 1'
                              if source else preset['time']),
        'backdrop': args.backdrop or (
            'the actual distant environment visible in Image 1, whether sky, ocean, city, hills or mist; '
            'keep its nature and do not invent a sky or cloud field' if source else
            'a colored painterly sky and distant landscape appropriate to the requested scene'),
        'ratio': args.ratio or '1:1',
    }
    if args.no_text:
        source_text_policy = ('No lettering anywhere, including existing source text: remove it cleanly '
                              'without shifting any person, object, background geometry or horizon.')
    elif args.source_text:
        source_text_policy = (
            f'Preserve this legible source text verbatim: {json.dumps(args.source_text, ensure_ascii=False)}. '
            'Keep its source placement in the faithful edition. Do not translate it or reuse any '
            'source or style-example artist name as the new author credit.'
        )
    elif source:
        source_text_policy = ('Preserve existing legible source lettering when present, especially in '
                              'the faithful edition; do not invent unreadable words or infer new credits.')
    else:
        source_text_policy = 'No text other than the exact requested typography.'
    reference_instruction = (
        'Image 1 is the user scene reference. Preserve its theme, people count and principal objects; '
        'this is a recomposed edition, not the separate source-faithful edit. Any other supplied '
        'images are material references only; do not copy their people, insignia or wording.' if source else
        'Any supplied examples are STYLE REFERENCES ONLY: study their ink/paper contrast, matte cut '
        'edges and spacious framing, without copying characters, insignia, equipment, text or exact layout.'
    )
    figure_framing = ('No human silhouettes or figures anywhere.' if count == 0 else
        'Keep the source figures recognizable, with their original facing direction unless the user '
        'explicitly permits a pose change; do not automatically turn them into back views. Keep each '
        "figure's original scale as the baseline; never retreat the camera or shrink originally "
        'large subjects merely to reach 15–35 percent image height. Only modest refinements of '
        'scale, spacing and depth are allowed for this recomposed edition, with bodies naturally '
        'supported by the ground.' if source else
        'Keep people calm, mostly seen from behind or in three-quarter rear view, looking into '
        'the distance. Each visible figure silhouette is approximately 15–35 percent of image '
        'height, small in the environment, in the lower half and naturally grounded.'
    )
    character_policy = (
        'Transform the user-source subjects, retaining their identities and scene roles; do not '
        'replace them with generic travelers or import identities, badges, equipment or wording '
        'from style-only examples.' if source else
        'Use original characters and architecture only, with generic cloaks / uniforms / belts; '
        'no identifiable source characters, franchise emblems, source titles or proprietary equipment.'
    )
    directions = [
        'baseline scene as specified; balanced lighting and stable staging',
        'composition edition: modestly refine scale, spacing and depth for a clearer sky and ink '
        'foreground, while respecting all explicit user layout locks',
        'atmosphere edition: gently vary cloud light and warm/cool balance within the same time '
        'of day; retain the scene, story and subject count',
        'additional lighting edition, only if explicitly requested: softly vary haze and side light',
    ]
    labels = ['基准构图', '构图优化', '氛围变化', '补充光线']
    variants = []
    for index in range(args.count):
        if source and index == 0:
            ratio = args.ratio or source_ratio
            if args.ratio:
                framing = (
                    'The user explicitly requests this output ratio. Retain the ENTIRE original '
                    'composition; if necessary extend the outer canvas and fill only the new margins. '
                    'Uniformly fit the whole original together if required. Never move or resize '
                    'individual subjects, crop them out, or rebuild the interior arrangement.'
                )
            else:
                framing = ('Keep the original aspect ratio and whole original framing. No crop, '
                           'camera retreat, outpainting, individual scaling or rearrangement is needed.')
            prompt = preserve_template.format_map({
                'source_layout': args.source_layout or (
                    'No written anchors supplied. Inspect Image 1 before editing; infer no positions '
                    'from the preset or style examples.'),
                'framing_policy': framing, 'ratio': ratio,
                'count_instruction': count_instruction, 'backdrop': variables['backdrop'],
                'source_text_policy': source_text_policy,
                'typography': typography(args, preserve=True),
            })
            label, mode = '原图保留', 'source-faithful-edit'
        else:
            ratio = variables['ratio']
            direction = directions[index]
            if args.vary_position and index > 0:
                direction += '; slight lateral staging changes are permitted only outside user locks'
            fields = dict(variables, typography=typography(args), figure_framing=figure_framing,
                          count_instruction=count_instruction, source_text_policy=source_text_policy,
                          character_policy=character_policy,
                          subject_avoid=('people or insignia imported from style-only references' if source
                                         else 'existing anime characters or copied insignia'),
                          reference_instruction=reference_instruction, variation=direction)
            prompt = template.format_map(fields)
            label, mode = labels[index], 'recomposed' if source else 'generate'
        variants.append({'variant': index + 1, 'label': label, 'mode': mode,
                         'ratio': ratio, 'prompt': prompt})
    return {
        'preset': args.preset, 'preset_label': preset['label'],
        'source_image': str(source) if source else None, 'source_ratio': source_ratio,
        'style_reference_to_inspect': str(ROOT / 'assets/references' / preset['reference']),
        'reference_caveat': 'Inspect the actual source and style images; path inclusion here does not pass them to a model.',
        'text_enabled': not args.no_text,
        'people_count': count,
        'source_text': args.source_text if not args.no_text else None,
        'variables': dict(variables, title=args.title, subtitle=args.subtitle, author=args.author,
                          credit_text=args.credit_text),
        'variants': variants,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preset', choices=['A', 'B', 'C', 'D'], default='B')
    parser.add_argument('--title', default='The Last Wall')
    parser.add_argument('--subtitle', default='Original Soundtrack')
    parser.add_argument('--author', help='Author for the credit line; omit to render no credit line at all.')
    parser.add_argument('--credit-text', help='Optional exact full credit line, e.g. LIN, overriding Music by + author.')
    parser.add_argument('--people')
    parser.add_argument('--people-count', type=int, help='Manually verified person count, including zero; no automatic detection.')
    parser.add_argument('--scene')
    parser.add_argument('--time')
    parser.add_argument('--backdrop', help='Actual colored background role, e.g. ocean and surf rather than a sky.')
    parser.add_argument('--ratio', help='Explicit ratio for all outputs; source-faithful uses original if omitted.')
    parser.add_argument('--count', type=int, choices=range(1, 5), default=3,
                        help='Default 3. Override only when the current user explicitly requests another count.')
    parser.add_argument('--source-image', type=Path, help='User original edit target, NOT a pure style reference.')
    parser.add_argument('--source-layout', help='Human-observed position, scale and pose anchors from viewing the source.')
    parser.add_argument('--source-text', help='Exact legible text transcribed from the source; do not guess.')
    parser.add_argument('--no-text', action='store_true')
    parser.add_argument('--vary-position', action='store_true',
                        help='Permit slight shifts in variants 2 onward; NEVER affects the source-faithful first variant.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.ratio:
        try:
            parts = [int(x) for x in args.ratio.split(':')]
            if len(parts) != 2 or min(parts) <= 0:
                raise ValueError
        except ValueError:
            parser.error('--ratio must contain two positive integers, e.g. 1:1 or 5:2')
    if args.source_layout and not args.source_image:
        parser.error('--source-layout requires --source-image')
    if args.source_text and not args.source_image:
        parser.error('--source-text requires --source-image')
    if args.people_count is not None and args.people_count < 0:
        parser.error('--people-count must be zero or greater')
    if args.people_count == 0 and args.people:
        parser.error('Omit --people when --people-count is zero to avoid conflicting subject instructions')
    if args.source_image and not args.source_image.is_file():
        parser.error(f'Source image not found: {args.source_image}')
    try:
        result = json.dumps(build(args), ensure_ascii=False, indent=2)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + '\n', encoding='utf-8')
    else:
        print(result)


if __name__ == '__main__':
    main()
