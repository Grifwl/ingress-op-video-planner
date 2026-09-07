"""Minimal Tkinter front end for the operation-to-QGIS-layers conversion.

Kept deliberately simple (stdlib-only, no extra dependencies) so it can be
frozen into a single-file executable with PyInstaller for players who do
not want to touch a terminal.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from op_video_planner.convert import generate_animation_data


class OpVideoPlannerApp(tk.Tk):
    """Main application window.

    Lets the user pick the two RESWUE export files and an output folder,
    then runs :func:`generate_animation_data` and reports the result (or
    any warnings/errors) in an on-screen log.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("Ingress Operation Video Planner")
        self.resizable(False, False)

        self.keys_path = tk.StringVar()
        self.links_path = tk.StringVar()
        self.out_dir = tk.StringVar()

        self._build_widgets()

    def _build_widgets(self) -> None:
        """Lay out the file/folder pickers, generate button and log area."""
        padding = {"padx": 8, "pady": 4}

        self._add_picker_row(
            row=0,
            label="Keys file (portals):",
            variable=self.keys_path,
            command=self._pick_keys_file,
        )
        self._add_picker_row(
            row=1,
            label="Links file (plan order):",
            variable=self.links_path,
            command=self._pick_links_file,
        )
        self._add_picker_row(
            row=2,
            label="Output folder:",
            variable=self.out_dir,
            command=self._pick_out_dir,
        )

        generate_button = tk.Button(self, text="Generate", command=self._on_generate)
        generate_button.grid(row=3, column=0, columnspan=3, sticky="we", **padding)

        self.log = scrolledtext.ScrolledText(self, width=70, height=10, state="disabled")
        self.log.grid(row=4, column=0, columnspan=3, **padding)

    def _add_picker_row(self, row: int, label: str, variable: tk.StringVar, command) -> None:
        """Add one "label + path entry + browse button" row to the grid."""
        tk.Label(self, text=label, width=22, anchor="w").grid(row=row, column=0, padx=8, pady=4, sticky="w")
        tk.Entry(self, textvariable=variable, width=45).grid(row=row, column=1, padx=4, pady=4)
        tk.Button(self, text="Browse...", command=command).grid(row=row, column=2, padx=8, pady=4)

    def _pick_keys_file(self) -> None:
        path = filedialog.askopenfilename(title="Select the keys CSV", filetypes=[("CSV files", "*.csv")])
        if path:
            self.keys_path.set(path)

    def _pick_links_file(self) -> None:
        path = filedialog.askopenfilename(title="Select the links CSV", filetypes=[("CSV files", "*.csv")])
        if path:
            self.links_path.set(path)

    def _pick_out_dir(self) -> None:
        path = filedialog.askdirectory(title="Select the output folder")
        if path:
            self.out_dir.set(path)

    def _log_line(self, message: str) -> None:
        """Append one line to the on-screen log, auto-scrolling to it."""
        self.log.configure(state="normal")
        self.log.insert(tk.END, message + "\n")
        self.log.configure(state="disabled")
        self.log.see(tk.END)

    def _on_generate(self) -> None:
        """Validate the selected paths and run the conversion."""
        if not self.keys_path.get() or not self.links_path.get() or not self.out_dir.get():
            messagebox.showerror("Missing information", "Please select both input files and an output folder.")
            return

        try:
            summary = generate_animation_data(
                keys_path=self.keys_path.get(),
                links_path=self.links_path.get(),
                out_dir=self.out_dir.get(),
                warn=self._log_line,
            )
        except Exception as exc:  # noqa: BLE001 - surface any failure to the user, not just expected ones
            messagebox.showerror("Conversion failed", str(exc))
            self._log_line(f"ERROR: {exc}")
            return

        self._log_line(
            f"Done. Portals: {summary['portals']}  Links: {summary['links']}  Fields: {summary['fields']}"
        )
        self._log_line(
            f"Timeline: {summary['start']} -> {summary['end']} ({summary['duration_seconds']} seconds)"
        )
        messagebox.showinfo("Done", "portals.csv, links.csv and fields.csv were written to the output folder.")


def main() -> None:
    """Entry point for the ``op-video-planner-gui`` console/gui script."""
    app = OpVideoPlannerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
