#!/usr/bin/env python3
"""Validate research JSONL structure and provenance, without defining app data."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys


FILES = {
    "sources.jsonl": ("source_id", (
        "url", "publisher", "title", "retrieved_at", "updated_at", "terms",
        "original_path", "original_unavailable_reason", "locator",
    )),
    "observations.jsonl": ("observation_id", (
        "source_id", "locator", "food", "region", "origin", "variety",
        "cultivation", "definition", "raw_season", "period", "transformation",
    )),
    "issues.jsonl": ("issue_id", (
        "kind", "source_ids", "observation_ids", "detail", "status", "resolution",
    )),
}


def present(value):
    return isinstance(value, str) and bool(value.strip())


def reject_constant(value):
    raise ValueError("non-JSON constant " + value)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate object key " + key)
        result[key] = value
    return result


def read_records(path, id_key, fields, errors):
    records = {}
    if not path.is_file():
        errors.append(f"{path}: required file is missing")
        return records
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: {exc}")
        return records
    for number, line in enumerate(lines, 1):
        location = f"{path}:{number}"
        try:
            record = json.loads(line, parse_constant=reject_constant, object_pairs_hook=unique_keys)
        except ValueError as exc:
            errors.append(f"{location}: invalid JSON object: {exc}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{location}: each line must be an object")
            continue
        if type(record.get("schema_version")) is not int or record["schema_version"] != 1:
            errors.append(f"{location}: schema_version must be 1")
        for key in (id_key, *fields):
            if key not in record:
                errors.append(f"{location}: missing {key}; use null for unknown values")
            elif isinstance(record[key], str) and not record[key].strip():
                errors.append(f"{location}: {key} cannot be an empty string")
        identity = record.get(id_key)
        if not present(identity):
            errors.append(f"{location}: {id_key} must be a nonempty string")
        elif identity in records:
            errors.append(f"{location}: duplicate {id_key} {identity}")
        else:
            records[identity] = (record, location)
    return records


def reference(value, records, location, key, errors):
    if not present(value) or value not in records:
        errors.append(f"{location}: {key} references an unknown ID: {value!r}")


def validate_dataset(directory):
    """Return counts and errors. Period values remain opaque to preserve source granularity."""
    directory = Path(directory)
    errors = []
    tables = {
        name: read_records(directory / name, identity, fields, errors)
        for name, (identity, fields) in FILES.items()
    }
    if not (directory / "summary.md").is_file():
        errors.append(f"{directory}: summary.md is missing")
    sources = tables["sources.jsonl"]
    observations = tables["observations.jsonl"]
    issues = tables["issues.jsonl"]
    for record, location in sources.values():
        stamp = record.get("retrieved_at")
        try:
            parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if isinstance(stamp, str) else None
            if parsed is None or parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("timezone is required")
        except ValueError:
            errors.append(f"{location}: retrieved_at must be an ISO 8601 timestamp with timezone")
        original = record.get("original_path")
        reason = record.get("original_unavailable_reason")
        if original is None:
            if not present(reason):
                errors.append(f"{location}: original_unavailable_reason is required when original_path is null")
        elif not present(original):
            errors.append(f"{location}: original_path must be a path string or null")
        else:
            relative = Path(original)
            path = directory / relative
            raw_root = (directory / "raw").resolve()
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "raw":
                errors.append(f"{location}: original_path must stay within raw/")
            elif not raw_root.is_relative_to(directory.resolve()) or not path.resolve().is_relative_to(raw_root) or not path.is_file():
                errors.append(f"{location}: original_path is missing or escapes raw/: {original}")
            if reason is not None:
                errors.append(f"{location}: original_unavailable_reason must be null when the original is saved")
    unknown_observations = set()
    for identity, (record, location) in observations.items():
        reference(record.get("source_id"), sources, location, "source_id", errors)
        if not present(record.get("food")):
            errors.append(f"{location}: food must be a nonempty string")
        if not present(record.get("transformation")):
            errors.append(f"{location}: transformation must describe extraction or preservation")
        if record.get("raw_season") is None:
            unknown_observations.add(identity)
    documented_unknowns = set()
    for record, location in issues.values():
        for key in ("kind", "detail", "status"):
            if not present(record.get(key)):
                errors.append(f"{location}: {key} must be a nonempty string")
        for key, target in (("source_ids", sources), ("observation_ids", observations)):
            values = record.get(key)
            if not isinstance(values, list):
                errors.append(f"{location}: {key} must be an array of IDs")
                continue
            for value in values:
                reference(value, target, location, key, errors)
                if key == "observation_ids" and present(value):
                    documented_unknowns.add(value)
    for identity in sorted(unknown_observations - documented_unknowns):
        errors.append(f"{observations[identity][1]}: null raw_season must be documented in issues.jsonl")
    return {name: len(records) for name, records in tables.items()}, errors


def discover(root):
    """Inspect only Git-visible files; generated results and raw source JSON are not datasets."""
    output = subprocess.check_output([
        "git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z",
    ])
    paths = {Path(os.fsdecode(p)) for p in output.split(b"\0") if p}
    paths = {p for p in paths if (root / p).is_file()}
    datasets = sorted({(root / p.parent).resolve() for p in paths if p.name in FILES and "raw" not in p.parts})
    unsupported = []
    for path in sorted(paths):
        if path.suffix not in (".json", ".jsonl"):
            continue
        if path.is_relative_to(Path("app/src/main/assets")):
            unsupported.append(f"{path}: bundled app data schema is not defined; validation is unsupported")
        elif path.suffix == ".jsonl" and path.name not in FILES and "raw" not in path.parts:
            unsupported.append(f"{path}: unrecognized research JSONL; specify an agreed data contract")
    return datasets, unsupported


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", nargs="*", type=Path, help="Research directories; default discovers Git-visible JSONL")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        datasets, errors = (args.datasets, []) if args.datasets else discover(root)
        checked = []
        for directory in datasets:
            counts, failures = validate_dataset(directory)
            checked.append({"directory": str(directory), "counts": counts})
            errors.extend(failures)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    result = {
        "status": "failed" if errors else "passed" if checked else "no_datasets",
        "datasets": checked,
        "errors": errors,
        "scope": "Research structure and references only; source fidelity, summary counts, and app image contracts require review.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
