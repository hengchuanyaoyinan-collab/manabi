"""台本生成。

Claude Max 契約を活かし、Claude Code (CLI) 経由で `claude` コマンドを呼ぶ
ことで API キー不要で台本を生成する。

CLAUDE_BIN 環境変数が指定されていればそれを使用。なければ `claude` を
PATH から探す。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from src.config import TEMPLATES_DIR
from src.models import VideoScript


CLAUDE_BIN_ENV = "CLAUDE_BIN"
DEFAULT_PROMPT_TEMPLATE = TEMPLATES_DIR / "script-prompt.md"


class ScriptGenerationError(RuntimeError):
    pass


def _resolve_claude() -> str:
    cli = os.environ.get(CLAUDE_BIN_ENV) or shutil.which("claude")
    if not cli:
        raise ScriptGenerationError(
            "`claude` CLI が見つかりません。Claude Code をインストールするか、"
            f"環境変数 {CLAUDE_BIN_ENV} にパスを設定してください。"
        )
    return cli


def render_prompt(topic: str, template_path: Path | None = None) -> str:
    template_path = template_path or DEFAULT_PROMPT_TEMPLATE
    text = template_path.read_text(encoding="utf-8")
    return text.replace("{TOPIC}", topic)


def call_claude_cli(prompt: str, *, model: str = "claude-opus-4-7") -> str:
    """`claude -p <prompt>` を呼んで標準出力を返す。"""
    cli = _resolve_claude()
    cmd = [cli, "-p", prompt, "--model", model, "--output-format", "text"]
    proc = subprocess.run(
        cmd, check=False, capture_output=True, text=True, timeout=600
    )
    if proc.returncode != 0:
        raise ScriptGenerationError(
            f"claude CLI failed (exit {proc.returncode}):\nstderr: {proc.stderr[:2000]}"
        )
    return proc.stdout


def parse_script_json(raw: str) -> VideoScript:
    """LLM の出力から JSON 部分を抜き出して VideoScript にする。"""
    text = raw.strip()
    # よくある形: ```json ... ``` で囲まれている
    if text.startswith("```"):
        # 最初と最後の ``` を除去
        first_nl = text.find("\n")
        text = text[first_nl + 1 :]
        if text.endswith("```"):
            text = text[: -3]
        elif "```" in text:
            text = text.rsplit("```", 1)[0]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        # JSON が混ざっている場合、最初の { から最後の } までを抜く
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError as e2:
                raise ScriptGenerationError(f"JSON parse failed: {e2}") from e
        else:
            raise ScriptGenerationError(f"JSON parse failed: {e}") from e

    return VideoScript.model_validate(data)


def generate_script(
    topic: str,
    *,
    model: str = "claude-opus-4-7",
    template_path: Path | None = None,
    save_to: Path | None = None,
) -> VideoScript:
    prompt = render_prompt(topic, template_path)
    raw = call_claude_cli(prompt, model=model)
    script = parse_script_json(raw)
    if save_to:
        save_to.parent.mkdir(parents=True, exist_ok=True)
        save_to.write_text(
            json.dumps(script.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return script


def load_script(path: Path) -> VideoScript:
    data = json.loads(path.read_text(encoding="utf-8"))
    return VideoScript.model_validate(data)


# CLI ----------------------------------------------------------------

def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="台本を生成して JSON 保存")
    p.add_argument("topic", nargs="?", help="題材")
    p.add_argument("--out", default="output/script.json")
    p.add_argument("--model", default="claude-opus-4-7")
    p.add_argument("--from-prompt-only", action="store_true",
                   help="プロンプトを表示するだけ")
    args = p.parse_args()

    if not args.topic:
        p.error("topic が必要です")
    if args.from_prompt_only:
        print(render_prompt(args.topic))
        return 0
    script = generate_script(args.topic, model=args.model, save_to=Path(args.out))
    print(f"✅ {script.title} を {args.out} に保存しました ({len(script.scenes)} シーン)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
