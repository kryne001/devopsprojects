import os
import argparse
import json
from pathlib import Path
from collections import defaultdict

def scan_directory(root_path, min_size):
    stats = defaultdict(lambda: {"count": 0, "total_size": 0})
    flagged = []
    
    if min_size is None: 
        LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100 MB
    else:
        LARGE_FILE_THRESHOLD = min_size * 1024 * 1024 

    root = Path(root_path)
    
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root_path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path exists but is not a directory: {root_path}")

    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            try:
                size = filepath.stat().st_size
                ext = filepath.suffix.lower() or "no_extension"
                
                stats[ext]["count"] += 1
                stats[ext]["total_size"] += size

                if size > LARGE_FILE_THRESHOLD:
                    flagged.append({"path": str(filepath), "size_mb": round(size / (1024*1024), 2), "reason": "large_file"})

                # Flag world-writable files -- a real security-relevant check
                mode = filepath.stat().st_mode
                if mode & 0o002:
                    flagged.append({"path": str(filepath), "reason": "world_writable"})

            except (PermissionError, FileNotFoundError):
                continue

    return stats, flagged

def print_summary(stats, flagged):
    print("\n--- File Type Summary ---")
    for ext, data in sorted(stats.items(), key=lambda x: -x[1]["total_size"]):
        size_mb = round(data["total_size"] / (1024*1024), 2)
        print(f"{ext:15} count={data['count']:5}  size={size_mb} MB")

    if flagged:
        print(f"\n--- Flags ({len(flagged)}) ---")
        for item in flagged:
            print(item)
    else:
        print("\nNo flags found.")


def main():
    parser = argparse.ArgumentParser(description="Scan a directory for file stats and security flags")
    parser.add_argument("path", help="Directory to scan")
    parser.add_argument("--output", help="Optional path to write JSON results")
    parser.add_argument("--min-size", type=int, default=None, help = "set large file size threshold")
    args = parser.parse_args()

    try:
        stats, flagged = scan_directory(args.path, args.min_size)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}")
        return

    print_summary(stats, flagged)

    if args.output:
        with open(args.output, "w") as f:
            json.dump({"stats": dict(stats), "flagged": flagged}, f, indent=2)
        print(f"\nResults written to {args.output}")

if __name__ == "__main__":
    main()