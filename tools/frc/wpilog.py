"""Read WPILOG 1.x without external dependencies.

Format reference: https://github.com/wpilibsuite/allwpilib/blob/main/datalog/doc/datalog.adoc
Only standard primitive types are decoded. Struct/protobuf/raw data stays opaque.
"""

from __future__ import annotations

import fnmatch
import hashlib
import heapq
import math
import struct
from pathlib import Path


class LogError(ValueError):
    pass


class TruncatedReadError(LogError):
    pass


def _read(stream, size):
    data = stream.read(size)
    if len(data) != size:
        raise TruncatedReadError(f"Truncated log at byte {stream.tell()}: expected {size} bytes")
    return data


def _string(data, offset):
    if offset + 4 > len(data):
        raise LogError("Truncated string length")
    size = int.from_bytes(data[offset:offset + 4], "little")
    end = offset + 4 + size
    if end > len(data):
        raise LogError("Truncated string payload")
    try:
        return data[offset + 4:end].decode("utf-8"), end
    except UnicodeDecodeError as exc:
        raise LogError("Invalid UTF-8 string") from exc


def decode(kind, data):
    scalar = {"int64": ("q", 8), "float": ("f", 4), "double": ("d", 8)}
    if kind == "boolean":
        if len(data) != 1 or data[0] not in (0, 1):
            raise LogError("Invalid boolean payload")
        return bool(data[0])
    if kind in scalar:
        fmt, size = scalar[kind]
        if len(data) != size:
            raise LogError(f"Invalid {kind} payload length")
        return struct.unpack("<" + fmt, data)[0]
    if kind == "string":
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LogError("Invalid UTF-8 data") from exc
    if kind == "boolean[]":
        if any(value not in (0, 1) for value in data):
            raise LogError("Invalid boolean array payload")
        return [bool(value) for value in data]
    if kind.endswith("[]") and kind[:-2] in scalar:
        fmt, size = scalar[kind[:-2]]
        if len(data) % size:
            raise LogError(f"Invalid {kind} payload length")
        return [item[0] for item in struct.iter_unpack("<" + fmt, data)]
    if kind == "string[]":
        if len(data) < 4:
            raise LogError("Truncated string array")
        count = int.from_bytes(data[:4], "little")
        if count > (len(data) - 4) // 4:
            raise LogError("Invalid string array count")
        values, offset = [], 4
        for _ in range(count):
            value, offset = _string(data, offset)
            values.append(value)
        if offset != len(data):
            raise LogError("Unexpected trailing string array bytes")
        return values
    return {"decoded": False, "type": kind, "bytes": len(data), "preview_hex": data[:32].hex(),
            "sha256": hashlib.sha256(data).hexdigest()}


def _finite_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, list):
        return [_finite_json(item) for item in value]
    return value


