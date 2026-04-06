from __future__ import annotations
from typing import Any, Callable, Optional
import re
from errors import ValidationError


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def extract_fields(raw: dict, fields: list[str], strict: bool = False) -> dict:
    result = {}
    for f in fields:
        if f in raw:
            result[f] = raw[f]
        elif strict:
            raise ValidationError(f, "required field missing in record")
    return result


def apply_defaults(data: dict, defaults: dict) -> dict:
    result = dict(defaults)
    result.update({k: v for k, v in data.items() if v is not None})
    return result


def transform_record(record: dict, field_map: dict[str, str] | None = None) -> dict:
    field_map = field_map or {}
    out = {}
    for key, value in record.items():
        new_key = field_map.get(key, key)
        if isinstance(value, str):
            out[new_key] = normalize_text(value)
        else:
            out[new_key] = value
    defaults = {"status": "active", "processed": True}
    return apply_defaults(out, defaults)


def filter_records(records: list[dict], predicate: Callable[[dict], bool]) -> list[dict]:
    return [r for r in records if predicate(r)]


def deduplicate(records: list[dict], key: str) -> list[dict]:
    seen: set = set()
    result = []
    for r in records:
        val = r.get(key)
        if val not in seen:
            seen.add(val)
            result.append(r)
    return result


def merge_records(base: dict, override: dict, deep: bool = False) -> dict:
    result = dict(base)
    for k, v in override.items():
        if deep and isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = merge_records(result[k], v, deep=True)
        else:
            result[k] = v
    return result


def flatten_nested(data: dict, prefix: str = "", sep: str = ".") -> dict:
    result = {}
    for key, value in data.items():
        full_key = f"{prefix}{sep}{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten_nested(value, prefix=full_key, sep=sep))
        else:
            result[full_key] = value
    return result


def batch_transform(
    records: list[dict],
    field_map: dict[str, str] | None = None,
    drop_empty: bool = True,
) -> list[dict]:
    transformed = [transform_record(r, field_map) for r in records]
    if drop_empty:
        transformed = filter_records(transformed, lambda r: len(r) > 0)
    return transformed


def run_pipeline(
    raw_records: list[dict],
    *,
    required_fields: list[str] | None = None,
    field_map: dict[str, str] | None = None,
    dedup_key: Optional[str] = None,
    flatten: bool = False,
) -> list[dict]:
    records = raw_records
    if required_fields:
        records = [extract_fields(r, required_fields) for r in records]
    records = batch_transform(records, field_map=field_map)
    if dedup_key:
        records = deduplicate(records, dedup_key)
    if flatten:
        records = [flatten_nested(r) for r in records]
    return records
