"""Rename medical report PDFs based on extracted patient name.

This script scans a source folder for PDF files, attempts to extract the patient name
from the first page of each report, and writes a renamed copy into a destination
folder (default: `medical_new/`) with a sequential prefix like `001JohnDoe.pdf`.

The extraction is intentionally forgiving: it looks for common labels like
"Patient Name" or "Name" on the first page and falls back to the original file
name if none are found.

Usage:
    python src/components/rename_pdf.py
    python src/components/rename_pdf.py --src medical --dst medical_new
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter


def _extract_name_from_text(text: str) -> Optional[str]:
    """Attempt to find a patient name in a block of text."""

    # Common patterns in medical report headers
    patterns = [
        r"Patient\s*Name\s*[:\-]\s*(?P<name>[A-Za-z][A-Za-z\s,.'-]{1,100})",
        r"Name\s*[:\-]\s*(?P<name>[A-Za-z][A-Za-z\s,.'-]{1,100})",
        r"Patient\s*[:\-]\s*(?P<name>[A-Za-z][A-Za-z\s,.'-]{1,100})",
    ]

    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            name = m.group("name").strip()
            # Normalize whitespace and remove trailing punctuation
            name = re.sub(r"\s+", " ", name)
            name = name.strip(" ,.-")
            return name

    return None


def extract_name_from_pdf(pdf_path: Path) -> Optional[str]:
    """Extract a patient name from the first page of a PDF."""

    try:
        reader = PdfReader(str(pdf_path))
        if not reader.pages:
            return None

        page = reader.pages[0]
        text = page.extract_text() or ""
        return _extract_name_from_text(text)

    except Exception:
        return None


def _format_safe_name(name: str) -> str:
    """Convert name into a filesystem-safe string."""

    # Remove characters that can be problematic in filenames
    safe = re.sub(r"[^A-Za-z0-9 _\-\.]", "", name)
    # Collapse whitespace
    safe = re.sub(r"\s+", " ", safe).strip()
    # Convert spaces to underscores
    safe = safe.replace(" ", "_")
    return safe or "unknown"


def _next_sequence(dest_dir: Path) -> int:
    """Find the next available sequence number for prefixing output files."""

    existing = [p.name for p in dest_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]
    seqs = []
    for name in existing:
        m = re.match(r"^(?P<num>\d{3})", name)
        if m:
            try:
                seqs.append(int(m.group("num")))
            except ValueError:
                pass

    return (max(seqs) + 1) if seqs else 1


def rename_reports(src_dir: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)

    seq = _next_sequence(dst_dir)

    for pdf_path in sorted(src_dir.glob("*.pdf")):
        if not pdf_path.is_file():
            continue

        name = extract_name_from_pdf(pdf_path)
        if not name:
            name = pdf_path.stem

        safe_name = _format_safe_name(name)
        prefix = f"{seq:03d}"
        out_name = f"{prefix}{safe_name}.pdf"
        out_path = dst_dir / out_name

        print(f"{pdf_path.name} -> {out_path.name}")

        if out_path.exists():
            # Merge: append new PDF to existing one
            existing_reader = PdfReader(str(out_path))
            new_reader = PdfReader(str(pdf_path))
            writer = PdfWriter()
            # Add existing pages
            for page in existing_reader.pages:
                writer.add_page(page)
            # Add new pages
            for page in new_reader.pages:
                writer.add_page(page)
            # Overwrite the existing file
            with out_path.open("wb") as f:
                writer.write(f)
        else:
            # Copy new file
            with pdf_path.open("rb") as f_in, out_path.open("wb") as f_out:
                f_out.write(f_in.read())

        seq += 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rename medical reports based on extracted patient name.")
    parser.add_argument("--src", default="hospital", help="Source folder containing PDFs.")
    parser.add_argument("--dst", default="medical_new", help="Destination folder for renamed PDFs.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    src_dir = Path(args.src)
    dst_dir = Path(args.dst)

    if not src_dir.exists() or not src_dir.is_dir():
        raise SystemExit(f"Source directory does not exist: {src_dir}")

    rename_reports(src_dir, dst_dir)


if __name__ == "__main__":
    main()
