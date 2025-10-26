"""Emoji translator spike entrypoint (delegates to production module)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.emoji_translator import DEFAULT_LOG, load_glyphs_from_file, load_lexicon, translate_tokens


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emoji translator prototype")
    parser.add_argument("--glyphs", help="Space-separated glyphs or ids", default=None)
    parser.add_argument("--glyph-file", help="Path to sample glyph JSON", default=None)
    parser.add_argument("--log", help="Log file path", default=str(DEFAULT_LOG))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lexicon = load_lexicon()

    if args.glyphs:
        tokens = args.glyphs.split()
    elif args.glyph_file:
        tokens = load_glyphs_from_file(Path(args.glyph_file))
    else:
        raise SystemExit("Provide --glyphs or --glyph-file")

    result = translate_tokens(tokens, index=lexicon, log_path=Path(args.log))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
