#!/usr/bin/env python3
"""Create the non-destructive standard skeleton for a new FDE project."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from install_brand_asset import EXPECTED_SHA256, SOURCE_LOGO, install_logo, sha256


DIRECTORIES = (
    "frontend",
    "frontend/public/brand",
    "backend",
    "docs/specs",
    "docs/architecture",
    "docs/verification",
)

PROJECT_DIR_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")
BRAND_LOGO_PATH = "frontend/public/brand/ff-logo.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize a standard frontend/backend/docs project skeleton without overwriting files."
    )
    parser.add_argument("project", type=Path, help="Target project root")
    parser.add_argument("--public-name", required=True, help="User-visible name in the form 'FF - Name'")
    parser.add_argument("--summary", required=True, help="One-sentence product positioning")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    return parser.parse_args()


def render(template: str, project_dir_name: str, public_name: str, summary: str) -> str:
    return (
        template.replace("{{PROJECT_DIR_NAME}}", project_dir_name)
        .replace("{{PUBLIC_NAME}}", public_name)
        .replace("{{SUMMARY}}", summary)
        .replace("{{DATE}}", date.today().isoformat())
    )


def main() -> int:
    args = parse_args()
    public_name = args.public_name.strip()
    summary = args.summary.strip()
    if not public_name.startswith("FF - ") or not public_name.removeprefix("FF - ").strip():
        raise SystemExit("--public-name must use the form 'FF - <正式產品名>'")
    if not summary:
        raise SystemExit("--summary must not be empty")

    project = args.project.expanduser().resolve()
    if not PROJECT_DIR_PATTERN.fullmatch(project.name):
        raise SystemExit(
            "project folder name must use PascalCase with ASCII letters and digits, "
            "starting with an uppercase letter; examples: AgenticRAG, OcrPlatform"
        )
    if project.exists() and not project.is_dir():
        raise SystemExit(f"target project root is not a directory: {project}")
    skill_root = Path(__file__).resolve().parents[1]
    assets = skill_root / "assets"
    skills_root = skill_root.parent
    templates = {
        "README.md": assets / "README.template.md",
        "AGENTS.md": assets / "AGENTS.template.md",
        "docs/PRD.md": skills_root / "product-prd/assets/PRD.template.md",
        "docs/specs/product-spec.md": (
            skills_root / "product-spec/assets/product-spec.template.md"
        ),
        "docs/specs/feature-map.md": (
            skills_root / "feature-spec-planning/assets/feature-map.template.md"
        ),
        "docs/architecture/architecture.md": assets / "architecture.template.md",
    }
    missing_templates = [str(path) for path in templates.values() if not path.is_file()]
    if missing_templates:
        raise SystemExit(
            "required project-level workflow templates are missing: "
            + ", ".join(missing_templates)
        )
    if not SOURCE_LOGO.is_file() or sha256(SOURCE_LOGO) != EXPECTED_SHA256:
        raise SystemExit("bundled FF logo is missing or has changed")

    file_targets = [project / relative for relative in (*templates, BRAND_LOGO_PATH, "CLAUDE.md")]
    directory_targets = {project / relative for relative in DIRECTORIES}
    for target in file_targets + list(directory_targets):
        directory_targets.update(parent for parent in target.parents if parent != project and project in parent.parents)
    for target in sorted(directory_targets, key=lambda path: (len(path.parts), str(path))):
        if not target.resolve().is_relative_to(project):
            raise SystemExit(f"required directory resolves outside project: {target}")
        if (target.exists() or target.is_symlink()) and not target.is_dir():
            raise SystemExit(f"required directory path is occupied by a file: {target}")
    for target in file_targets:
        if not target.resolve().is_relative_to(project):
            raise SystemExit(f"required file resolves outside project: {target}")
        if (target.exists() or target.is_symlink()) and not target.is_file():
            raise SystemExit(f"required file path is occupied by a non-file: {target}")
    rendered = {
        relative: render(path.read_text(encoding="utf-8"), project.name, public_name, summary)
        for relative, path in templates.items()
    }

    logo_target = project / BRAND_LOGO_PATH
    if logo_target.is_symlink():
        raise SystemExit("FF logo destination must not be a symbolic link")
    if logo_target.exists():
        if not logo_target.is_file():
            raise SystemExit("FF logo destination exists and is not a file")
        if sha256(logo_target) != EXPECTED_SHA256:
            raise SystemExit(
                "FF logo destination already contains different bytes; refusing to overwrite"
            )
    created_dirs: list[str] = []
    created_files: list[str] = []
    kept_files: list[str] = []

    for relative in DIRECTORIES:
        target = project / relative
        if target.exists() and not target.is_dir():
            raise SystemExit(f"required directory path is occupied by a file: {target}")
        if not target.exists():
            created_dirs.append(relative)
            if not args.dry_run:
                target.mkdir(parents=True, exist_ok=True)

    for relative, content in rendered.items():
        target = project / relative
        if target.exists():
            kept_files.append(relative)
            continue
        created_files.append(relative)
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    if logo_target.exists():
        kept_files.append(BRAND_LOGO_PATH)
    else:
        created_files.append(BRAND_LOGO_PATH)
        if not args.dry_run:
            state, installed_logo = install_logo(project, BRAND_LOGO_PATH)
            if state != "installed" or sha256(installed_logo) != EXPECTED_SHA256:
                raise SystemExit("FF logo installation failed integrity verification")

    claude = project / "CLAUDE.md"
    if claude.exists():
        kept_files.append("CLAUDE.md")
    else:
        created_files.append("CLAUDE.md")
        if not args.dry_run:
            project.mkdir(parents=True, exist_ok=True)
            claude.write_text("@AGENTS.md\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "project": str(project),
                "project_directory_name": project.name,
                "dry_run": args.dry_run,
                "created_directories": created_dirs,
                "created_files": created_files,
                "kept_files": kept_files,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
