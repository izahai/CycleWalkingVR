import sys

from polarUtils import (
    load_positions, choose_random_points,
    centroid, visualize_points
)

DEFAULT_PATH = "sphere_positions.json"
DEFAULT_SAMPLE_COUNT = 100


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    sample_count = DEFAULT_SAMPLE_COUNT
    if len(sys.argv) > 2:
        sample_count = max(1, int(sys.argv[2]))
    show = "--show" in sys.argv[1:]

    positions = load_positions(path)
    if not positions:
        raise SystemExit("No valid positions found in JSON.")

    samples = choose_random_points(positions, sample_count)
    center = centroid(samples)
    if center is None:
        raise SystemExit("Could not compute centroid.")

    print(f"Samples used: {len(samples)} / {len(positions)}")
    print(f"Centroid: x={center[0]:.6f}, y={center[1]:.6f}, z={center[2]:.6f}")
    if show:
        visualize_points(samples, center)


if __name__ == "__main__":
    main()
