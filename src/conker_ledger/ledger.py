from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE_SUFFIX_RE = re.compile(r"_\d{4}-\d{2}-\d{2}$")
FULL_EVAL_SUFFIX_RE = re.compile(r"_fullval_(?:train|test)_[a-z0-9]+$")
SEED_RE = re.compile(r"_seed(\d+)")


def _json_default(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def dumps_json(value: Any) -> str:
    return json.dumps(value, indent=2, default=_json_default)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        if math.isfinite(float(value)):
            return float(value)
        return None
    return None


def infer_run_id_from_stem(stem: str) -> str:
    stem = FULL_EVAL_SUFFIX_RE.sub("", stem)
    stem = DATE_SUFFIX_RE.sub("", stem)
    return stem


def infer_family_id(run_id: str) -> str:
    run_id = re.sub(r"_seed\d+", "", run_id)
    run_id = re.sub(r"_save$", "", run_id)
    return run_id


def parse_bridge_record(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    model = data.get("model", {}) if isinstance(data.get("model"), dict) else {}
    quant_rows = data.get("quantization", [])
    saved_state_path = model.get("saved_state_path")
    loaded_state_path = model.get("loaded_state_path")
    run_id = infer_run_id_from_stem(Path(saved_state_path).stem) if saved_state_path else infer_run_id_from_stem(path.stem)
    seed_match = SEED_RE.search(run_id)
    quant_by_bits: dict[str, float | None] = {}
    for row in quant_rows if isinstance(quant_rows, list) else []:
        bits = row.get("bits")
        key = f"int{int(bits)}" if isinstance(bits, (int, float)) else None
        if key:
            quant_by_bits[key] = finite_or_none(row.get("test_bpb"))
    return {
        "kind": "bridge",
        "path": str(path),
        "title": data.get("title"),
        "run_id": run_id,
        "family_id": infer_family_id(run_id),
        "seed": int(seed_match.group(1)) if seed_match else model.get("seed"),
        "bpb": finite_or_none(model.get("test_bpb")),
        "bits_per_token": finite_or_none(model.get("test_bits_per_token")),
        "loss": finite_or_none(model.get("test_eval_loss")),
        "train_time_sec": finite_or_none(model.get("train_time_sec")),
        "params": model.get("params"),
        "saved_state_path": saved_state_path,
        "loaded_state_path": loaded_state_path,
        "int4_bpb": quant_by_bits.get("int4"),
        "int6_bpb": quant_by_bits.get("int6"),
        "raw": {
            "preset": model.get("preset"),
            "variant": model.get("variant"),
            "scale": model.get("scale"),
            "learning_rate": model.get("learning_rate"),
        },
    }


def parse_full_eval_record(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    state_npz = data.get("state_npz")
    run_id = infer_run_id_from_stem(Path(state_npz).stem) if isinstance(state_npz, str) else infer_run_id_from_stem(path.stem)
    seed_match = SEED_RE.search(run_id)
    quant_bits = int(data.get("quant_bits", 0) or 0)
    quant_label = "fp16" if quant_bits == 0 else f"int{quant_bits}"
    artifact_bytes = data.get("artifact_bytes_zlib")
    return {
        "kind": "full_eval",
        "path": str(path),
        "title": data.get("title"),
        "run_id": run_id,
        "family_id": infer_family_id(run_id),
        "seed": int(seed_match.group(1)) if seed_match else None,
        "quant_label": quant_label,
        "quant_bits": quant_bits,
        "bpb": finite_or_none(data.get("eval_bpb")),
        "bits_per_token": finite_or_none(data.get("eval_bits_per_token")),
        "loss": finite_or_none(data.get("eval_loss")),
        "eval_tokens": data.get("eval_tokens"),
        "artifact_bytes": int(artifact_bytes) if isinstance(artifact_bytes, (int, float)) and math.isfinite(float(artifact_bytes)) else None,
        "state_npz": state_npz,
        "summary_json": data.get("summary_json"),
    }


def parse_study_record(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    variants = data.get("variants", [])
    return {
        "kind": "study",
        "path": str(path),
        "title": data.get("title"),
        "run_id": infer_run_id_from_stem(path.stem),
        "family_id": infer_family_id(infer_run_id_from_stem(path.stem)),
        "variant_count": len(variants) if isinstance(variants, list) else 0,
    }


def classify_record(path: Path, data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    if "eval_bpb" in data:
        return parse_full_eval_record(path, data)
    model = data.get("model")
    if isinstance(model, dict) and "test_bpb" in model:
        return parse_bridge_record(path, data)
    if "variants" in data:
        return parse_study_record(path, data)
    return None


def scan_results(root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    skipped: list[str] = []
    for path in sorted(root.glob("*.json")):
        try:
            data = load_json(path)
            record = classify_record(path, data)
        except Exception as exc:  # pragma: no cover - defensive scan path
            skipped.append(f"{path.name}: {exc}")
            continue
        if record is None:
            skipped.append(path.name)
            continue
        records.append(record)

    by_kind = Counter(record["kind"] for record in records)
    by_family = Counter(record["family_id"] for record in records)
    return {
        "root": str(root),
        "record_count": len(records),
        "by_kind": dict(by_kind),
        "family_count": len(by_family),
        "top_families": by_family.most_common(20),
        "records": records,
        "skipped": skipped,
    }


def sort_records(records: list[dict[str, Any]], metric: str, *, ascending: bool = True) -> list[dict[str, Any]]:
    def key_fn(record: dict[str, Any]) -> tuple[int, float]:
        value = record.get(metric)
        if value is None:
            return (1, float("inf"))
        return (0, float(value))

    return sorted(records, key=key_fn, reverse=not ascending)


def survival_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"bridge": None, "full": {}})
    for record in records:
        if record["kind"] == "bridge":
            grouped[record["run_id"]]["bridge"] = record
        elif record["kind"] == "full_eval":
            grouped[record["run_id"]]["full"][record.get("quant_label") or "unknown"] = record

    rows: list[dict[str, Any]] = []
    for run_id, group in sorted(grouped.items()):
        bridge = group["bridge"]
        full = group["full"]
        bridge_bpb = bridge.get("bpb") if bridge else None
        bridge_int6 = bridge.get("int6_bpb") if bridge else None
        full_fp16 = full.get("fp16", {}).get("bpb") if "fp16" in full else None
        full_int6 = full.get("int6", {}).get("bpb") if "int6" in full else None
        status = "bridge_only"
        if full:
            if any(v.get("bpb") is None for v in full.values()):
                status = "full_eval_failed"
            else:
                status = "survived_full_eval"
        rows.append(
            {
                "run_id": run_id,
                "family_id": infer_family_id(run_id),
                "seed": bridge.get("seed") if bridge else None,
                "bridge_fp16": bridge_bpb,
                "bridge_int6": bridge_int6,
                "full_fp16": full_fp16,
                "full_int6": full_int6,
                "delta_fp16": None if bridge_bpb is None or full_fp16 is None else full_fp16 - bridge_bpb,
                "delta_int6": None if bridge_int6 is None or full_int6 is None else full_int6 - bridge_int6,
                "status": status,
                "bridge_path": bridge.get("path") if bridge else None,
                "full_paths": {k: v.get("path") for k, v in full.items()},
            }
        )
    return rows


def lineage_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if record["kind"] != "bridge":
            continue
        loaded = record.get("loaded_state_path")
        saved = record.get("saved_state_path")
        if not loaded or not saved:
            continue
        parent_id = infer_run_id_from_stem(Path(loaded).stem)
        child_id = infer_run_id_from_stem(Path(saved).stem)
        rows.append(
            {
                "parent_run_id": parent_id,
                "child_run_id": child_id,
                "family_id": record["family_id"],
                "seed": record.get("seed"),
                "child_bpb": record.get("bpb"),
                "child_path": record.get("path"),
            }
        )
    return rows


def render_table(rows: list[dict[str, Any]], columns: list[str], top: int | None = None) -> str:
    if top is not None:
        rows = rows[:top]
    if not rows:
        return "(no rows)"
    widths = {col: max(len(col), *(len(str(row.get(col, ""))) for row in rows)) for col in columns}
    header = "  ".join(col.ljust(widths[col]) for col in columns)
    sep = "  ".join("-" * widths[col] for col in columns)
    body = [
        "  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        for row in rows
    ]
    return "\n".join([header, sep, *body])

