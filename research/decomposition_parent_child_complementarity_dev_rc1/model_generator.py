from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_SPECS = {
    "flan": {
        "model": "google/flan-t5-small",
        "revision": "14fd6edcfdd71f2ef5b67d4e735fee8bc6d9fd31",
        "architecture": "seq2seq",
        "strategies": ("D3", "D5a"),
    },
    "smol": {
        "model": "HuggingFaceTB/SmolLM2-360M-Instruct",
        "revision": "a10cc1512eabd3dde888204e902eca88bddb4951",
        "architecture": "causal",
        "strategies": ("D4", "D5b"),
    },
}

PROMPTS = {
    "D3": """You are producing a retrieval-oriented decomposition of one proposition. Return ONLY a JSON array of 2 to 4 strings. The strings must be jointly equivalent to the exact root proposition, independently auditable, and useful as retrieval queries. Preserve every number, date, temporal condition, negation, modal/deontic force, exception, condition, named entity and population/scope restriction. Do not add facts that are not in the root. If you cannot safely decompose, return [].""",
    "D4": """You are producing a typed-semantic decomposition of one proposition. Return ONLY a JSON array of 2 to 4 proposition strings. Prefer boundaries corresponding to condition/exception, temporal scope, numeric/qualifier, modal/deontic force, and entity/population scope, but the conjunction must preserve the exact root meaning. Preserve every number, date, negation, modality, condition, exception and scope restriction. Do not add facts that are not in the root. If no safe decomposition exists, return [].""",
    "D5a": """Independently decompose the exact root proposition into 2 to 4 jointly necessary, independently auditable propositions. Return ONLY a JSON array of strings. The conjunction must neither add nor remove meaning. Preserve all scope, negation, numbers, dates, modality, conditions and exceptions. Do not add facts that are not in the root. If you cannot safely do this, return [].""",
    "D5b": """Independently decompose the exact root proposition into 2 to 4 jointly necessary, independently auditable propositions. Return ONLY a JSON array of strings. The conjunction must neither add nor remove meaning. Preserve all scope, negation, numbers, dates, modality, conditions and exceptions. Do not add facts that are not in the root. If you cannot safely do this, return [].""",
}


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _case_prompt(case: dict[str, Any], strategy: str) -> str:
    return (
        f"{PROMPTS[strategy]}\n\n"
        f"EXACT ROOT:\n{case['root_proposition']['text']}\n\n"
        "SOURCE-EXPOSURE POLICY:\n"
        "The full source aperture is frozen in the experiment input and later Contract A "
        "fixtures, but source bodies are intentionally not available to this decomposition "
        "generator. Derive child propositions only from the exact root above.\n"
    )


def _clean_child(value: str) -> str:
    text = " ".join(value.strip().split())
    text = re.sub(r"^(?:[-*]|\d+[.)])\s*", "", text)
    return text.strip()


def _parse_children(generated: str) -> tuple[list[str], str | None]:
    text = generated.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            return [], "NON_JSON_OUTPUT"
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return [], "NON_JSON_OUTPUT"
    if not isinstance(parsed, list):
        return [], "OUTPUT_NOT_ARRAY"
    if not all(isinstance(value, str) for value in parsed):
        return [], "NON_STRING_CHILD"
    children = [_clean_child(value) for value in parsed]
    children = [value for value in children if value]
    if not 2 <= len(children) <= 4:
        return [], "CHILD_COUNT_OUT_OF_RANGE"
    if len(children) != len(set(children)):
        return [], "DUPLICATE_CHILD_TEXT"
    return children, None


def _model_context_limit(tokenizer: Any) -> int:
    limit = int(getattr(tokenizer, "model_max_length", 0) or 0)
    if limit <= 0 or limit > 100_000:
        return 4096
    return limit


def _generate_seq2seq(model: Any, tokenizer: Any, prompt: str) -> tuple[str, int, int]:
    tokenized = tokenizer(prompt, return_tensors="pt", truncation=False)
    input_tokens = int(tokenized["input_ids"].shape[1])
    limit = _model_context_limit(tokenizer)
    if input_tokens > limit:
        raise ValueError(f"INPUT_EXCEEDS_MODEL_CONTEXT:{input_tokens}>{limit}")
    with torch.no_grad():
        output = model.generate(
            **tokenized,
            do_sample=False,
            max_new_tokens=192,
            num_beams=1,
        )
    return tokenizer.decode(output[0], skip_special_tokens=True), input_tokens, limit


