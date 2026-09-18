from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


class IsolationPromptError(RuntimeError):
    pass


def load_yaml(path: str | Path) -> dict[str, Any]:
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise IsolationPromptError("prompt YAML must be an object")
    return value


def parse_values(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise IsolationPromptError(f"expected KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        if not key:
            raise IsolationPromptError("empty variable key")
        out[key] = value
    return out


def render(
    prompt_path: str,
    variables: dict[str, str],
    file_variables: dict[str, str],
) -> str:
    prompt = load_yaml(prompt_path)
    values = dict(variables)
    for key, path in file_variables.items():
        values[key] = Path(path).read_text(encoding="utf-8")

    messages = prompt.get("messages")
    if not isinstance(messages, list) or not messages:
        raise IsolationPromptError("prompt YAML requires messages")

    rendered: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            raise IsolationPromptError("message must be object")
        role = str(message.get("role", "")).strip().upper()
        body = str(message.get("content", ""))
        for key, value in values.items():
            body = body.replace("{{" + key + "}}", value)
        unresolved = re.findall(r"\{\{[^{}]+\}\}", body)
        if unresolved:
            raise IsolationPromptError(
                f"unresolved prompt variables: {unresolved}"
            )
        rendered.append(f"## {role}\n\n{body.strip()}")

    schema = prompt.get("jsonSchema")
    if schema:
        rendered.append(
            "## OUTPUT CONTRACT\n\n"
            "Return exactly one JSON object. Do not use Markdown fences, "
            "commentary, or text before/after the JSON. The required JSON "
            "schema is:\n\n"
            + str(schema).strip()
        )

    return "\n\n".join(rendered) + "\n"


def _parse_json_envelope(raw: str) -> dict[str, Any]:
    attempts = [raw]
    if raw.count("{") == raw.count("}") + 1:
        attempts.append(raw + "}")

    parsed: Any = None
    last_error: json.JSONDecodeError | None = None
    for attempt in attempts:
        try:
            parsed = json.loads(attempt)
            break
        except json.JSONDecodeError as error:
            last_error = error

    if parsed is None:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            fragment = raw[start : end + 1]
            fragments = [fragment]
            if fragment.count("{") == fragment.count("}") + 1:
                fragments.append(fragment + "}")
            for attempt in fragments:
                try:
                    parsed = json.loads(attempt)
                    break
                except json.JSONDecodeError as error:
                    last_error = error

    if parsed is None:
        raise IsolationPromptError(
            f"Copilot response is not mechanically recoverable JSON: "
            f"{last_error}"
        ) from None
    if not isinstance(parsed, dict):
        raise IsolationPromptError(
            "Copilot JSON output must be an object"
        )

    embedded_schema = parsed.get("schema")
    if isinstance(embedded_schema, dict):
        properties = embedded_schema.get("properties")
        if isinstance(properties, dict):
            nested_values = {
                key: embedded_schema[key]
                for key in properties
                if key in embedded_schema
                and key not in {"required", "additionalProperties"}
            }
            if nested_values:
                return nested_values

        required = embedded_schema.get("required")
        if (
            isinstance(required, list)
            and required
            and all(isinstance(key, str) for key in required)
            and all(key in parsed for key in required)
        ):
            return {key: parsed[key] for key in required}

    return parsed


def extract_json(raw_path: str, out_path: str) -> None:
    raw = Path(raw_path).read_text(encoding="utf-8").strip()
    fence = chr(96) * 3
    if raw.startswith(fence):
        lines = raw.splitlines()
        if lines and lines[0].startswith(fence):
            lines = lines[1:]
        if lines and lines[-1].strip() == fence:
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    value = _parse_json_envelope(raw)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("render")
    p.add_argument("--prompt", required=True)
    p.add_argument("--var", action="append", default=[])
    p.add_argument("--file-var", action="append", default=[])
    p.add_argument("--out", required=True)

    p = sub.add_parser("extract-json")
    p.add_argument("--raw", required=True)
    p.add_argument("--out", required=True)

    args = parser.parse_args()

    if args.command == "render":
        text = render(
            args.prompt,
            parse_values(args.var),
            parse_values(args.file_var),
        )
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        extract_json(args.raw, args.out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
