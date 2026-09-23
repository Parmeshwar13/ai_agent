"""Small text helpers shared by organization and project creation."""

import re
import unicodedata

from django.utils.text import slugify


def unique_slug(value: str, taken, *, fallback: str, max_length: int = 48) -> str:
    """Return a slug that does not collide with `taken(slug) -> bool`."""

    normalized = unicodedata.normalize("NFKD", value or "")
    base = slugify(normalized)[:max_length].strip("-") or fallback
    candidate = base
    suffix = 2
    while taken(candidate):
        tail = f"-{suffix}"
        candidate = f"{base[: max_length - len(tail)].strip('-')}{tail}"
        suffix += 1
    return candidate


def project_key(name: str) -> str:
    """Short human key such as WFM from 'Workforce management'."""

    words = re.findall(r"[A-Za-z0-9]+", name or "")
    if not words:
        return "PRJ"
    if len(words) == 1:
        return words[0][:4].upper()
    return "".join(word[0] for word in words[:4]).upper()[:6]


def unique_key(name: str, taken) -> str:
    base = project_key(name)
    candidate = base
    suffix = 2
    while taken(candidate):
        tail = str(suffix)
        candidate = f"{base[: 6 - len(tail)]}{tail}"
        suffix += 1
    return candidate
