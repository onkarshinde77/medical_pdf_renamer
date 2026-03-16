"""Simple GUI frontend for the PDF renaming/merging tool.

This provides two directory input fields (hospital PDFs + medical PDFs), an output
folder field, and a Run button that processes the selected folders.

Run with:
    python -m src.app.gui
"""

from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from src.components.rename_pdf import rename_reports


def _choose_folder(entry: tk.Entry) -> None:
    """Pop up a folder chooser and put the selected path into the given entry."""

    initial = entry.get() or os.getcwd()
    chosen = filedialog.askdirectory(title="Select folder", initialdir=initial)
    if chosen:
        entry.delete(0, tk.END)
        entry.insert(0, chosen)


def _run_process(hospital_path: str, medical_path: str, output_path: str, status_label: tk.Label) -> None:
    """Run the PDF renaming/merging operation and update the status label."""

    try:
        src_dirs = [Path(hospital_path), Path(medical_path)]
        dst_dir = Path(output_path)

        for src in src_dirs:
            if not src.exists() or not src.is_dir():
                raise FileNotFoundError(f"Source directory does not exist: {src}")

        rename_reports(src_dirs, dst_dir)
        status_label.config(text=f"Done. Output written to: {dst_dir}")

    except Exception as exc:
        messagebox.showerror("Error", str(exc))
        status_label.config(text="Failed. See error dialog.")


def main() -> None:
    root = tk.Tk()
    root.title("Medical PDF Renamer")

    frame = tk.Frame(root, padx=12, pady=12)
    frame.pack(fill=tk.BOTH, expand=True)

    # Hospital PDFs
    tk.Label(frame, text="Hospital PDFs folder:").grid(row=0, column=0, sticky="w")
    hospital_entry = tk.Entry(frame, width=60)
    hospital_entry.grid(row=0, column=1, padx=(4, 0))
    tk.Button(frame, text="Browse...", command=lambda: _choose_folder(hospital_entry)).grid(row=0, column=2, padx=4)

    # Medical PDFs
    tk.Label(frame, text="Medical PDFs folder:").grid(row=1, column=0, sticky="w", pady=(8, 0))
    medical_entry = tk.Entry(frame, width=60)
    medical_entry.grid(row=1, column=1, padx=(4, 0), pady=(8, 0))
    tk.Button(frame, text="Browse...", command=lambda: _choose_folder(medical_entry)).grid(row=1, column=2, padx=4, pady=(8, 0))

    # Output folder
    tk.Label(frame, text="Output folder:").grid(row=2, column=0, sticky="w", pady=(8, 0))
    output_entry = tk.Entry(frame, width=60)
    output_entry.grid(row=2, column=1, padx=(4, 0), pady=(8, 0))
    output_entry.insert(0, "all_data")
    tk.Button(frame, text="Browse...", command=lambda: _choose_folder(output_entry)).grid(row=2, column=2, padx=4, pady=(8, 0))

    status_label = tk.Label(frame, text="Ready.")
    status_label.grid(row=3, column=0, columnspan=3, pady=(12, 0), sticky="w")

    run_button = tk.Button(
        frame,
        text="Run",
        width=12,
        command=lambda: _run_process(
            hospital_entry.get(), medical_entry.get(), output_entry.get(), status_label
        ),
    )
    run_button.grid(row=4, column=0, columnspan=3, pady=(12, 0))

    root.mainloop()


if __name__ == "__main__":
    main()
