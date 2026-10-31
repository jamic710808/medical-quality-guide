#!/usr/bin/env python3
"""Install the immutable FF logo into a confirmed frontend-relative path."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path, PurePosixPath


EXPECTED_SHA256 = "522944bbaee48d98190c8c5a0a0ac80f05b71b1975838807742a782e2aeceedc"
SKILL_ROOT = Path(__file__).resolve().parents[1]
SOURCE_LOGO = SKILL_ROOT / "assets" / "brand" / "ff-logo.png"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_relative_path(value: str) -> PurePosixPath:
    if "\\" in value:
        raise ValueError("logo path must use POSIX separators")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("logo path must be a safe project-relative path")
    if not relative.parts or relative.parts[0] != "frontend":
        raise ValueError("logo path must stay inside frontend/")
    if relative.suffix.lower() != ".png":
        raise ValueError("logo path must end in .png")
    return relative


def install_logo(target: Path, relative_value: str) -> tuple[str, Path]:
    target = target.expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise ValueError("target project root exists and is not a directory")
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)
    if not SOURCE_LOGO.is_file() or sha256(SOURCE_LOGO) != EXPECTED_SHA256:
        raise RuntimeError("bundled FF logo is missing or has changed")

    relative = parse_relative_path(relative_value)
    destination = target.joinpath(*relative.parts)
    resolved_destination = destination.resolve()
    try:
        resolved_destination.relative_to(target)
    except ValueError as exc:
        raise ValueError("logo destination resolves outside the target project") from exc
    if destination.is_symlink():
        raise FileExistsError("logo destination must not be a symbolic link")
    if destination.exists():
        if not destination.is_file():
            raise FileExistsError("logo destination exists and is not a file")
        if sha256(destination) == EXPECTED_SHA256:
            return "unchanged", destination
        raise FileExistsError(
            "logo destination already contains different bytes; refusing to overwrite"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE_LOGO, destination)
    if sha256(destination) != EXPECTED_SHA256:
        destination.unlink(missing_ok=True)
        raise RuntimeError("installed logo failed checksum verification")
    return "installed", destination


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy the bundled FF logo into a confirmed frontend path."
    )
    parser.add_argument("target", help="Target project root")
    parser.add_argument(
        "--path",
        required=True,
        dest="relative_path",
        help="Confirmed project-relative PNG path under frontend/",
    )
    args = parser.parse_args()

    try:
        state, destination = install_logo(Path(args.target), args.relative_path)
    except (ValueError, RuntimeError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"status={state} path={destination.relative_to(Path(args.target).resolve())} "
        f"sha256={EXPECTED_SHA256}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