def records(path, *, allow_truncated=False, diagnostics=None):
    """Yield (timestamp_us, entry_definition, data). Controls are applied in file order."""
    active, generations = {}, {}
    with Path(path).open("rb") as stream:
        if _read(stream, 6) != b"WPILOG":
            raise LogError("Not a WPILOG file")
        version = int.from_bytes(_read(stream, 2), "little")
        if version >> 8 != 1:
            raise LogError(f"Unsupported WPILOG version 0x{version:04x}")
        size = int.from_bytes(_read(stream, 4), "little")
        if size > 64 * 1024 * 1024:
            raise LogError("Extra header exceeds 64 MiB reader limit")
        _read(stream, size)
        while True:
            first = stream.read(1)
            if not first:
                return
            try:
                flags = first[0]
                if flags & 0x80:
                    raise LogError("Reserved record-header bit set")
                entry_id = int.from_bytes(_read(stream, (flags & 3) + 1), "little")
                size = int.from_bytes(_read(stream, ((flags >> 2) & 3) + 1), "little")
                timestamp = int.from_bytes(_read(stream, ((flags >> 4) & 7) + 1), "little")
                if size > 64 * 1024 * 1024:
                    raise LogError("Record exceeds 64 MiB reader limit")
                data = _read(stream, size)
            except TruncatedReadError as exc:
                if not allow_truncated:
                    raise
                if diagnostics is not None:
                    diagnostics.append(str(exc) + "; only the intact prefix was analyzed")
                return
            if entry_id:
                if entry_id not in active:
                    raise LogError(f"Data for inactive entry {entry_id}")
                yield timestamp, active[entry_id], data
                continue
            if len(data) < 5:
                raise LogError("Truncated control record")
            control, target = data[0], int.from_bytes(data[1:5], "little")
            if control == 0:
                if not target or target in active:
                    raise LogError(f"Invalid or already active entry {target}")
                name, offset = _string(data, 5)
                kind, offset = _string(data, offset)
                metadata, offset = _string(data, offset)
                if offset != len(data):
                    raise LogError("Unexpected trailing start record bytes")
                generations[target] = generations.get(target, 0) + 1
                definition = {"id": target, "generation": generations[target],
                              "name": name, "type": kind, "metadata": metadata}
                active[target] = definition
                yield timestamp, definition, None
            elif control == 1:
                if len(data) != 5 or target not in active:
                    raise LogError("Invalid finish control")
                del active[target]
            elif control == 2:
                metadata, offset = _string(data, 5)
                if target not in active or offset != len(data):
                    raise LogError("Invalid metadata control")
                # Copy so historical entry definitions are not mutated retroactively.
                active[target] = dict(active[target], metadata=metadata)
            else:
                raise LogError(f"Unknown control record type {control}")


def _percentile(values, quantile):
    position = (len(values) - 1) * quantile
    lo = int(position)
    hi = min(lo + 1, len(values) - 1)
    fraction = position - lo
    return values[lo] * (1 - fraction) + values[hi] * fraction


