#!/usr/bin/env python3
"""PreToolUse hook for file tools: protect secret files and block credential writes.

- Denies Read/Edit/Write/NotebookEdit/Grep/Glob on secret paths, including
  `.env.*` variants that permission rules cannot express (examples are allowed).
- Denies writes whose new content contains a high-confidence credential format.
  The reason names the kind of credential, never the value.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hook_lib import decide, find_secret_content, read_event, secret_reference  # noqa: E402

PATH_FIELDS = ("file_path", "notebook_path", "path", "glob")


def new_content(tool_input: dict[str, Any]) -> str:
    parts = [tool_input.get(key) for key in ("content", "new_string", "new_source")]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            parts.append(edit.get("new_string"))
    return "\n".join(p for p in parts if isinstance(p, str))


def main() -> int:
    event = read_event()
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    for field in PATH_FIELDS:
        value = tool_input.get(field)
        if isinstance(value, str) and secret_reference(value):
            decide("PreToolUse", "deny",
                   "Access to secret files is blocked by project policy; "
                   "use .env.example for documented placeholders.")
    kind = find_secret_content(new_content(tool_input))
    if kind:
        decide("PreToolUse", "deny",
               f"The new content appears to contain a real {kind}. Use a placeholder and "
               "keep real values in git-ignored .env files or a secrets manager.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
