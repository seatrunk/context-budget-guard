"""Validate a sanitized single-phase benchmark report, not a runtime or savings claim."""
import argparse
from datetime import date
import json
import math
from pathlib import Path
import re
import sys

ROOT_KEYS = {"schema_version", "recorded_on", "guard_enabled", "synthetic", "scope", "samples_per_case",
             "model", "provider", "prototype", "billing", "measurements", "limitations"}
ROW_KEYS = {"case", "wall_seconds", "tool_content_utf8_bytes", "input_tokens", "cache_read_tokens",
            "output_tokens", "api_calls", "tool_calls"}
CASES = {"small", "over_lines", "over_result"}
PRIVATE = re.compile(r"(?:/(?:home|Users)/[^/\s]+|[A-Za-z]:[\\/]Users[\\/]|\bgh[pousr]_[A-Za-z0-9]{20,}|\bsk-[A-Za-z0-9_-]{20,})")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact_keys(value, expected, label):
    require(isinstance(value, dict) and set(value) == expected, f"{label} has missing or unknown fields")


def number(value, label, integer=False):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            f"{label} must be finite and nonnegative, not boolean")
    if integer:
        require(type(value) is int, f"{label} must be an integer")


def safe_strings(value):
    if isinstance(value, str):
        require(not PRIVATE.search(value), "private-path or credential-shaped text detected; sanitize before publishing")
    elif isinstance(value, dict):
        for key, item in value.items():
            safe_strings(key)
            safe_strings(item)
    elif isinstance(value, list):
        for item in value:
            safe_strings(item)


def validate_report(data):
    safe_strings(data)
    exact_keys(data, ROOT_KEYS, "report")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1, "unsupported schema version")
    require(isinstance(data["recorded_on"], str), "recorded_on must be an ISO date")
    try:
        date.fromisoformat(data["recorded_on"])
    except ValueError:
        raise ValueError("recorded_on must be an ISO date") from None
    require(type(data["guard_enabled"]) is bool and data["synthetic"] is True, "phase must be explicit and fixtures synthetic")
    require(data["scope"] in {"installed-cli", "desktop-managed"}, "unsupported measurement scope")
    number(data["samples_per_case"], "samples_per_case", integer=True)
    require(data["samples_per_case"] == 1, "schema 1 records one observation per case; repetitions need separate reports")
    for key in ("model", "provider"):
        require(isinstance(data[key], str) and bool(data[key].strip()), f"{key} must be nonempty")
    prototype = data["prototype"]
    exact_keys(prototype, {"base_commit", "patch_sha256", "review_status", "desktop_loaded_provenance_verified"}, "prototype")
    for key, length in (("base_commit", 40), ("patch_sha256", 64)):
        require(isinstance(prototype[key], str) and re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", prototype[key]),
                f"prototype.{key} has invalid fingerprint format")
    require(prototype["review_status"] in {"approved", "rejected", "pending"}, "unknown review status")
    require(type(prototype["desktop_loaded_provenance_verified"]) is bool, "provenance verification must be boolean")
    if data["guard_enabled"]:
        require(prototype["review_status"] == "approved", "enabled observations require an approved candidate")
    if data["scope"] == "desktop-managed":
        require(prototype["desktop_loaded_provenance_verified"], "Desktop measurements require loaded-source proof")
    billing = data["billing"]
    exact_keys(billing, {"mode", "actual_cost_usd"}, "billing")
    require(billing["mode"] in {"subscription_included", "metered", "unknown"}, "unknown billing mode")
    if billing["actual_cost_usd"] is not None:
        number(billing["actual_cost_usd"], "actual_cost_usd")
    measurements = data["measurements"]
    require(isinstance(measurements, list) and len(measurements) == 3, "exactly three observations required")
    seen = set()
    for index, row in enumerate(measurements):
        label = f"measurement {index}"
        exact_keys(row, ROW_KEYS, label)
        require(isinstance(row["case"], str) and row["case"] in CASES and row["case"] not in seen,
                "duplicate or unknown case")
        seen.add(row["case"])
        for key in ROW_KEYS - {"case"}:
            number(row[key], label + "." + key, integer=key != "wall_seconds")
        require(row["cache_read_tokens"] <= row["input_tokens"], "cached input cannot exceed total input")
        require(row["tool_calls"] == 1 and row["api_calls"] >= 1, "single-tool observation contract violated")
    require(isinstance(data["limitations"], list) and bool(data["limitations"])
            and all(isinstance(item, str) and item.strip() for item in data["limitations"]),
            "limitations must contain nonempty text")


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "invalid arguments; use --help for usage\n")


def main():
    parser = SafeArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        with args.report.open(encoding="utf-8") as stream:
            data = json.load(stream)
        validate_report(data)
    except (OSError, ValueError, TypeError, OverflowError, RecursionError):
        # Do not echo a possibly secret-bearing payload or exception value.
        print("invalid benchmark: schema, privacy, or measurement contract rejected; inspect locally", file=sys.stderr)
        return 2
    print("valid sanitized single-phase report; this does not prove enforcement or savings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