def inspect_log(path, *, patterns=(), list_only=False, match="*", start=None, end=None,
                limit=2000, changes=False, stats=False, max_values=200000, allow_truncated=False):
    """Stream a log; retain bounded chronological output and bounded percentile values."""
    if limit < 1 or limit > 100000 or max_values < 1 or max_values > 1000000:
        raise LogError("limit must be 1..100000 and max-values 1..1000000")
    for bound in (start, end):
        if bound is not None and (not math.isfinite(bound) or bound < 0):
            raise LogError("Time bounds must be finite nonnegative log seconds")
    if start is not None and end is not None and end < start:
        raise LogError("end must be at least start")
    if not list_only and not patterns:
        raise LogError("Select signals explicitly, or use --list")
    entries, numeric, initial, heap = {}, {}, {}, []
    matched = set()
    selected_count = 0
    first_time, last_time = None, None
    diagnostics = []
    for sequence, (timestamp, entry, payload) in enumerate(records(path, allow_truncated=allow_truncated, diagnostics=diagnostics)):
        key = (entry["id"], entry["generation"])
        seconds = timestamp / 1e6
        if key not in entries:
            entries[key] = dict(entry, samples=0, first_timestamp=None, last_timestamp=None)
        else:
            entries[key]["metadata"] = entry["metadata"]
        if payload is None:
            continue
        item = entries[key]
        item["samples"] += 1
        item["first_timestamp"] = seconds if item["first_timestamp"] is None else min(item["first_timestamp"], seconds)
        item["last_timestamp"] = seconds if item["last_timestamp"] is None else max(item["last_timestamp"], seconds)
        first_time = seconds if first_time is None else min(first_time, seconds)
        last_time = seconds if last_time is None else max(last_time, seconds)
        if list_only:
            continue
        selectors = [pattern for pattern in patterns if fnmatch.fnmatchcase(entry["name"], pattern)]
        matched.update(selectors)
        if not selectors or (end is not None and seconds > end):
            continue
        value = decode(entry["type"], payload)
        row = {"timestamp": seconds, "id": entry["id"], "generation": entry["generation"],
               "name": entry["name"], "value": _finite_json(value)}
        if start is not None and seconds < start:
            if key not in initial or seconds >= initial[key]["timestamp"]:
                initial[key] = row
            continue
        selected_count += 1
        if stats:
            state = numeric.setdefault(key, {"samples": 0, "finite_samples": 0, "nonfinite_samples": 0,
                                              "min": None, "max": None, "mean": 0.0, "values": []})
            state["samples"] += 1
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if math.isfinite(value):
                    state["finite_samples"] += 1
                    state["min"] = value if state["min"] is None else min(state["min"], value)
                    state["max"] = value if state["max"] is None else max(state["max"], value)
                    weight = 1 / state["finite_samples"]
                    state["mean"] = state["mean"] * (1 - weight) + value * weight
                    if len(state["values"]) < max_values:
                        state["values"].append(value)
                else:
                    state["nonfinite_samples"] += 1
            continue
        # Keep the earliest N samples by timestamp, not the first N in file order.
        candidate = (-timestamp, -sequence, row)
        if len(heap) < limit:
            heapq.heappush(heap, candidate)
        elif candidate[:2] > heap[0][:2]:
            heapq.heapreplace(heap, candidate)
    catalog = sorted(entries.values(), key=lambda item: (item["name"], item["id"], item["generation"]))
    # Selectors match declared entries even when they have no samples.
    for item in catalog:
        matched.update(pattern for pattern in patterns if fnmatch.fnmatchcase(item["name"], pattern))
    result = {"path": str(Path(path).resolve()), "complete": not diagnostics, "warnings": diagnostics,
              "selector_interpretation": "Missing selectors were not observed in the intact prefix" if diagnostics else "Missing selectors were not declared in this file",
              "time_unit": "seconds since log clock origin (not window-relative)",
              "log_first_timestamp": first_time, "log_last_timestamp": last_time,
              "window": {"start": start, "end": end}, "missing_selectors": [p for p in patterns if p not in matched]}
    if list_only:
        catalog = [item for item in catalog if fnmatch.fnmatchcase(item["name"], match)]
        result.update(entries=catalog[:limit], total_entries=len(catalog), truncated=len(catalog) > limit)
        return result
    selected = [item for item in catalog if any(fnmatch.fnmatchcase(item["name"], p) for p in patterns)]
    result.update(selected_entries=selected, samples_in_window=selected_count,
                  initial_values=sorted(initial.values(), key=lambda row: (row["name"], row["id"], row["generation"])))
    if stats:
        summaries = []
        for item in selected:
            key = (item["id"], item["generation"])
            state = numeric.get(key)
            summary = dict(item, window_samples=state["samples"] if state else 0)
            if state and state["finite_samples"]:
                values = sorted(state["values"])
                summary["numeric"] = {k: state[k] for k in ("finite_samples", "nonfinite_samples", "min", "max", "mean")}
                summary["numeric"].update(p50=_percentile(values, .5), p95=_percentile(values, .95),
                                           p99=_percentile(values, .99), percentile_samples=len(values),
                                           percentiles_exact=len(values) == state["finite_samples"])
            else:
                summary["numeric"] = None
                summary["nonfinite_samples"] = state["nonfinite_samples"] if state else 0
            summaries.append(summary)
        result.update(statistics=summaries, weighting="sample weighted; percentiles use first max-values finite samples in file order when capped")
    else:
        rows = [item[2] for item in sorted(heap, key=lambda item: (-item[0], -item[1]))]
        if changes:
            previous = {key: row["value"] for key, row in initial.items()}
            changed_rows = []
            for row in rows:
                key = (row["id"], row["generation"])
                if key not in previous or previous[key] != row["value"]:
                    changed_rows.append(row)
                previous[key] = row["value"]
            rows = changed_rows
        result.update(samples=rows, truncated=selected_count > limit,
                      limit_applies_to="earliest selected samples before change filtering")
    return result
