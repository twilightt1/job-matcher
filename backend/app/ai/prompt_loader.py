from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt_template(prompt_name: str) -> str:
    prompt_path = PROMPTS_DIR / prompt_name
    return prompt_path.read_text(encoding="utf-8")
