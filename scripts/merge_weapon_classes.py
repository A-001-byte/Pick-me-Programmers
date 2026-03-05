"""
merge_weapon_classes.py
───────────────────────
Preprocesses a YOLO weapon-detection dataset by merging multiple gun-related
classes into a single "gun" class.  The original dataset is preserved; a new
copy is written to  datasets/weapon_merged/.

Original classes (indices from data.yaml):
    0: Gunmen   1: Rifle       2: blunt_object  3: knife
    4: knife_attacker  5: person  6: pistol  7: shot-gun  8: submachine-gun

New classes:
    0: gun   (← Gunmen, Rifle, pistol, shot-gun, submachine-gun)
    1: knife (← knife, knife_attacker)
    2: blunt_weapon (← blunt_object)
    3: person       (← person)

Usage:
    python scripts/merge_weapon_classes.py              # full run
    python scripts/merge_weapon_classes.py --dry-run    # preview only
"""

from __future__ import annotations

import argparse
import shutil
import sys
import textwrap
from collections import Counter
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SRC_DATASET = PROJECT_ROOT / "datasets" / "yolo-weapon-detection"
DST_DATASET = PROJECT_ROOT / "datasets" / "weapon_merged"

SPLITS = ["train", "valid", "test"]

# Original class names (order matches indices in data.yaml)
ORIGINAL_CLASSES = [
    "Gunmen",           # 0
    "Rifle",            # 1
    "blunt_object",     # 2
    "knife",            # 3
    "knife_attacker",   # 4
    "person",           # 5
    "pistol",           # 6
    "shot-gun",         # 7
    "submachine-gun",   # 8
]

# New consolidated classes
NEW_CLASSES = ["gun", "knife", "blunt_weapon", "person"]

# Mapping: original index → new index
CLASS_REMAP: dict[int, int] = {
    0: 0,  # Gunmen        → gun
    1: 0,  # Rifle         → gun
    2: 2,  # blunt_object  → blunt_weapon
    3: 1,  # knife         → knife
    4: 1,  # knife_attacker→ knife
    5: 3,  # person        → person
    6: 0,  # pistol        → gun
    7: 0,  # shot-gun      → gun
    8: 0,  # submachine-gun→ gun
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def remap_label_line(line: str) -> str | None:
    """Remap a single YOLO annotation line.  Returns None for blank lines."""
    line = line.strip()
    if not line:
        return None
    parts = line.split()
    old_cls = int(parts[0])
    
    # bounds check
    if old_cls < 0 or old_cls >= len(ORIGINAL_CLASSES):
        print(f"  ⚠  Class id {old_cls} out of bounds, skipping line: {line}")
        return None
        
    new_cls = CLASS_REMAP.get(old_cls)
    if new_cls is None:
        print(f"  ⚠  Unknown class id {old_cls}, skipping line: {line}")
        return None
        
    parts[0] = str(new_cls)
    return " ".join(parts)


def write_data_yaml(dst: Path) -> None:
    """Write a new data.yaml for the merged dataset."""
    content = textwrap.dedent(f"""\
        train: train/images
        val: valid/images
        test: test/images

        nc: {len(NEW_CLASSES)}
        names: {NEW_CLASSES}
    """)
    dst.write_text(content, encoding="utf-8")


# ── Main logic ───────────────────────────────────────────────────────────────

def process_dataset(dry_run: bool = False) -> None:
    if not SRC_DATASET.exists():
        sys.exit(f"❌ Source dataset not found: {SRC_DATASET}")

    old_counter: Counter[str] = Counter()
    new_counter: Counter[str] = Counter()
    total_images = 0
    total_labels = 0

    for split in SPLITS:
        src_images = SRC_DATASET / split / "images"
        src_labels = SRC_DATASET / split / "labels"
        dst_images = DST_DATASET / split / "images"
        dst_labels = DST_DATASET / split / "labels"

        if not src_images.exists():
            print(f"⚠  Skipping split '{split}' — images dir not found.")
            continue

        print(f"\n{'─' * 60}")
        print(f"  Processing split: {split}")
        print(f"{'─' * 60}")

        # ── Images ───────────────────────────────────────────────────
        image_files = sorted(
            f for f in src_images.iterdir() if f.is_file()
        )
        print(f"  Images found: {len(image_files)}")
        total_images += len(image_files)

        if not dry_run:
            dst_images.mkdir(parents=True, exist_ok=True)
            for img in image_files:
                shutil.copy2(img, dst_images / img.name)

        # ── Labels ───────────────────────────────────────────────────
        if not src_labels.exists():
            print(f"  ⚠  No labels directory for split '{split}'.")
            continue

        label_files = sorted(
            f for f in src_labels.iterdir()
            if f.is_file() and f.suffix == ".txt"
        )
        print(f"  Labels found: {len(label_files)}")
        total_labels += len(label_files)

        if not dry_run:
            dst_labels.mkdir(parents=True, exist_ok=True)

        for lbl in label_files:
            lines = lbl.read_text(encoding="utf-8").strip().splitlines()
            remapped: list[str] = []
            for raw_line in lines:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                old_cls = int(raw_line.split()[0])
                if 0 <= old_cls < len(ORIGINAL_CLASSES):
                    old_counter[ORIGINAL_CLASSES[old_cls]] += 1

                new_line = remap_label_line(raw_line)
                if new_line is not None:
                    new_cls = int(new_line.split()[0])
                    if 0 <= new_cls < len(NEW_CLASSES):
                        new_counter[NEW_CLASSES[new_cls]] += 1
                    remapped.append(new_line)

            if not dry_run:
                (dst_labels / lbl.name).write_text(
                    "\n".join(remapped) + ("\n" if remapped else ""),
                    encoding="utf-8",
                )

    # ── data.yaml ────────────────────────────────────────────────────
    if not dry_run:
        write_data_yaml(DST_DATASET / "data.yaml")

    # ── Summary ──────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  {'DRY RUN — ' if dry_run else ''}Summary")
    print(f"{'═' * 60}")
    print(f"  Total images : {total_images}")
    print(f"  Total labels : {total_labels}")

    print("\n  Original class distribution:")
    for name, count in sorted(old_counter.items(), key=lambda x: -x[1]):
        print(f"    {name:20s} → {count:>6,}")

    print("\n  New (merged) class distribution:")
    for name, count in sorted(new_counter.items(), key=lambda x: -x[1]):
        print(f"    {name:20s} → {count:>6,}")

    if not dry_run:
        print(f"\n  ✅ Merged dataset saved to: {DST_DATASET}")
        print(f"     data.yaml: {DST_DATASET / 'data.yaml'}")
    else:
        print("\n  ℹ  Dry run complete — no files were written.")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge weapon-detection classes for YOLO training."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the remapping without writing any files.",
    )
    args = parser.parse_args()
    process_dataset(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
