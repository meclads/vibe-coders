"""Closest Pair Lab desktop application."""

from __future__ import annotations

import csv
import math
import queue
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from benchmark import benchmark, benchmark_sizes
from closest_pair import Point, format_pair, timed_brute, timed_divide


COLORS = {
    "background": "#0B1220",
    "panel": "#111C2E",
    "panel_alt": "#162338",
    "border": "#26364D",
    "mint": "#5EEAD4",
    "text": "#F4F7FB",
    "muted": "#91A2B8",
    "red": "#FB7185",
    "blue": "#60A5FA",
    "purple": "#A78BFA",
    "green": "#34D399",
}


class ClosestPairApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Closest Pair Lab")
        self.root.geometry("1440x920")
        self.root.minsize(1120, 760)
        self.points: list[Point] = []
        self.trace = None
        self.brute_pair = None
        self.divide_pair = None
        self.results_queue: queue.Queue = queue.Queue()
        self.busy = False
        self._configure_style()
        self._build_layout()
        self._generate_points()

    def _configure_style(self):
        self.root.configure(bg=COLORS["background"])
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["background"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 22), foreground=COLORS["text"])
        style.configure("Section.TLabel", background=COLORS["panel"], font=("Segoe UI Semibold", 11), foreground=COLORS["text"])
        style.configure("Metric.TLabel", background=COLORS["panel_alt"], font=("Segoe UI Semibold", 16), foreground=COLORS["mint"])
        style.configure("TButton", font=("Segoe UI Semibold", 9), padding=(10, 8), background=COLORS["panel_alt"], foreground=COLORS["text"], bordercolor=COLORS["border"])
        style.map("TButton", background=[("active", "#20314A"), ("disabled", "#172236")], foreground=[("disabled", "#64748B")])
        style.configure("Accent.TButton", background=COLORS["mint"], foreground=COLORS["background"], bordercolor=COLORS["mint"])
        style.map("Accent.TButton", background=[("active", "#99F6E4"), ("disabled", "#2A615C")])
        style.configure("TEntry", fieldbackground="#0D1728", foreground=COLORS["text"], insertcolor=COLORS["text"], bordercolor=COLORS["border"], padding=7)
        style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
        style.configure("TNotebook.Tab", background=COLORS["panel"], foreground=COLORS["muted"], padding=(16, 9), font=("Segoe UI Semibold", 9))
        style.map("TNotebook.Tab", background=[("selected", COLORS["panel_alt"])], foreground=[("selected", COLORS["mint"])])
        style.configure("Treeview", background="#0D1728", fieldbackground="#0D1728", foreground=COLORS["text"], rowheight=27, bordercolor=COLORS["border"], font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=COLORS["panel_alt"], foreground=COLORS["muted"], font=("Segoe UI Semibold", 9), relief="flat")
        style.map("Treeview", background=[("selected", "#24404E")])
        style.configure("Horizontal.TProgressbar", background=COLORS["mint"], troughcolor=COLORS["panel_alt"], bordercolor=COLORS["panel_alt"])

    def _panel(self, parent, padding=14):
        return ttk.Frame(parent, style="Panel.TFrame", padding=padding)

    def _build_layout(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        header = ttk.Frame(self.root, padding=(24, 18, 24, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        branding = ttk.Label(header, text="CLOSEST PAIR LAB", foreground=COLORS["mint"], font=("Segoe UI Semibold", 9))
        branding.grid(row=0, column=0, sticky="w")
        self.status_badge = tk.Label(header, text="READY", bg="#17372F", fg=COLORS["mint"], padx=12, pady=5, font=("Segoe UI Semibold", 8))
        self.status_badge.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Label(header, text="Closest Pair of Points", style="Title.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Label(header, text="Brute Force vs Divide & Conquer", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(2, 0))

        body = ttk.Frame(self.root, padding=(20, 4, 20, 18))
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, minsize=280, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self._build_controls(body)
        self._build_workspace(body)

    def _build_controls(self, parent):
        sidebar = self._panel(parent, 16)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        sidebar.grid_columnconfigure(0, weight=1)
        ttk.Label(sidebar, text="DATASET", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(sidebar, text="POINT COUNT N", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(17, 5))
        self.n_var = tk.StringVar(value="120")
        ttk.Entry(sidebar, textvariable=self.n_var).grid(row=2, column=0, sticky="ew")

        ttk.Label(sidebar, text="COORDINATE BOUNDS", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(15, 5))
        bounds = ttk.Frame(sidebar, style="Panel.TFrame")
        bounds.grid(row=4, column=0, sticky="ew")
        bounds.grid_columnconfigure(0, weight=1)
        bounds.grid_columnconfigure(1, weight=1)
        self.minimum_var = tk.StringVar(value="-100")
        self.maximum_var = tk.StringVar(value="100")
        ttk.Entry(bounds, textvariable=self.minimum_var).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Entry(bounds, textvariable=self.maximum_var).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ttk.Label(bounds, text="MIN", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Label(bounds, text="MAX", style="Muted.TLabel").grid(row=1, column=1, sticky="w", padx=(5, 0), pady=(3, 0))

        ttk.Label(sidebar, text="RANDOM SEED", style="Muted.TLabel").grid(row=5, column=0, sticky="w", pady=(15, 5))
        self.seed_var = tk.StringVar(value="2026")
        ttk.Entry(sidebar, textvariable=self.seed_var).grid(row=6, column=0, sticky="ew")
        ttk.Button(sidebar, text="Generate New Points", command=self._generate_points).grid(row=7, column=0, sticky="ew", pady=(13, 6))
        ttk.Button(sidebar, text="Load CSV", command=self._load_csv).grid(row=8, column=0, sticky="ew", pady=3)
        ttk.Button(sidebar, text="Run Both Algorithms", style="Accent.TButton", command=self._run_algorithms).grid(row=9, column=0, sticky="ew", pady=(11, 6))
        ttk.Button(sidebar, text="Reset", command=self._reset).grid(row=10, column=0, sticky="ew", pady=3)

        ttk.Separator(sidebar).grid(row=11, column=0, sticky="ew", pady=17)
        ttk.Label(sidebar, text="BENCHMARK", style="Section.TLabel").grid(row=12, column=0, sticky="w")
        ttk.Label(sidebar, text="Maximum N (brute force)", style="Muted.TLabel").grid(row=13, column=0, sticky="w", pady=(10, 5))
        self.max_benchmark_var = tk.StringVar(value="1600")
        ttk.Entry(sidebar, textvariable=self.max_benchmark_var).grid(row=14, column=0, sticky="ew")
        self.benchmark_button = ttk.Button(sidebar, text="Run Benchmark", command=self._run_benchmark)
        self.benchmark_button.grid(row=15, column=0, sticky="ew", pady=(10, 6))
        self.progress = ttk.Progressbar(sidebar, mode="determinate", maximum=100)
        self.progress.grid(row=16, column=0, sticky="ew", pady=(4, 5))
        self.progress_label = ttk.Label(sidebar, text="Ready for analysis", style="Muted.TLabel", wraplength=240)
        self.progress_label.grid(row=17, column=0, sticky="w")
        ttk.Label(sidebar, text="Small datasets may not show a consistent speed advantage; overhead and hardware affect timings.", style="Muted.TLabel", wraplength=240).grid(row=18, column=0, sticky="w", pady=(18, 0))

    def _build_workspace(self, parent):
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=0, column=1, sticky="nsew")
        self.analysis_tab = ttk.Frame(self.notebook, padding=10)
        self.benchmark_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.analysis_tab, text="  Analysis  ")
        self.notebook.add(self.benchmark_tab, text="  Runtime Study  ")
        self.analysis_tab.grid_columnconfigure(0, weight=1)
        self.analysis_tab.grid_columnconfigure(1, weight=1)
        self.analysis_tab.grid_rowconfigure(2, weight=1)
        self._build_results(self.analysis_tab)
        self._build_point_visuals(self.analysis_tab)
        self._build_benchmark_view(self.benchmark_tab)

    def _build_results(self, parent):
        results = ttk.Frame(parent, style="TFrame")
        results.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        results.grid_columnconfigure(0, weight=1)
        results.grid_columnconfigure(1, weight=1)
        self.brute_card = self._result_card(results, "BRUTE FORCE", "O(N²)", COLORS["red"])
        self.brute_card["frame"].grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.divide_card = self._result_card(results, "DIVIDE & CONQUER", "O(N log N)", COLORS["blue"])
        self.divide_card["frame"].grid(row=0, column=1, sticky="ew", padx=(6, 0))
        footer = self._panel(parent, 11)
        footer.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 9))
        footer.grid_columnconfigure(1, weight=1)
        self.verify_label = ttk.Label(footer, text="Run both algorithms to compare results", style="Muted.TLabel")
        self.verify_label.grid(row=0, column=0, sticky="w")
        self.time_label = ttk.Label(footer, text="Brute Force  -- ms     |     Divide & Conquer  -- ms", style="Muted.TLabel")
        self.time_label.grid(row=0, column=1, sticky="e")

    def _result_card(self, parent, title, complexity, accent):
        card = self._panel(parent, 13)
        card.configure(style="Panel.TFrame")
        card.grid_columnconfigure(0, weight=1)
        header = ttk.Frame(card, style="Panel.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ttk.Label(header, text=title, style="Section.TLabel").grid(row=0, column=0, sticky="w")
        tk.Label(header, text=complexity, bg=COLORS["panel_alt"], fg=accent, padx=8, pady=4, font=("Segoe UI Semibold", 8)).grid(row=0, column=1, sticky="e")
        distance = ttk.Label(card, text="N/A", style="Metric.TLabel")
        distance.grid(row=1, column=0, sticky="w", pady=(10, 3))
        pair = ttk.Label(card, text="No result yet", style="Muted.TLabel", wraplength=430)
        pair.grid(row=2, column=0, sticky="w")
        return {"frame": card, "distance": distance, "pair": pair}

    def _build_point_visuals(self, parent):
        chart_panel = self._panel(parent, 10)
        chart_panel.grid(row=2, column=0, sticky="nsew", padx=(0, 6))
        chart_panel.grid_columnconfigure(0, weight=1)
        chart_panel.grid_rowconfigure(1, weight=1)
        chart_heading = ttk.Frame(chart_panel, style="Panel.TFrame")
        chart_heading.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        chart_heading.grid_columnconfigure(0, weight=1)
        ttk.Label(chart_heading, text="POINT GEOMETRY", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(chart_heading, text="Redraw", command=self._redraw_points).grid(row=0, column=1, sticky="e")
        self.point_figure = Figure(figsize=(6.2, 4.5), dpi=100, facecolor=COLORS["panel"])
        self.point_axes = self.point_figure.add_subplot(111)
        self.point_canvas = FigureCanvasTkAgg(self.point_figure, master=chart_panel)
        self.point_canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

        table_panel = self._panel(parent, 10)
        table_panel.grid(row=2, column=1, sticky="nsew", padx=(6, 0))
        table_panel.grid_columnconfigure(0, weight=1)
        table_panel.grid_rowconfigure(1, weight=1)
        ttk.Label(table_panel, text="GENERATED POINTS", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.point_table = self._tree(table_panel, 1, ("index", "x", "y"), ("#", "X COORDINATE", "Y COORDINATE"))

    def _build_benchmark_view(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        chart_panel = self._panel(parent, 12)
        chart_panel.grid(row=0, column=0, sticky="nsew")
        chart_panel.grid_columnconfigure(0, weight=1)
        chart_panel.grid_rowconfigure(1, weight=1)
        ttk.Label(chart_panel, text="RUNNING TIME VS INPUT SIZE", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 7))
        self.benchmark_figure = Figure(figsize=(9, 4.8), dpi=100, facecolor=COLORS["panel"])
        self.benchmark_axes = self.benchmark_figure.add_subplot(111)
        self.benchmark_canvas = FigureCanvasTkAgg(self.benchmark_figure, master=chart_panel)
        self.benchmark_canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
        table_panel = self._panel(parent, 10)
        table_panel.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        table_panel.grid_columnconfigure(0, weight=1)
        ttk.Label(table_panel, text="MEASURED BENCHMARKS", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.benchmark_table = self._tree(table_panel, 1, ("n", "brute", "divide", "distance"), ("N", "BRUTE FORCE (MS)", "DIVIDE & CONQUER (MS)", "MINIMUM DISTANCE"))
        self.benchmark_table.configure(height=6)

    def _tree(self, parent, columns, headings):
        wrapper = ttk.Frame(parent, style="Panel.TFrame")
        wrapper.grid(row=row, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)
        table = ttk.Treeview(wrapper, columns=columns, show="headings", selectmode="browse")
        for column, heading in zip(columns, headings):
            table.heading(column, text=heading)
            table.column(column, anchor="w" if column == "index" else "e", width=72 if column in ("index", "n") else 125, stretch=True)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        return table

    def _set_status(self, status: str):
        styles = {
            "READY": ("#17372F", COLORS["mint"]),
            "RUNNING": ("#3D321B", "#FCD34D"),
            "VERIFIED": ("#17372F", COLORS["mint"]),
            "ERROR": ("#44232A", COLORS["red"]),
        }
        background, foreground = styles[status]
        self.status_badge.configure(text=status, bg=background, fg=foreground)

    def _read_seed(self):
        raw = self.seed_var.get().strip()
        return int(raw) if raw else None

    def _generate_points(self):
        try:
            count = int(self.n_var.get())
            lower = float(self.minimum_var.get())
            upper = float(self.maximum_var.get())
            seed = self._read_seed()
            if count < 0:
                raise ValueError("N must be zero or greater.")
            if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
                raise ValueError("Coordinate bounds must be finite and MIN must be less than MAX.")
        except ValueError as error:
            messagebox.showerror("Invalid input", str(error), parent=self.root)
            self._set_status("ERROR")
            return
        rng = random.Random(seed)
        self.points = [(rng.uniform(lower, upper), rng.uniform(lower, upper)) for _ in range(count)]
        self._clear_analysis()
        self._refresh_points()
        self.progress_label.configure(text=f"Generated {count:,} points")
        self._set_status("READY")

    def _load_csv(self):
        path = filedialog.askopenfilename(parent=self.root, title="Load point coordinates", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            points = []
            with open(path, newline="", encoding="utf-8-sig") as csv_file:
                for row_number, row in enumerate(csv.reader(csv_file), start=1):
                    if not row or all(not value.strip() for value in row):
                        continue
                    if len(row) < 2:
                        raise ValueError(f"Row {row_number} must contain x and y values.")
                    try:
                        x, y = float(row[0]), float(row[1])
                    except ValueError:
                        if not points and row_number == 1:
                            continue
                        raise ValueError(f"Row {row_number} contains a non-numeric coordinate.")
                    if not math.isfinite(x) or not math.isfinite(y):
                        raise ValueError(f"Row {row_number} contains a non-finite coordinate.")
                    points.append((x, y))
            self.points = points
            self.n_var.set(str(len(points)))
            self._clear_analysis()
            self._refresh_points()
            self.progress_label.configure(text=f"Loaded {len(points):,} points from CSV")
            self._set_status("READY")
        except (OSError, ValueError) as error:
            messagebox.showerror("CSV could not be loaded", str(error), parent=self.root)
            self._set_status("ERROR")

    def _refresh_points(self):
        self._redraw_points()
        for item in self.point_table.get_children():
            self.point_table.delete(item)
        for index, (x, y) in enumerate(self.points, start=1):
            self.point_table.insert("", "end", values=(index, f"{x:.6f}", f"{y:.6f}"))

    def _redraw_points(self):
        axes = self.point_axes
        axes.clear()
        axes.set_facecolor("#0D1728")
        axes.tick_params(colors=COLORS["muted"], labelsize=8)
        for spine in axes.spines.values():
            spine.set_color(COLORS["border"])
        axes.grid(color="#26364D", linewidth=0.65, alpha=0.75)
        axes.set_title("Closest-pair geometry", color=COLORS["text"], fontsize=11, pad=10)
        axes.set_xlabel("X coordinate", color=COLORS["muted"])
        axes.set_ylabel("Y coordinate", color=COLORS["muted"])
        if self.points:
            x_values = [point[0] for point in self.points]
            y_values = [point[1] for point in self.points]
            unique_points = sorted(set(self.points))
            counts = {point: self.points.count(point) for point in unique_points}
            axes.scatter([p[0] for p in unique_points], [p[1] for p in unique_points], s=25, color=COLORS["mint"], alpha=0.8, edgecolors="#E2FFFA", linewidths=0.35, label="Input points", zorder=3)
            for point, count in counts.items():
                if count > 1:
                    axes.annotate(f"×{count}", point, xytext=(5, 5), textcoords="offset points", color=COLORS["text"], fontsize=8)
            if self.trace:
                split_x = self.trace["split_x"]
                axes.axvline(split_x, color=COLORS["purple"], linestyle="--", linewidth=1.4, label="D&C dividing line", zorder=1)
                y_min, y_max = min(y_values), max(y_values)
                height = max(y_max - y_min, 1.0)
                axes.add_patch(Rectangle((self.trace["strip_left"], y_min - 0.04 * height), self.trace["strip_right"] - self.trace["strip_left"], 1.08 * height, facecolor=COLORS["purple"], edgecolor=COLORS["purple"], alpha=0.12, label="D&C strip", zorder=0))
                axes.text(split_x, y_max + 0.06 * height, f"strip width 2d = {2 * self.trace['distance']:.6f}", color=COLORS["purple"], fontsize=8, ha="center")
            if self.brute_pair and self.divide_pair and self.brute_pair == self.divide_pair:
                first, second = self.brute_pair
                axes.plot([first[0], second[0]], [first[1], second[1]], color=COLORS["red"], linewidth=4.2, alpha=0.85, label="Brute-force closest pair", zorder=4)
                axes.plot([first[0], second[0]], [first[1], second[1]], color=COLORS["blue"], linewidth=2.0, linestyle="--", label="D&C closest pair (overlap)", zorder=5)
            else:
                for pair, color, label, style in ((self.brute_pair, COLORS["red"], "Brute-force closest pair", "-"), (self.divide_pair, COLORS["blue"], "D&C closest pair", "--")):
                    if pair:
                        first, second = pair
                        axes.plot([first[0], second[0]], [first[1], second[1]], color=color, linewidth=2.5, linestyle=style, marker="o", markersize=4, label=label, zorder=5)
            axes.margins(0.12)
            axes.legend(loc="best", facecolor=COLORS["panel"], edgecolor=COLORS["border"], labelcolor=COLORS["text"], fontsize=7)
            if len(self.points) < 2:
                axes.text(0.5, 0.94, "No pair exists for N < 2", transform=axes.transAxes, ha="center", color=COLORS["muted"], fontsize=9)
        else:
            axes.text(0.5, 0.5, "No points loaded", transform=axes.transAxes, ha="center", color=COLORS["muted"])
        self.point_figure.tight_layout(pad=1.6)
        self.point_canvas.draw_idle()

    def _clear_analysis(self):
        self.trace = None
        self.brute_pair = None
        self.divide_pair = None
        self.brute_card["distance"].configure(text="N/A")
        self.divide_card["distance"].configure(text="N/A")
        self.brute_card["pair"].configure(text="No result yet")
        self.divide_card["pair"].configure(text="No result yet")
        self.verify_label.configure(text="Run both algorithms to compare results")
        self.time_label.configure(text="Brute Force  -- ms     |     Divide & Conquer  -- ms")

    def _run_algorithms(self):
        if self.busy:
            return
        points = list(self.points)
        if len(points) < 2:
            self._clear_analysis()
            self._refresh_points()
            self.verify_label.configure(text="N/A: a closest pair requires at least two points")
            self.progress_label.configure(text="No pair exists")
            self._set_status("READY")
            return
        self._begin_task("Running both algorithms...")

        def work():
            try:
                brute_result, brute_ms = timed_brute(points)
                divide_result, divide_ms = timed_divide(points)
                agrees = math.isclose(brute_result[0], divide_result[0], rel_tol=1e-10, abs_tol=1e-10)
                self.results_queue.put(("analysis", (brute_result, brute_ms, divide_result, divide_ms, agrees)))
            except Exception as error:
                self.results_queue.put(("error", str(error)))

        threading.Thread(target=work, daemon=True).start()

    def _run_benchmark(self):
        if self.busy:
            return
        try:
            maximum = int(self.max_benchmark_var.get())
            sizes = benchmark_sizes(maximum)
            seed = self._read_seed()
        except ValueError as error:
            messagebox.showerror("Invalid benchmark settings", str(error), parent=self.root)
            self._set_status("ERROR")
            return
        self._begin_task("Benchmark starting...")
        self.notebook.select(self.benchmark_tab)

        def report_progress(current, total):
            self.results_queue.put(("benchmark_progress", (current, total)))

        def work():
            try:
                rows = benchmark(sizes, seed=2026 if seed is None else seed, progress=report_progress)
                self.results_queue.put(("benchmark", rows))
            except Exception as error:
                self.results_queue.put(("error", str(error)))

        threading.Thread(target=work, daemon=True).start()

    def _begin_task(self, message):
        self.busy = True
        self.progress.configure(value=0, maximum=100)
        self.progress_label.configure(text=message)
        self._set_status("RUNNING")
        self._poll_results()

    def _poll_results(self):
        try:
            while True:
                kind, payload = self.results_queue.get_nowait()
                if kind == "analysis":
                    brute, brute_ms, divide, divide_ms, agrees = payload
                    self.brute_pair, self.divide_pair = brute[1], divide[1]
                    self.trace = divide[2]
                    self.brute_card["distance"].configure(text=f"{brute[0]:.6f}")
                    self.divide_card["distance"].configure(text=f"{divide[0]:.6f}")
                    self.brute_card["pair"].configure(text=format_pair(brute[1]))
                    self.divide_card["pair"].configure(text=format_pair(divide[1]))
                    self.time_label.configure(text=f"Brute Force  {brute_ms:.3f} ms     |     Divide & Conquer  {divide_ms:.3f} ms")
                    self.verify_label.configure(text="VERIFIED  ·  minimum distances agree" if agrees else "ERROR  ·  minimum distances differ", foreground=COLORS["mint"] if agrees else COLORS["red"])
                    self._redraw_points()
                    self.progress_label.configure(text="Analysis complete")
                    self._set_status("VERIFIED" if agrees else "ERROR")
                    self.busy = False
                elif kind == "benchmark_progress":
                    current, total = payload
                    self.progress.configure(value=100 * current / total)
                    self.progress_label.configure(text=f"Benchmarking dataset {current} of {total}...")
                elif kind == "benchmark":
                    self._display_benchmarks(payload)
                    self.progress.configure(value=100)
                    self.progress_label.configure(text=f"Benchmark complete · {len(payload)} sizes verified")
                    self._set_status("VERIFIED")
                    self.busy = False
                elif kind == "error":
                    self.progress_label.configure(text="Task failed")
                    self._set_status("ERROR")
                    self.busy = False
                    messagebox.showerror("Analysis error", payload, parent=self.root)
        except queue.Empty:
            pass
        if self.busy:
            self.root.after(80, self._poll_results)

    def _display_benchmarks(self, rows):
        axes = self.benchmark_axes
        axes.clear()
        axes.set_facecolor("#0D1728")
        axes.tick_params(colors=COLORS["muted"], labelsize=9)
        for spine in axes.spines.values():
            spine.set_color(COLORS["border"])
        axes.grid(color="#26364D", linewidth=0.7, alpha=0.8)
        sizes = [row["n"] for row in rows]
        brute_times = [row["brute_ms"] for row in rows]
        divide_times = [row["divide_ms"] for row in rows]
        axes.plot(sizes, brute_times, marker="o", markersize=5, color=COLORS["red"], linewidth=2, label="Brute force · O(N²)")
        axes.plot(sizes, divide_times, marker="o", markersize=5, color=COLORS["blue"], linewidth=2, label="Divide & conquer · O(N log N)")
        axes.set_title("Running Time vs Input Size", color=COLORS["text"], fontsize=13, pad=12)
        axes.set_xlabel("Number of points N", color=COLORS["muted"])
        axes.set_ylabel("Execution time (ms)", color=COLORS["muted"])
        axes.legend(facecolor=COLORS["panel"], edgecolor=COLORS["border"], labelcolor=COLORS["text"])
        self.benchmark_figure.tight_layout(pad=1.8)
        self.benchmark_canvas.draw_idle()
        for item in self.benchmark_table.get_children():
            self.benchmark_table.delete(item)
        for row in rows:
            self.benchmark_table.insert("", "end", values=(row["n"], f"{row['brute_ms']:.3f}", f"{row['divide_ms']:.3f}", f"{row['distance']:.6f}"))

    def _reset(self):
        if self.busy:
            return
        self.n_var.set("120")
        self.minimum_var.set("-100")
        self.maximum_var.set("100")
        self.seed_var.set("2026")
        self.max_benchmark_var.set("1600")
        self._generate_points()
        for item in self.benchmark_table.get_children():
            self.benchmark_table.delete(item)
        axes = self.benchmark_axes
        axes.clear()
        axes.set_facecolor("#0D1728")
        axes.set_title("Running Time vs Input Size", color=COLORS["text"])
        axes.set_xlabel("Number of points N", color=COLORS["muted"])
        axes.set_ylabel("Execution time (ms)", color=COLORS["muted"])
        self.benchmark_canvas.draw_idle()


def main():
    root = tk.Tk()
    ClosestPairApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()