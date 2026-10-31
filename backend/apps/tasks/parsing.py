"""Understand one free-text sentence: customer, kind of work, assignee.

Rule-based and offline on purpose — fast, free, predictable. Every guess is
shown to the user before saving and can be corrected with one click.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from django.contrib.auth import get_user_model

from apps.core.models import Party

from .models import Task

_TRANSLATE = str.maketrans({
    "ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "أ": "ا", "إ": "ا", "آ": "ا",
    "‌": " ", "‏": "", "‎": "",
    **{c: str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")},
    **{c: str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")},
})

# Words that are part of a company name but too generic to identify it alone.
_GENERIC_PREFIXES = ("شرکت", "فروشگاه", "گروه", "موسسه", "دفتر", "هلدینگ", "کارخانه")

# Checked in order; the first kind with a matching keyword wins.
KIND_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    (Task.Kind.FAULT, ("خراب", "قطع", "خاموش", "مشکل", "ایراد", "ارور", "خطا", "کار نمی",
                       "نمیکنه", "نمی کنه", "هنگ", "سوخت", "بالا نمیاد", "وصل نمیشه",
                       "error", "down")),
    (Task.Kind.PROJECT, ("پروژه", "مناقصه", "پیاده سازی", "طراحی شبکه", "طرح جدید")),
    (Task.Kind.INSTALL, ("نصب", "راه اندازی", "کانفیگ", "پیکربندی",
                         "setup", "install")),
]

MANAGEMENT_ALIASES = {"مدیریت", "مدیر", "management"}

MENTION_RE = re.compile(r"@([^\s@،,.!?؟]+)")


def normalize(text: str) -> str:
    text = (text or "").translate(_TRANSLATE).lower()
    return re.sub(r"\s+", " ", text).strip()


def _contains_word(haystack: str, needle: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None


def guess_kind(text: str) -> str:
    norm = normalize(text)
    for kind, words in KIND_KEYWORDS:
        if any(w in norm for w in words):
            return kind
    return Task.Kind.SUPPORT


def _core_name(norm_name: str) -> str:
    for prefix in _GENERIC_PREFIXES:
        if norm_name.startswith(prefix + " "):
            return norm_name[len(prefix) + 1:].strip()
    return norm_name


def find_customer(text: str) -> Party | None:
    """The customer whose name (or distinctive part of it) appears in the text."""
    norm = normalize(text)
    best, best_len = None, 0
    for party in Party.objects.filter(is_customer=True).only("id", "name"):
        full = normalize(party.name)
        for candidate in {full, _core_name(full)}:
            if len(candidate) >= 3 and len(candidate) > best_len and _contains_word(norm, candidate):
                best, best_len = party, len(candidate)
    return best


def guess_customer_name(text: str) -> str:
    """A free-text guess like «شرکت آلفا» when the customer is not in the list."""
    m = re.search(r"(شرکت|فروشگاه|موسسه|گروه|هلدینگ)\s+(\S+)", normalize(text))
    return f"{m.group(1)} {m.group(2)}" if m else ""


def find_mention(text: str):
    """Return (found, user_or_None). ``@مدیریت`` → (True, None)."""
    User = get_user_model()
    for token in MENTION_RE.findall(text or ""):
        tok = normalize(token).replace("_", " ")
        if tok in MANAGEMENT_ALIASES:
            return True, None
        users = list(User.objects.filter(is_active=True).only("id", "full_name"))
        exact = [u for u in users if normalize(u.full_name) == tok]
        first = [u for u in users if normalize(u.full_name).split(" ")[:1] == [tok]]
        partial = [u for u in users if tok in normalize(u.full_name)]
        for group in (exact, first, partial):
            if len(group) == 1:
                return True, group[0]
    return False, None


@dataclass
class Parsed:
    kind: str
    customer: Party | None
    customer_name: str
    mention_found: bool
    assignee: object | None


def parse(text: str) -> Parsed:
    customer = find_customer(text)
    found, assignee = find_mention(text)
    return Parsed(
        kind=guess_kind(text),
        customer=customer,
        customer_name="" if customer else guess_customer_name(text),
        mention_found=found,
        assignee=assignee,
    )
