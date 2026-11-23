"""Text formatting rules applied to the final transcription."""

import re
from dataclasses import dataclass

# Opening marks that may precede the first letter of a sentence.
_OPENERS = r"[¿¡\"'(\[]*"
_END_MARKS = ".?!…:;"


@dataclass
class FormatOptions:
    capitalize: bool = True
    final_period: bool = True
    capitalize_sentences: bool = False


def _upper_first(match: re.Match) -> str:
    return match.group(1) + match.group(2).upper()


def format_text(text: str, options: FormatOptions) -> str:
    # Whisper sometimes leaves repeated, leading or trailing whitespace.
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return text

    if options.capitalize_sentences:
        text = re.sub(rf"(^{_OPENERS}|[.!?…]\s+{_OPENERS})(\w)", _upper_first, text)
    elif options.capitalize:
        text = re.sub(rf"^({_OPENERS})(\w)", _upper_first, text)

    if options.final_period and text[-1] not in _END_MARKS:
        text += _closing_mark(text)
    return text


def _closing_mark(text: str) -> str:
    """Close an open ¿ or ¡ with its pair, otherwise end with a period."""
    for opener, closer in (("¿", "?"), ("¡", "!")):
        last = text.rfind(opener)
        if last != -1 and closer not in text[last:]:
            return closer
    return "."