def _generate_causal(model: Any, tokenizer: Any, prompt: str) -> tuple[str, int, int]:
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        rendered = prompt
    tokenized = tokenizer(rendered, return_tensors="pt", truncation=False)
    input_tokens = int(tokenized["input_ids"].shape[1])
    limit = _model_context_limit(tokenizer)
    if input_tokens > limit:
        raise ValueError(f"INPUT_EXCEEDS_MODEL_CONTEXT:{input_tokens}>{limit}")
    with torch.no_grad():
        output = model.generate(
            **tokenized,
            do_sample=False,
            max_new_tokens=192,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated_ids = output[0, input_tokens:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True), input_tokens, limit


def generate(*, input_path: Path, model_key: str, output: Path) -> dict[str, Any]:
    if model_key not in MODEL_SPECS:
        raise ValueError(f"unknown model key: {model_key}")
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    spec = MODEL_SPECS[model_key]

    torch.manual_seed(0)
    tokenizer = AutoTokenizer.from_pretrained(
        spec["model"], revision=spec["revision"], trust_remote_code=False
    )
    if spec["architecture"] == "seq2seq":
        model = AutoModelForSeq2SeqLM.from_pretrained(
            spec["model"], revision=spec["revision"], trust_remote_code=False
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            spec["model"], revision=spec["revision"], trust_remote_code=False
        )
    model.eval()

    rows: list[dict[str, Any]] = []
    for case in payload["cases"]:
        for strategy in spec["strategies"]:
            prompt = _case_prompt(case, strategy)
            prompt_sha = sha256_bytes(prompt.encode("utf-8"))
            try:
                if spec["architecture"] == "seq2seq":
                    generated, input_tokens, context_limit = _generate_seq2seq(
                        model, tokenizer, prompt
                    )
                else:
                    generated, input_tokens, context_limit = _generate_causal(
                        model, tokenizer, prompt
                    )
                children, parse_error = _parse_children(generated)
                status = "declared" if parse_error is None else "failed"
                reason = parse_error
            except (ValueError, RuntimeError) as exc:
                generated = ""
                children = []
                status = "failed"
                reason = str(exc)
                raw_tokens = tokenizer(prompt, return_tensors="pt", truncation=False)["input_ids"]
                input_tokens = int(raw_tokens.shape[1])
                context_limit = _model_context_limit(tokenizer)
            rows.append(
                {
                    "original_claim_id": case["original_claim_id"],
                    "strategy": strategy,
                    "status": status,
                    "failure_reason": reason,
                    "children": children,
                    "raw_generation": generated,
                    "prompt_sha256": prompt_sha,
                    "input_tokens": input_tokens,
                    "model_context_limit": context_limit,
                    "generator_source_exposure": "exact_root_only",
                    "source_aperture_sha256": case["source_aperture_sha256"],
                }
            )

    result = {
        "schema_version": "1.0",
        "experiment": payload["experiment"],
        "generation_input_sha256": sha256_bytes(input_path.read_bytes()),
        "model_key": model_key,
        "model": spec["model"],
        "revision": spec["revision"],
        "architecture": spec["architecture"],
        "do_sample": False,
        "torch_seed": 0,
        "generator_source_exposure": "exact_root_only",
        "generation_input_source_arrays_frozen_but_not_consumed": True,
        "strategies": list(spec["strategies"]),
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    return {
        "model": spec["model"],
        "revision": spec["revision"],
        "row_count": len(rows),
        "declared_count": sum(row["status"] == "declared" for row in rows),
        "failed_count": sum(row["status"] == "failed" for row in rows),
        "generator_source_exposure": "exact_root_only",
        "output_sha256": sha256_bytes(output.read_bytes()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model-key", choices=sorted(MODEL_SPECS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = generate(input_path=args.input, model_key=args.model_key, output=args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
