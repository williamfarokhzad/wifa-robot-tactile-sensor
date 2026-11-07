"""Estimate total normal load and its center on a synthetic flat taxel pad."""
import argparse
import json
import math
from pathlib import Path


def numeric(value, label, *, positive=True):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    value = float(value)
    if not math.isfinite(value) or (value <= 0 if positive else value < 0):
        raise ValueError(f"{label} must be finite and {'positive' if positive else 'nonnegative'}")
    return value


def grid(data, label, shape=None):
    if not isinstance(data, list) or not data or not isinstance(data[0], list) or not data[0]:
        raise ValueError(f"{label} must be a nonempty grid")
    height, width = len(data), len(data[0])
    if shape is not None and shape != (height, width):
        raise ValueError(f"{label} must have {shape[0]} rows and {shape[1]} columns")
    if any(not isinstance(row, list) or len(row) != width for row in data):
        raise ValueError(f"{label} must be rectangular")
    return height, width


def raw_counts(data, label, shape, maximum):
    grid(data, label, shape)
    for row in data:
        if any(type(v) is not int or not 0 <= v <= maximum for v in row):
            raise ValueError(f"{label} must contain integer counts from 0 to {maximum}")
    return data


def estimate(config):
    pitch = numeric(config["pitch_mm"], "pitch_mm")
    deadband = numeric(config["deadband_counts"], "deadband_counts", positive=False)
    minimum = numeric(config["minimum_load_n"], "minimum_load_n")
    maximum = config["adc_max"]
    if type(maximum) is not int or maximum < 2:
        raise ValueError("adc_max must be an integer of at least 2")
    gain = config["counts_per_newton"]
    height, width = shape = grid(gain, "counts_per_newton")
    gain = [[numeric(v, "counts_per_newton") for v in row] for row in gain]
    samples = config["unloaded_frames"]
    if not isinstance(samples, list) or len(samples) < 2:
        raise ValueError("provide at least two unloaded frames")
    for frame in samples:
        raw_counts(frame, "unloaded frame", shape, maximum)
        if any(v in (0, maximum) for row in frame for v in row):
            raise ValueError("unloaded frame has a value at an ADC rail")
    frame = raw_counts(config["frame"], "frame", shape, maximum)
    clipped = [[r, c] for r, row in enumerate(frame) for c, v in enumerate(row) if v in (0, maximum)]
    if clipped:
        return dict(status="clipped", clipped_row_col=clipped, force_n=None,
                    center_mm=None, taxel_forces_n=None)
    loads = []
    for r in range(height):
        row = []
        for c in range(width):
            baseline = math.fsum(s[r][c] for s in samples) / len(samples)
            delta = frame[r][c] - baseline
            row.append(delta / gain[r][c] if delta > deadband else 0.0)
        loads.append(row)
    total = math.fsum(v for row in loads for v in row)
    if not math.isfinite(total):
        raise ValueError("calibrated total must be finite")
    active = total >= minimum
    center = None
    if active:
        # Divide each weight before multiplying by its position.
        center = [math.fsum(v / total * (c * pitch) for row in loads for c, v in enumerate(row)),
                  math.fsum(v / total * (r * pitch) for r, row in enumerate(loads) for v in row)]
        if not all(map(math.isfinite, center)):
            raise ValueError("calibrated center must be finite")
    return dict(status="contact" if active else "below_threshold", clipped_row_col=[],
                force_n=total, center_mm=center, taxel_forces_n=loads)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON pad configuration and sample")
    args = parser.parse_args()
    try:
        config = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("the JSON root must be an object")
        result = estimate(config)
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        parser.exit(2, f"input error: {exc}\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
