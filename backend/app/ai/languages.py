from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SupportedLanguage:
    """Canonical language label plus aliases detected in resumes and JDs."""

    label: str
    aliases: tuple[str, ...]


SUPPORTED_LANGUAGES: tuple[SupportedLanguage, ...] = (
    SupportedLanguage(
        label="English",
        aliases=("english", "anh", "tiếng anh", "tieng anh", "英語", "英语"),
    ),
    SupportedLanguage(
        label="Vietnamese",
        aliases=(
            "vietnamese",
            "vietnamese language",
            "vietnamese communication",
            "viet",
            "việt",
            "viet nam",
            "việt nam",
            "tiếng việt",
            "tieng viet",
            "ベトナム語",
            "越南语",
        ),
    ),
    SupportedLanguage(
        label="Chinese",
        aliases=(
            "chinese",
            "mandarin",
            "mandarin chinese",
            "trung",
            "tiếng trung",
            "tieng trung",
            "tiếng hoa",
            "tieng hoa",
            "中国語",
            "中文",
            "普通话",
            "普通話",
            "汉语",
            "漢語",
        ),
    ),
    SupportedLanguage(
        label="Japanese",
        aliases=(
            "japanese",
            "nhat",
            "nhật",
            "tiếng nhật",
            "tieng nhat",
            "nihongo",
            "日本語",
            "日语",
            "日語",
        ),
    ),
)


def detect_supported_languages(text: str) -> list[str]:
    """Return canonical supported language labels mentioned in text.

    The matching is intentionally deterministic and alias-based so local parsing
    and scoring remain stable for portfolio/demo use.
    """

    normalized_text = text.casefold()
    detected: list[str] = []
    for language in SUPPORTED_LANGUAGES:
        if any(_contains_alias(normalized_text, alias) for alias in language.aliases):
            detected.append(language.label)
    return detected


def canonicalize_supported_languages(languages: list[str]) -> list[str]:
    """Normalize parsed language values to canonical supported labels."""

    canonical: list[str] = []
    for language in languages:
        matches = detect_supported_languages(language)
        for match in matches:
            if match not in canonical:
                canonical.append(match)
    return canonical


def _contains_alias(normalized_text: str, alias: str) -> bool:
    normalized_alias = alias.casefold()
    if _contains_cjk_or_kana(normalized_alias):
        return normalized_alias in normalized_text

    pattern = rf"(?<!\w){re.escape(normalized_alias)}(?!\w)"
    return re.search(pattern, normalized_text) is not None


def _contains_cjk_or_kana(value: str) -> bool:
    return any(
        "\u3040" <= char <= "\u30ff" or "\u3400" <= char <= "\u9fff"
        for char in value
    )
