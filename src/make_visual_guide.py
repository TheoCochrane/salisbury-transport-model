"""Build docs/toy-model-visual-guide.pdf: the toy model explained in figures.

The guide carries no code. It runs the notebook's own code cells to get the model
values, then draws its own figures from them, so every number in the PDF is the
number the notebook produces.

Usage:  python src/make_visual_guide.py
"""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon

REPO = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO / "notebooks" / "toy_model.ipynb"
OUT = REPO / "docs" / "toy-model-visual-guide.pdf"

# --- look -------------------------------------------------------------------

INK = "#1d2b36"
SOFT = "#5f7484"
FAINT = "#9aabb8"
RULE = "#c9d3db"
TINT = "#eef3f7"
BLUE = "#2b6ca3"
ACCENT = "#b3581d"
GOOD = "#2d7a55"
BAD = "#a8402b"

SERIF = ["Constantia", "Cambria", "Palatino Linotype", "DejaVu Serif", "serif"]
SANS = ["Segoe UI", "Corbel", "Candara", "DejaVu Sans", "sans-serif"]

plt.rcParams.update({
    "font.family": SERIF,
    "axes.edgecolor": RULE,
    "axes.labelcolor": SOFT,
    "xtick.color": SOFT,
    "ytick.color": SOFT,
    "text.color": INK,
    "axes.titlecolor": INK,
    "pdf.fonttype": 42,
    "figure.dpi": 110,
})

PAGE_W, PAGE_H = 8.27, 11.69          # A4 portrait, inches
ML, MR, MT, MB = 0.95, 0.95, 0.80, 0.75
TW = PAGE_W - ML - MR


# --- page construction ------------------------------------------------------

class Page:
    """One A4 page. Everything is placed in inches from the top-left corner."""

    def __init__(self, book, section=""):
        self.book = book
        self.section = section
        self.fig = plt.figure(figsize=(PAGE_W, PAGE_H), facecolor="white")
        self.y = MT
        book.pages.append(self)
        self.number = len(book.pages)

    # coordinate helpers: inches -> figure fraction
    def fx(self, x):
        return x / PAGE_W

    def fy(self, y):
        return 1.0 - y / PAGE_H

    def rule(self, y=None, x0=ML, x1=None, colour=RULE, lw=0.7):
        y = self.y if y is None else y
        x1 = PAGE_W - MR if x1 is None else x1
        self.fig.add_artist(Line2D([self.fx(x0), self.fx(x1)], [self.fy(y), self.fy(y)],
                                   color=colour, linewidth=lw))

    def text(self, s, size=10.5, font=SERIF, colour=INK, x=ML, weight="normal",
             style="normal", ha="left", dy=0.0):
        self.fig.text(self.fx(x), self.fy(self.y + dy), s, fontsize=size, family=font,
                      color=colour, fontweight=weight, fontstyle=style, ha=ha, va="baseline")

    def space(self, inches):
        self.y += inches

    def title(self, s, eyebrow=None):
        if eyebrow:
            self.text(eyebrow.upper(), size=8, font=SANS, colour=ACCENT)
            self.y += 0.22
        self.text(s, size=20, font=SANS, colour=INK)
        self.y += 0.30

    def heading(self, s):
        self.y += 0.08
        self.text(s, size=12.5, font=SANS, colour=INK)
        self.y += 0.24

    def _measure_rich(self, line, size, font=None):
        """Width of a line in inches, honouring **bold** runs."""
        total = 0.0
        for i, run in enumerate(line.split("**")):
            if run:
                total += self._measure(run, size, "bold" if i % 2 else "normal", font)
        return total

    def wrap(self, s, size, width, font=None):
        """Greedy line breaking measured in inches, so a line never leaves the margin."""
        lines, cur = [], ""
        for word in s.split():
            trial = f"{cur} {word}".strip()
            if not cur or self._measure_rich(trial, size, font) <= width:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines or [""]

    def para(self, s, size=10.5, colour=INK, lead=0.185, width=None, gap=0.13):
        """Wrap and draw a paragraph. **bold** spans are rendered bold."""
        for line in self.wrap(s, size, width or TW):
            self._rich_line(line, size, colour)
            self.y += lead
        self.y += gap

    def _measure(self, s, size, weight, font=None):
        """Width of `s` in inches. A sentinel keeps trailing spaces from being dropped."""
        renderer = self.fig.canvas.get_renderer()
        widths = []
        for probe in (s + "|", "|"):
            t = self.fig.text(0, 0, probe, fontsize=size, family=font or SERIF,
                              fontweight=weight)
            widths.append(t.get_window_extent(renderer=renderer).width / self.fig.dpi)
            t.remove()
        return widths[0] - widths[1]

    def _rich_line(self, line, size, colour):
        """Draw one line, honouring **bold** markers, by measuring each run."""
        if "**" not in line:
            self.text(line, size=size, colour=colour)
            return
        x = ML
        for i, run in enumerate(line.split("**")):
            if not run:
                continue
            weight = "bold" if i % 2 else "normal"
            self.fig.text(self.fx(x), self.fy(self.y), run, fontsize=size, family=SERIF,
                          color=colour, fontweight=weight, va="baseline")
            x += self._measure(run, size, weight)

    def bullets(self, items, size=10.5, lead=0.185):
        for item in items:
            lines = self.wrap(item, size, TW - 0.22)
            self.text("—", size=size, colour=ACCENT)
            for k, line in enumerate(lines):
                self.fig.text(self.fx(ML + 0.22), self.fy(self.y), line, fontsize=size,
                              family=SERIF, color=INK, va="baseline")
                self.y += lead
            self.y += 0.05
        self.y += 0.08

    def callout(self, body, label="TAG", height=None, colour=ACCENT):
        """A tinted box for a reference or an aside."""
        lines = self.wrap(body, 9, TW - 0.80)
        h = height or (0.20 + 0.165 * len(lines))
        self.fig.patches.append(Rectangle(
            (self.fx(ML), self.fy(self.y + h)), TW / PAGE_W, h / PAGE_H,
            transform=self.fig.transFigure, facecolor=TINT, edgecolor="none", zorder=0))
        self.fig.add_artist(Line2D([self.fx(ML), self.fx(ML)],
                                   [self.fy(self.y + h), self.fy(self.y)],
                                   color=colour, linewidth=1.6))
        self.y += 0.165
        self.fig.text(self.fx(ML + 0.16), self.fy(self.y), label.upper(), fontsize=7.5,
                      family=SANS, color=colour, va="baseline")
        for k, line in enumerate(lines):
            self.fig.text(self.fx(ML + 0.62), self.fy(self.y), line, fontsize=9,
                          family=SERIF, color=INK, va="baseline")
            self.y += 0.165
        self.y += 0.14

    def figure(self, draw, height, caption=None, pad=0.10, width=None, x=None,
               below=0.0):
        """Carve out an axes region and hand it to `draw(ax)`.

        `below` reserves space under the axes box for tick labels, an axis label or a
        legend, which matplotlib draws outside the rectangle we asked for.
        """
        w = width or TW
        x = ML if x is None else x
        ax = self.fig.add_axes([self.fx(x), self.fy(self.y + height),
                                w / PAGE_W, height / PAGE_H])
        ax.set_facecolor("white")
        draw(ax)
        self.y += height + below + pad
        if caption:
            for line in self.wrap(caption, 8.5, w, font=SANS):
                self.fig.text(self.fx(x), self.fy(self.y), line, fontsize=8.5,
                              family=SANS, color=SOFT, va="baseline")
                self.y += 0.155
            self.y += 0.08
        return ax

    def table(self, rows, widths, header=None, size=9.5, lead=0.215, align=None):
        """A plain rule-separated table. `widths` are fractions of the text width."""
        xs, acc = [], 0.0
        for frac in widths:
            xs.append(ML + acc * TW)
            acc += frac
        align = align or ["left"] * len(widths)

        def row(cells, weight="normal", colours=None, font=SERIF):
            for k, cell in enumerate(cells):
                col = (colours or [INK] * len(cells))[k]
                ha = align[k]
                x = xs[k] + (widths[k] * TW - 0.06 if ha == "right" else 0.0)
                self.fig.text(self.fx(x), self.fy(self.y), str(cell), fontsize=size,
                              family=font, color=col, fontweight=weight, ha=ha, va="baseline")
            self.y += lead

        if header:
            row(header, colours=[SOFT] * len(header), font=SANS)
            self.y -= 0.07
            self.rule()
            self.y += 0.15
        for r in rows:
            cells = r["cells"] if isinstance(r, dict) else r
            row(cells, colours=r.get("colours") if isinstance(r, dict) else None)
        self.y += 0.06

    def finish(self):
        """Running foot: section on the left, page number on the right."""
        y = PAGE_H - MB + 0.28
        self.fig.add_artist(Line2D([self.fx(ML), self.fx(PAGE_W - MR)],
                                   [self.fy(y - 0.16)] * 2, color=RULE, linewidth=0.7))
        if self.section:
            self.fig.text(self.fx(ML), self.fy(y), self.section, fontsize=8,
                          family=SANS, color=FAINT, va="baseline")
        self.fig.text(self.fx(PAGE_W - MR), self.fy(y), str(self.number), fontsize=8,
                      family=SANS, color=FAINT, ha="right", va="baseline")


class Book:
    def __init__(self):
        self.pages = []

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with PdfPages(path) as pdf:
            for page in self.pages:
                page.finish()
                pdf.savefig(page.fig)
                plt.close(page.fig)
            info = pdf.infodict()
            info["Title"] = "The toy four-zone model, in pictures"
            info["Subject"] = "A visual walkthrough of a four-step transport model"
            info["Keywords"] = "transport modelling, four-step model, TAG, Salisbury"
        return path


# --- the model --------------------------------------------------------------

def load_model():
    """Run the notebook's code cells and hand back everything they defined."""
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    code = code.replace("%matplotlib inline", "").replace("plt.show()", "pass")
    env = {"__name__": "__main__", "display": lambda *a, **k: None}
    plt.rcParams["figure.max_open_warning"] = 0
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(code, str(NOTEBOOK), "exec"), env)
    plt.close("all")
    return env


M = load_model()
ZONES, POS, n, idx = M["ZONES"], M["POS"], M["n"], M["idx"]
links, c, best = M["links"], M["c"], M["best"]
W, H, zone_corner = M["W"], M["H"], M["zone_corner"]


# --- shared drawing ---------------------------------------------------------

def frame_off(ax, xlim=(0, 8), ylim=(0, 6)):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_nodes(ax, size=330, fs=10.5, colour=BLUE):
    for z, (x, y) in POS.items():
        ax.scatter(x, y, s=size, color=colour, zorder=4)
        ax.text(x, y, z, color="white", ha="center", va="center",
                fontsize=fs, fontweight="bold", zorder=5, family=SANS)


def draw_links(ax, widths=None, colour=FAINT, labels=None, label_size=8):
    centre = np.array([4.0, 3.0])
    for k, row in links.iterrows():
        (x1, y1), (x2, y2) = POS[row["from"]], POS[row["to"]]
        lw = 2.4 if widths is None else widths[k]
        ax.plot([x1, x2], [y1, y2], color=colour, linewidth=lw,
                solid_capstyle="round", zorder=2)
        if labels is not None:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            d = np.array([mx, my]) - centre
            nrm = np.hypot(*d)
            if nrm:
                mx, my = np.array([mx, my]) + 0.62 * d / nrm
            ax.text(mx, my, labels[k], ha="center", va="center", fontsize=label_size,
                    family=SANS, color=INK, zorder=6,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.92, pad=1.2))


def draw_zone_boxes(ax, face=TINT, edge=RULE, dashed=False):
    for z, (x, y) in zone_corner.items():
        ax.add_patch(Rectangle((x, y), W, H, facecolor="none" if dashed else face,
                               edgecolor=edge, linewidth=1.0,
                               linestyle="--" if dashed else "-", zorder=0))


def stage_diagram(ax, active=(), feedback=False):
    names = ["1. Trip generation\nhow many trips", "2. Trip distribution\nwhere they go",
             "3. Mode choice\ncar or bus", "4. Assignment\nwhich roads"]
    ax.set_xlim(0, 10.4)
    ax.set_ylim(-0.9 if feedback else -0.1, 1.45)
    ax.axis("off")
    for k, label in enumerate(names):
        on = (k + 1) in active
        x = k * 2.6
        ax.add_patch(FancyBboxPatch((x, 0.1), 2.1, 1.1, boxstyle="round,pad=0.04",
                                    facecolor="#d6e4f2" if on else "#f4f7f9",
                                    edgecolor=BLUE if on else RULE,
                                    linewidth=1.6 if on else 0.9))
        ax.text(x + 1.05, 0.65, label, ha="center", va="center", fontsize=8.5,
                family=SANS, color=INK if on else FAINT,
                fontweight="bold" if on else "normal")
        if k < 3:
            ax.annotate("", xy=(x + 2.48, 0.65), xytext=(x + 2.18, 0.65),
                        arrowprops=dict(arrowstyle="->", color=SOFT, lw=1.0))
    if feedback:
        a, b = 3 * 2.6 + 1.05, 1 * 2.6 + 1.05
        ax.plot([a, a], [0.1, -0.35], color=BAD, ls="--", lw=1.1)
        ax.plot([a, b], [-0.35, -0.35], color=BAD, ls="--", lw=1.1)
        ax.annotate("", xy=(b, 0.1), xytext=(b, -0.35),
                    arrowprops=dict(arrowstyle="->", color=BAD, ls="--", lw=1.1))
        ax.text((a + b) / 2, -0.62, "not in this model: congested times do not feed back",
                ha="center", fontsize=8, family=SANS, color=BAD)


def matrix_plot(ax, Mx, title=None, fmt="{:.0f}", cmap="Blues", labels=ZONES):
    im = ax.imshow(Mx, cmap=cmap)
    top = np.nanmax(Mx)
    for i in range(Mx.shape[0]):
        for j in range(Mx.shape[1]):
            ax.text(j, i, fmt.format(Mx[i, j]), ha="center", va="center", fontsize=8.5,
                    family=SANS, color="white" if Mx[i, j] > 0.6 * top else INK)
    ax.set_xticks(range(len(labels)), labels, fontsize=9, family=SANS)
    ax.set_yticks(range(len(labels)), labels, fontsize=9, family=SANS)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    if title:
        ax.set_xlabel(title, fontsize=8.5, family=SANS, color=SOFT, labelpad=6)
    return im


def tidy(ax, xlabel=None, ylabel=None, title=None):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8.5, length=3)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_family(SANS)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, family=SANS)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, family=SANS)
    if title:
        ax.set_title(title, fontsize=10, family=SANS, pad=8)


# --- pages ------------------------------------------------------------------

def page_cover(book):
    p = Page(book)
    p.y = 1.35
    p.text("A FOUR-STEP TRANSPORT MODEL, IN PICTURES", size=9, font=SANS, colour=ACCENT)
    p.y += 0.52
    p.text("The toy", size=38, font=SANS)
    p.y += 0.52
    p.text("four-zone model", size=38, font=SANS)
    p.y += 0.30
    p.rule(x1=ML + 2.0, colour=ACCENT, lw=2.0)
    p.y += 0.42
    p.para("Four zones, five roads and a thousand journeys an hour. Every number in this "
           "guide is made up, and small enough to check by hand. Nothing here is Salisbury "
           "data. What it does show is every step a real model takes, in the order it takes "
           "them, with a picture for each one.", size=12, lead=0.235)
    p.y += 0.10
    p.para("The companion notebook, notebooks/toy_model.ipynb, does all of this in code. "
           "This guide is the same model with the code taken out.", size=11, colour=SOFT,
           lead=0.215)

    p.y = 5.05

    def map_fig(ax):
        draw_zone_boxes(ax)
        draw_links(ax, widths=[links.loc[k, "capacity_vph"] / 42 for k in links.index],
                   colour=FAINT)
        draw_nodes(ax, size=520, fs=13)
        frame_off(ax, (-0.3, 8.3), (-0.3, 6.3))

    p.figure(map_fig, 4.6, pad=0.16)

    p.y = PAGE_H - MB - 1.25
    p.rule()
    p.y += 0.30
    p.table(
        [["Zones", "4 (A, B, C, D)"],
         ["Roads", "5, two-way"],
         ["Journeys modelled", f"{M['T_all'].sum():,.0f} an hour, for two trip purposes"],
         ["Cars on the network", f"{M['V_car'].sum():,.0f} an hour"]],
        widths=[0.30, 0.70], size=10)


def page_overview(book):
    p = Page(book, "How the guide is built")
    p.title("Seven levels, one idea at a time", eyebrow="How to read this")
    p.para("A transport model answers one question: if we change something, who travels "
           "where, by what, on which roads? It answers it in four steps, always in the same "
           "order. Each step hands its answer to the next.")
    p.figure(lambda ax: stage_diagram(ax, active=(1, 2, 3, 4)), 1.35,
             caption="The four steps. Trip generation is given to us in this toy model, "
                     "so the guide builds the other three.")
    p.para("The model is assembled in seven levels. Each level keeps everything from the "
           "level before and adds exactly one idea, so you can stop anywhere and still have "
           "a working model.")
    p.table(
        [["0", "From real places to a map of zones and roads", "—"],
         ["1", "Where work trips go, using travel time only", "2"],
         ["2", "A second kind of trip: shopping and leisure", "2"],
         ["3", "Turning money, walking and waiting into minutes", "3"],
         ["4", "Choosing between car and bus", "3"],
         ["5", "Putting cars on the roads, and congestion", "4"],
         ["6", "Checking the model against counts", "all"]],
        widths=[0.09, 0.73, 0.18], header=["Level", "What it adds", "Step"],
        align=["left", "left", "left"], size=10, lead=0.235)
    p.y += 0.12
    p.heading("What the model never sees")
    p.para("Every simplification below is deliberate, and each one is a place the model can "
           "be wrong. Writing them down is part of the method, not an apology for it.")
    p.table(
        [["Where in a zone a journey starts", "one point per zone"],
         ["One-way roads", "every road runs the same both ways"],
         ["Modes other than car and bus", "no walking, cycling or rail"],
         ["Time of day", "the morning peak hour only"],
         ["Congestion changing destinations", "journeys are distributed at free-flow times"]],
        widths=[0.52, 0.48], header=["Left out", "Instead"], size=9.5, lead=0.225)


def page_level0_a(book):
    p = Page(book, "Level 0 — from the real world to a network")
    p.title("Real places become four zones", eyebrow="Level 0")
    p.para("A real town is a scatter of places of different shapes and sizes: houses, a "
           "works, a school, some shops. No model can hold every one of them, so the first "
           "job is to throw most of the detail away on purpose.")

    PLACES, SHAPE, COLOUR = M["PLACES"], M["SHAPE"], M["COLOUR"]
    recolour = {"home": BLUE, "work": ACCENT, "school": "#6b4f9e", "shop": GOOD}

    def places(ax, boxes=False):
        for name, (kind, cx, cy, r) in PLACES.items():
            ax.add_patch(Polygon(SHAPE[name], closed=True, facecolor=recolour[kind],
                                 alpha=0.22, edgecolor=recolour[kind], linewidth=1.0))
            ax.text(cx, cy, name, ha="center", va="center", fontsize=8, family=SANS,
                    color=INK)
        if boxes:
            draw_zone_boxes(ax, dashed=True, edge=ACCENT)
            for z, (x, y) in zone_corner.items():
                ax.text(x + 0.18, y + H - 0.22, z, fontsize=13, fontweight="bold",
                        family=SANS, color=ACCENT, va="top")
        frame_off(ax, (-0.3, 8.3), (-0.3, 6.3))

    half = (TW - 0.25) / 2
    y0 = p.y
    p.figure(lambda ax: places(ax, False), 3.15, width=half, x=ML, pad=0.0)
    p.y = y0
    p.figure(lambda ax: places(ax, True), 3.15, width=half, x=ML + half + 0.25,
             pad=0.12)
    p.para("**Left:** the places themselves, as irregular as real places are.", size=10,
           gap=0.02)
    p.para("**Right:** four boxes drawn over them. From here on, everything inside a box is "
           "one place. We lose which house a journey starts from; we gain a table of four "
           "rows that a person can check.", size=10)

    def dots(ax):
        draw_zone_boxes(ax, dashed=True)
        for z, (x, y) in POS.items():
            ax.annotate("", xy=(x, y), xytext=(x + 1.4, y + 0.9),
                        arrowprops=dict(arrowstyle="->", color=FAINT, lw=0.9, ls=":"))
        draw_nodes(ax, size=430, fs=12)
        frame_off(ax, (-0.3, 8.3), (-0.3, 6.3))

    def network(ax):
        draw_zone_boxes(ax, dashed=True)
        draw_links(ax, colour=FAINT)
        ax.plot([POS["B"][0], POS["D"][0]], [POS["B"][1], POS["D"][1]],
                color=BAD, lw=1.1, ls="--", zorder=1)
        ax.text(4.0, 3.12, "no road B to D", ha="center", fontsize=8, family=SANS,
                color=BAD, rotation=36.9,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.0))
        draw_nodes(ax, size=430, fs=12)
        frame_off(ax, (-0.3, 8.3), (-0.3, 6.3))

    y0 = p.y
    p.figure(dots, 3.15, width=half, x=ML, pad=0.0)
    p.y = y0
    p.figure(network, 3.15, width=half, x=ML + half + 0.25, pad=0.12)
    p.para("**Left:** each zone shrinks to a single point, its centroid. Every journey in "
           "that zone now starts and ends there.", size=10, gap=0.02)
    p.para("**Right:** the roads between the points. B and D have no road between them, so "
           "that journey has to go round through C.", size=10)


def page_level0_b(book):
    p = Page(book, "Level 0 — from the real world to a network")
    p.title("Roads get times; zones keep their size", eyebrow="Level 0")
    p.para("A road needs numbers before the model can use it. Each gets a free-flow time, "
           "which is how long it takes when empty, and a capacity in vehicles per hour. The "
           "time is used from the next page onwards. The capacity is not needed until "
           "congestion arrives at Level 5.")

    def net_times(ax):
        draw_zone_boxes(ax)
        draw_links(
            ax, widths=[links.loc[k, "capacity_vph"] / 42 for k in links.index],
            labels=[f"{r['from']}–{r['to']}\n{r['free_flow_min']:.0f} min\n"
                    f"{r['capacity_vph']:.0f} veh/h" for _, r in links.iterrows()],
            label_size=8)
        draw_nodes(ax, size=430, fs=12)
        for z, (x, y) in zone_corner.items():
            ax.text(x + 0.15, y + 0.15, f"{W*H} km²", fontsize=7.5, family=SANS,
                    color=FAINT, va="bottom")
        frame_off(ax, (-0.9, 8.9), (-0.6, 6.6))

    p.figure(net_times, 3.5,
             caption="The whole network. Line thickness is capacity, so the thicker a road, "
                     "the more traffic it can carry before it slows down.")

    p.heading("A journey that never leaves its zone")
    p.para("Some journeys start and end inside the same zone. They are short, but they are "
           "not free. Give them a cost of zero and the model decides that staying put is "
           "the most attractive journey in town, because the next page rewards cheap "
           "journeys. The rule used here is half the time to the nearest other zone.")

    def intra(ax):
        ax.add_patch(Rectangle((0, 0), 4, 3, facecolor=TINT, edgecolor=RULE, lw=1.0))
        ax.add_patch(Rectangle((4.8, 0), 4, 3, facecolor=TINT, edgecolor=RULE, lw=1.0))
        for (x, y), z in [((2, 1.5), "A"), ((6.8, 1.5), "B")]:
            ax.scatter(x, y, s=330, color=BLUE, zorder=3)
            ax.text(x, y, z, color="white", ha="center", va="center", fontsize=10.5,
                    fontweight="bold", family=SANS, zorder=4)
        ax.annotate("", xy=(3.3, 2.45), xytext=(0.7, 2.45),
                    arrowprops=dict(arrowstyle="<->", color=ACCENT, lw=1.6))
        ax.text(2, 2.66, f"inside zone A: {c[0,0]:.0f} min", ha="center", fontsize=8.5,
                family=SANS, color=ACCENT)
        ax.annotate("", xy=(6.4, 1.5), xytext=(2.4, 1.5),
                    arrowprops=dict(arrowstyle="-|>", color=SOFT, lw=1.2, ls="--"))
        ax.text(4.4, 1.72, f"to zone B: {best[0,1]:.0f} min", ha="center", fontsize=8.5,
                family=SANS, color=SOFT)
        frame_off(ax, (-0.3, 9.1), (-0.3, 3.4))

    p.figure(intra, 1.7,
             caption="Zone A's nearest neighbour is ten minutes away, so a journey inside A "
                     "is given five.")
    p.callout("A measure of intra-zonal costs should be estimated. It is common to assume a "
              "value based on the cost to adjacent zones. Some models for example adopt half "
              "the lowest inter-zonal cost. — TAG M2.2 §5.2.28. Matches TAG.",
              label="TAG")


def page_part_a(book):
    p = Page(book, "Level 1 — Part A, travel times")
    p.title("How long it takes between every pair", eyebrow="Part A")
    p.figure(lambda ax: stage_diagram(ax, active=(2,)), 1.25, pad=0.14)
    p.para("The roads carry the times; the model needs the times between **zones**. For "
           "most pairs that is just the road between them. For B and D, which have no road, "
           "it is the quickest way round. With five roads you can do this in your head.")

    rows = []
    for (a, b), (mins, route) in M["shortest_by_hand"].items():
        direct = M["link_time"][idx[a], idx[b]]
        rows.append([f"{a} to {b}",
                     "no road" if np.isinf(direct) else f"{direct:.0f} min",
                     f"{mins:.0f} min", route])
    p.table(rows, widths=[0.18, 0.22, 0.22, 0.38],
            header=["Pair", "Direct road", "Quickest", "Route taken"], size=10, lead=0.235)
    p.y += 0.06
    p.para("Only one pair out of six needs a route of more than one road. In a real network "
           "of thousands of roads, almost every pair does, which is why models use a "
           "shortest-path algorithm rather than a person.", size=10, colour=SOFT)

    def times(ax):
        im = matrix_plot(ax, c, title="travel time between zones, minutes")
        ax.set_ylabel("from", fontsize=9, family=SANS, color=SOFT)

    def routes(ax):
        ax.set_xlim(0, 3)
        ax.set_ylim(0, 3)
        ax.axis("off")
        for k, (zones, used) in enumerate(sorted(
                M["paths"][("A", "C")], key=M["free_flow_total"])):
            total = M["free_flow_total"]((zones, used))
            y = 2.4 - k * 0.9
            ax.text(0.0, y, " → ".join(zones), fontsize=10, family=SANS,
                    color=ACCENT if k == 0 else INK, va="center")
            ax.text(2.9, y, f"{total:.0f} min", fontsize=10, family=SANS,
                    color=ACCENT if k == 0 else SOFT, va="center", ha="right")
            if k == 0:
                ax.text(0.0, y - 0.34, "quickest, so this is the one the model uses",
                        fontsize=8, family=SANS, color=SOFT, va="center")

    half = (TW - 0.3) / 2
    y0 = p.y
    p.figure(times, 2.1, width=half - 0.25, x=ML + 0.18, pad=0.0)
    p.y = y0 + 0.25
    p.figure(routes, 1.8, width=half, x=ML + half + 0.3, pad=0.12)
    p.y = max(p.y, y0 + 2.35)
    p.para("**Left:** the finished table of times, including the diagonal for journeys "
           "inside a zone.", size=10, gap=0.02)
    p.para("**Right:** the three ways from A to C. Every journey in the model takes the "
           "quickest route available to it.", size=10)


def page_part_bc(book):
    p = Page(book, "Level 1 — Parts B and C")
    p.title("How many journeys, and how far people will go", eyebrow="Parts B and C")
    p.para("Two inputs remain. First, how many journeys start and end in each zone. "
           "Journeys that start must also end, so the two totals have to match: the "
           "starting figures are kept and the ending figures scaled to agree with them.")

    P_w, A_w = M["P_w"], M["A_w"]

    def pa(ax):
        hub = np.array([4.0, 3.0])

        def turn(v, deg):
            t = np.radians(deg)
            return np.array([v[0]*np.cos(t) - v[1]*np.sin(t), v[0]*np.sin(t) + v[1]*np.cos(t)])

        for k, z in enumerate(ZONES):
            q = np.array(POS[z], float)
            out = (q - hub) / np.linalg.norm(q - hub)
            for ang, colour, val, lab, outward in [(26, ACCENT, P_w[k], "start", True),
                                                   (-26, GOOD, A_w[k], "end", False)]:
                d = turn(out, ang)
                tip, tail = (q + 1.5 * d, q + 0.42 * d) if outward else (q + 0.42 * d, q + 1.5 * d)
                ax.annotate("", xy=tip, xytext=tail,
                            arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.5))
                ax.text(*(q + 1.62 * d), f"{val:.0f}", color=colour, fontsize=9,
                        family=SANS, ha="left" if d[0] > 0 else "right", va="center")
        draw_links(ax, colour="#e3eaf0", widths=[1.2] * 5)
        draw_nodes(ax, size=400, fs=11.5)
        ax.text(4.0, -0.9, "orange: journeys starting   ·   green: journeys ending",
                ha="center", fontsize=8.5, family=SANS, color=SOFT)
        frame_off(ax, (-1.6, 9.6), (-1.5, 7.5))

    p.figure(pa, 2.9,
             caption=f"A thousand journeys an hour in all. Zone A is the big employer, so "
                     f"{A_w[0]:.0f} journeys end there against the {P_w[0]:.0f} that start.")

    p.heading("Distance puts people off")
    p.para("The second input is how much travel time discourages a journey. Two things fix "
           "its shape: people prefer shorter journeys, and each extra minute puts off the "
           "same share of them rather than the same number. Ten minutes to twenty costs "
           "as much, proportionally, as forty to fifty.")

    beta_w, deterrence = M["beta_w"], M["deterrence"]

    def curve(ax):
        t = np.linspace(0, 60, 300)
        ax.plot(t, deterrence(t, beta_w), color=ACCENT, lw=1.8)
        for mins in (10, 20, 30, 40):
            ax.plot([mins, mins], [0, deterrence(mins, beta_w)], color=FAINT, lw=0.7, ls=":")
            ax.scatter([mins], [deterrence(mins, beta_w)], s=16, color=ACCENT, zorder=3)
            ax.text(mins, deterrence(mins, beta_w) + 0.045,
                    f"{deterrence(mins, beta_w):.2f}", ha="center", fontsize=8, family=SANS,
                    color=SOFT)
        ax.set_xlim(0, 60)
        ax.set_ylim(0, 1.12)
        tidy(ax, "travel time (minutes)", "weight given to the journey")

    p.figure(curve, 2.2, width=TW * 0.74, x=ML + TW * 0.13, below=0.46,
             caption="Each ten minutes multiplies the weight by about 0.61, however far "
                     "along the curve you start. The weight is not a number of journeys "
                     "yet; it only says how attractive a journey of that length is.")
    p.callout("It is expected that the model form will generally be logit. — TAG M2.1 "
              "§4.9.14. The exponential used here is one of the forms TAG describes. "
              "The value 0.05 per minute is a placeholder until it is calibrated against "
              "observed trip lengths (TAG M2.2 §5.2.31).", label="TAG")


def page_part_de(book):
    p = Page(book, "Level 1 — Parts D and E")
    p.title("A first guess, then balancing it", eyebrow="Parts D and E")
    p.para("Multiply the three things together — journeys starting, journeys ending, "
           "and the weight for that travel time — and you have a first guess at every "
           "pair in the town. It is Newton's gravity: two bodies pull on each other in "
           "proportion to their size, and the pull falls away with distance.")

    P_w, A_w, F_w, T0 = M["P_w"], M["A_w"], M["F_w"], M["T0"]
    i0, j0 = idx["A"], idx["B"]

    def guess(ax):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 2.6)
        ax.axis("off")
        parts = [(1.0, f"{P_w[i0]:.0f}", "starting in A"),
                 (3.4, f"{A_w[j0]:.0f}", "ending in B"),
                 (5.8, f"{F_w[i0, j0]:.2f}", "weight at 10 min")]
        for x, val, lab in parts:
            ax.text(x, 1.55, val, fontsize=19, family=SANS, ha="center", color=INK)
            ax.text(x, 1.05, lab, fontsize=8.5, family=SANS, ha="center", color=SOFT)
        for x in (2.2, 4.6):
            ax.text(x, 1.55, "×", fontsize=15, family=SANS, ha="center", color=ACCENT)
        ax.text(7.0, 1.55, "=", fontsize=15, family=SANS, ha="center", color=ACCENT)
        ax.text(8.4, 1.55, f"{T0[i0, j0]:,.0f}", fontsize=19, family=SANS, ha="center",
                color=ACCENT)
        ax.text(8.4, 1.05, "journeys A to B", fontsize=8.5, family=SANS, ha="center",
                color=SOFT)
        ax.plot([0.4, 9.6], [0.62, 0.62], color=RULE, lw=0.8)
        ax.text(5.0, 0.22, f"but only {P_w[i0]:.0f} people leave A altogether",
                fontsize=10, family=SANS, ha="center", color=BAD)

    p.figure(guess, 1.5, pad=0.14)
    p.para("The guess is roughly eighty times too big, because nothing in it forces the "
           "totals to come out right. Fixing that is the next step.")

    p.heading("Fixing the rows and columns by turns")
    p.para("Scale every row so it adds up to the journeys starting there, and the columns "
           "go wrong. Scale every column, and the rows go slightly wrong. Repeat. Each pass "
           "the error is smaller, and within a few passes both are right at once.")

    M0 = T0.copy()
    M1 = M0 * (P_w / M0.sum(axis=1))[:, None]
    M2 = M1 * (A_w / M1.sum(axis=0))[None, :]
    top = M2.max()

    def margins(ax, Mx, title):
        ax.imshow(Mx, cmap="Blues", vmin=0, vmax=top * 1.1)
        for i in range(n):
            for j in range(n):
                ax.text(j, i, f"{Mx[i, j]:,.0f}", ha="center", va="center", fontsize=6.5,
                        family=SANS, color="white" if Mx[i, j] > 0.6 * top else INK)
        for i in range(n):
            ok = np.isclose(Mx.sum(axis=1)[i], P_w[i], rtol=5e-3)
            ax.text(n - 0.35, i, f"{Mx.sum(axis=1)[i]:,.0f}", ha="left", va="center",
                    fontsize=7, family=SANS, color=GOOD if ok else BAD, fontweight="bold")
        for j in range(n):
            ok = np.isclose(Mx.sum(axis=0)[j], A_w[j], rtol=5e-3)
            ax.text(j, n - 0.3, f"{Mx.sum(axis=0)[j]:,.0f}", ha="center", va="center",
                    fontsize=7, family=SANS, color=GOOD if ok else BAD, fontweight="bold")
        ax.set_xticks(range(n), ZONES, fontsize=8, family=SANS)
        ax.set_yticks(range(n), ZONES, fontsize=8, family=SANS)
        ax.set_xlim(-0.55, n + 0.95)
        ax.set_ylim(n + 0.1, -0.6)
        ax.xaxis.tick_top()
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xlabel(title, fontsize=8.5, family=SANS, color=SOFT, labelpad=4)

    third = (TW - 0.9) / 3
    y0 = p.y
    for k, (Mx, title) in enumerate([(M0, "the first guess"),
                                     (M1, "rows made right"),
                                     (M2, "then columns")]):
        p.y = y0
        p.figure(lambda ax, Mx=Mx, t=title: margins(ax, Mx, t), 2.0, width=third,
                 x=ML + k * (third + 0.45), pad=0.0)
    p.y = y0 + 2.45
    p.para("Green means a total matches its target and red means it does not. The numbers "
           "down the right are row totals; those along the bottom are column totals.",
           size=9.5, colour=SOFT)

    p.para(f"On these numbers {len(M['furness_hist'])} passes are enough: after the last "
           f"one, no total moves by more than a tenth of a percent, which is where the "
           f"model stops. Nothing about the journeys has changed — only how they are "
           f"shared out between the pairs of zones.")


def page_matrix(book):
    p = Page(book, "Level 1 — the answer, and Level 2")
    p.title("The finished table of journeys", eyebrow="Part E")
    T_w, T_o, c_ = M["T_w"], M["T_o"], c

    half = (TW - 0.45) / 2
    y0 = p.y

    def trips(ax):
        matrix_plot(ax, T_w, title="work journeys per hour")
        ax.set_ylabel("from", fontsize=9, family=SANS, color=SOFT)

    def bands(ax):
        x = np.arange(len(M["BAND_LABELS"]))
        ax.bar(x - 0.19, M["shares_w"].values, width=0.38, color=BLUE, label="work")
        ax.bar(x + 0.19, M["shares_o"].values, width=0.38, color=ACCENT, label="other")
        ax.set_xticks(x, M["BAND_LABELS"], fontsize=8, family=SANS)
        tidy(ax, None, "share of journeys")
        ax.legend(fontsize=8, frameon=False, prop={"family": SANS, "size": 8})

    p.figure(trips, 2.2, width=half - 0.3, x=ML + 0.3, pad=0.0)
    p.y = y0 + 0.1
    p.figure(bands, 2.0, width=half, x=ML + half + 0.45, pad=0.12, below=0.40)
    p.y = max(p.y, y0 + 2.75)
    p.para("**Left:** the balanced table. Every row adds up to the journeys starting in "
           "that zone, every column to the journeys ending there.", size=10, gap=0.02)
    p.para("**Right:** how long those journeys turn out to be. Matching the totals is not "
           "enough on its own — the journeys also have to be the right length, and that "
           "is what calibrating the weight curve against survey data would fix.", size=10)

    p.heading("Level 2: a second kind of journey")
    p.para("Work is only part of the travelling. Shopping, leisure and personal business "
           "behave differently in two ways. Shoppers will not travel as far, so their weight "
           "curve falls faster. And they choose where to go, so their destination figures "
           "are only relative weights rather than fixed totals — which means no "
           "balancing loop is needed at all, just one pass.")

    def two_curves(ax):
        t = np.linspace(0, 60, 300)
        ax.plot(t, M["deterrence"](t, M["beta_w"]), color=BLUE, lw=1.8,
                label=f"work, β = {M['beta_w']}")
        ax.plot(t, M["deterrence"](t, M["beta_o"]), color=ACCENT, lw=1.8,
                label=f"other, β = {M['beta_o']}")
        ax.set_xlim(0, 60)
        ax.set_ylim(0, 1.08)
        tidy(ax, "travel time (minutes)", "weight")
        ax.legend(fontsize=8, frameon=False, prop={"family": SANS, "size": 8})

    def desire(ax):
        two = T_o + T_o.T
        scale = two[np.triu_indices(n, 1)].max()
        for a in range(n):
            for b in range(a + 1, n):
                (x1, y1), (x2, y2) = POS[ZONES[a]], POS[ZONES[b]]
                ax.plot([x1, x2], [y1, y2], color=ACCENT, alpha=0.75,
                        lw=0.5 + 5.5 * two[a, b] / scale)
        draw_nodes(ax, size=330, fs=10)
        frame_off(ax, (0.6, 7.4), (0.6, 5.4))

    y0 = p.y
    p.figure(two_curves, 1.95, width=half, x=ML, pad=0.0, below=0.44)
    p.y = y0
    p.figure(desire, 1.95, width=half, x=ML + half + 0.45, pad=0.12)
    p.y = max(p.y, y0 + 2.50)
    p.para(f"**Left:** shoppers give up sooner, so their average journey is "
           f"{M['mean_o']:.1f} minutes against {M['mean_w']:.1f} for work.", size=10,
           gap=0.02)
    p.para(f"**Right:** where the shopping journeys go; a thicker line carries more. The "
           f"town now makes {M['T_all'].sum():,.0f} journeys an hour across both purposes.",
           size=10)


def page_cost_choice(book):
    p = Page(book, "Levels 3 and 4 — cost and choice")
    p.title("Everything in minutes, then a choice", eyebrow="Parts G to I")
    p.figure(lambda ax: stage_diagram(ax, active=(3,)), 1.25, pad=0.14)
    p.para("To compare a car with a bus you need one number for each, in one unit. Money "
           "becomes minutes by dividing by the value of time. Walking and waiting count for "
           "more than sitting in a vehicle, because people dislike them more. The total is "
           "the generalised cost.")

    i0, j0 = idx["A"], idx["B"]
    vot, cm, fare = M["vot"], M["car_money"], M["bus_fare"]
    parts_car = [("in the vehicle", c[i0, j0], BLUE),
                 ("money", cm / vot, ACCENT)]
    parts_bus = [("in the vehicle", M["bus_ivt_factor"] * c[i0, j0], BLUE),
                 ("walk, counted double", M["walk_weight"] * M["walk_min"], "#7fa8c4"),
                 ("wait", M["wait_weight"] * M["wait_min"], "#a9c4d6"),
                 ("fare", fare / vot, ACCENT)]

    def costs(ax):
        seen = set()
        for row_y, parts in [(1, parts_car), (0, parts_bus)]:
            left = 0.0
            for name, val, colour in parts:
                ax.barh(row_y, val, left=left, height=0.46, color=colour,
                        edgecolor="white", linewidth=0.8,
                        label=None if name in seen else name)
                seen.add(name)
                if val > 2.0:
                    ax.text(left + val / 2, row_y, f"{val:g}", ha="center", va="center",
                            fontsize=8.5, family=SANS, color="white")
                left += val
            ax.text(left + 0.5, row_y, f"{left:g} min", va="center", fontsize=10,
                    family=SANS, color=INK)
        ax.set_yticks([1, 0], ["car", "bus"], fontsize=10, family=SANS)
        ax.set_xlim(0, 36)
        ax.set_ylim(-0.6, 1.6)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0, labelsize=9)
        ax.set_xlabel("minutes", fontsize=9, family=SANS)
        ax.legend(fontsize=8, frameon=False, ncol=4, loc="lower center",
                  bbox_to_anchor=(0.5, -0.52), prop={"family": SANS, "size": 8})

    p.figure(costs, 1.75, below=1.02, caption="One journey, A to B. The fare of £1.80 becomes nine "
                                  "minutes at a value of time of £12 an hour, and three "
                                  "minutes of walking counts as six.")

    p.heading("Who has the choice, and what they choose")
    p.para("Not everyone can choose. Households with no car are on the bus whatever the "
           "costs say. Everyone else weighs the two costs, and the cheaper option takes the "
           "larger share — not all of it, because people differ in ways the costs do "
           "not capture.")

    T_all, T_own, T_zero = M["T_all"], M["T_own"], M["T_zero"]
    T_car, T_bus = M["T_car_person"], M["T_bus"]

    def sankey(ax):
        ax.set_xlim(-0.2, 9.4)
        ax.set_ylim(0, 3.4)
        ax.axis("off")
        boxes = {"All journeys": (0.0, 1.25, T_all.sum()),
                 "Car available": (3.3, 2.15, T_own.sum()),
                 "No car": (3.3, 0.35, T_zero.sum()),
                 "By car": (6.6, 2.15, T_car.sum()),
                 "By bus": (6.6, 0.35, T_bus.sum())}
        edges = [("All journeys", "Car available", T_own.sum()),
                 ("All journeys", "No car", T_zero.sum()),
                 ("Car available", "By car", T_car.sum()),
                 ("Car available", "By bus", T_own.sum() - T_car.sum()),
                 ("No car", "By bus", T_zero.sum())]
        for a, b, v in edges:
            xa, ya, _ = boxes[a]
            xb, yb, _ = boxes[b]
            ax.plot([xa + 2.3, xb], [ya + 0.42, yb + 0.42], color=BLUE, alpha=0.4,
                    lw=1 + 14 * v / T_all.sum(), solid_capstyle="butt")
            ax.text((xa + 2.3 + xb) / 2, (ya + yb) / 2 + 0.52, f"{v:,.0f}", ha="center",
                    fontsize=8.5, family=SANS, color=SOFT)
        for name, (x, y, tot) in boxes.items():
            ax.add_patch(FancyBboxPatch((x, y), 2.3, 0.84, boxstyle="round,pad=0.04",
                                        facecolor=TINT, edgecolor=BLUE, linewidth=1.0))
            ax.text(x + 1.15, y + 0.52, name, ha="center", va="center", fontsize=9,
                    family=SANS, color=INK)
            ax.text(x + 1.15, y + 0.24, f"{tot:,.0f} an hour", ha="center", va="center",
                    fontsize=8, family=SANS, color=SOFT)

    p.figure(sankey, 2.12,
             caption=f"Of {T_own.sum():,.0f} journeys with a car available, seven in ten go "
                     f"by car. The bus carries {T_bus.sum():,.0f}: the "
                     f"{T_own.sum() - T_car.sum():,.0f} who chose it and the "
                     f"{T_zero.sum():,.0f} who had no choice.")
    p.callout("Most variable demand models use some form of hierarchical logit formulation. "
              "— TAG M2.1 §4.2. The single car-or-bus split here is a simplified "
              "version. Lambda should be calibrated from data (M2.1 §4.5.10), so 0.1 "
              "per minute is a placeholder.", label="TAG")


def page_assignment(book):
    p = Page(book, "Level 5 — assignment")
    p.title("Cars on the roads, and congestion", eyebrow="Parts J and K")
    p.figure(lambda ax: stage_diagram(ax, active=(4,), feedback=True), 1.75, pad=0.16)
    p.para(f"Roads carry vehicles, not people, so the {M['T_car_person'].sum():,.0f} car "
           f"journeys become {M['V_car'].sum():,.0f} vehicles once they are divided by the "
           f"people per car. Then each one takes its quickest route — but a busy road "
           f"is a slow road, and a slow road is no longer the quickest, so the routes and "
           f"the times have to be solved together.")

    flows, cap, t0 = M["flows"], M["cap"], M["t0"]
    t_final = M["t_final"]

    def flowmap(ax):
        draw_zone_boxes(ax)
        top = flows.max()
        for k, row in links.iterrows():
            (x1, y1), (x2, y2) = POS[row["from"]], POS[row["to"]]
            ax.plot([x1, x2], [y1, y2], color=BLUE, alpha=0.75,
                    lw=1.0 + 7.0 * flows[k] / top, solid_capstyle="round", zorder=2)
        draw_links(ax, widths=[0.0] * 5, colour="none",
                   labels=[f"{flows[k]:.0f}" for k in links.index], label_size=9)
        draw_nodes(ax, size=400, fs=11.5)
        frame_off(ax, (-0.7, 8.7), (-0.4, 6.4))

    def bpr(ax):
        vc = np.linspace(0, 1.4, 300)
        ax.plot(vc, 1 + M["alpha"] * vc ** M["bpr_power"], color=ACCENT, lw=1.8)
        ax.scatter(flows / cap, t_final / t0, s=26, color=BLUE, zorder=3)
        for k, row in links.iterrows():
            ax.annotate(f"{row['from']}–{row['to']}", (flows[k] / cap[k],
                        (t_final / t0)[k]), textcoords="offset points", xytext=(5, 3),
                        fontsize=7.5, family=SANS, color=SOFT)
        ax.set_xlim(0, 1.4)
        tidy(ax, "how full the road is", "times slower than empty")

    half = (TW - 0.4) / 2
    y0 = p.y
    p.figure(flowmap, 2.5, width=half, x=ML, pad=0.0)
    p.y = y0 + 0.2
    p.figure(bpr, 2.2, width=half, x=ML + half + 0.4, pad=0.12, below=0.46)
    p.y = max(p.y, y0 + 2.95)
    p.para("**Left:** vehicles per hour on each road; a thicker line carries more.",
           size=10, gap=0.02)
    p.para("**Right:** the congestion curve. A road at half capacity is barely slower than "
           "an empty one; past about three-quarters it climbs steeply.", size=10)

    p.heading("One honest limitation")
    p.para("On these particular numbers nothing reroutes. Every pair of zones has one clear "
           "quickest route, so raising the times does not change anybody's mind and the "
           "loop settles on the first pass. Congestion is in the model and does slow the "
           "roads; it simply has no traffic to move around. Tighter capacities, or a "
           "network with genuine alternatives, would show the effect this step exists for.")
    p.callout("The speed/flow relationships recommended for use in highway assignment models "
              "are specified in Appendix E. — TAG M3.1 §2.9. The curve used here "
              "is the US Bureau of Public Roads form, which is not the one TAG "
              "specifies. Either switch to Appendix E or justify this one.", label="TAG",
              colour=BAD)


def page_validation(book):
    p = Page(book, "Level 6 — validation")
    p.title("Comparing the model with the real world", eyebrow="Parts L to N")
    p.para("A model can be wrong and still look convincing, so it is compared against counts "
           "it was never tuned to. Three checks: each road on its own, the total across a "
           "line drawn through the town, and journey times along a few routes.")

    check = M["check_links"]
    flows, counts = M["flows"], M["counts"]
    share = M["share_passing"]
    journey = M["journey"]

    def geh(ax):
        Mm = check["modelled"].to_numpy(float)
        Cc = check["counted"].to_numpy(float)
        cl = np.linspace(20, 300, 300)
        root = np.sqrt(625 + 400 * cl)
        ax.plot(cl, cl + (25 + root) / 4, color=FAINT, lw=0.9)
        ax.plot(cl, cl + (25 - root) / 4, color=FAINT, lw=0.9, label="GEH = 5")
        ax.plot([20, 300], [20, 300], color=RULE, lw=0.7, ls=":")
        ok = check["geh_below_5"].to_numpy()
        ax.scatter(Cc, Mm, s=34, c=[GOOD if o else BAD for o in ok], zorder=3)
        nudge = {"B–C": (6, -11), "C–D": (6, 5), "D–A": (-6, -12),
                 "A–C": (8, -2), "A–B": (6, 4)}
        for k in range(len(links)):
            name = f"{links.loc[k, 'from']}–{links.loc[k, 'to']}"
            ax.annotate(name, (Cc[k], Mm[k]), textcoords="offset points",
                        xytext=nudge.get(name, (6, 4)), fontsize=7.5,
                        family=SANS, color=SOFT)
        ax.set_xlim(0, 300)
        ax.set_ylim(0, 300)
        ax.set_aspect("equal")
        tidy(ax, "counted (veh/h)", "modelled (veh/h)")
        ax.legend(fontsize=8, frameon=False, loc="upper left",
                  prop={"family": SANS, "size": 8})

    def screen(ax):
        cs, ms = M["counted_screenline"], M["modelled_screenline"]
        ax.bar(["counted", "modelled"], [cs, ms], width=0.5, color=[FAINT, BLUE])
        ax.axhspan(cs * 0.95, cs * 1.05, color=GOOD, alpha=0.14, label="within 5%")
        for k, v in enumerate([cs, ms]):
            ax.text(k, v + 8, f"{v:,.0f}", ha="center", fontsize=9, family=SANS, color=INK)
        ax.set_ylim(0, cs * 1.32)
        tidy(ax, None, "veh/h across the line")
        ax.legend(fontsize=8, frameon=False, prop={"family": SANS, "size": 8})

    third = (TW - 0.45) / 2
    y0 = p.y
    p.figure(geh, 2.3, width=third, x=ML, pad=0.0, below=0.46)
    p.y = y0 + 0.15
    p.figure(screen, 2.0, width=third - 0.45, x=ML + third + 0.9, pad=0.12, below=0.42)
    p.y = max(p.y, y0 + 2.85)
    p.para("**Left:** each road against its count. A 20-vehicle error matters more on a "
           "quiet road than a busy one, so GEH divides by the size of the flow; anything "
           "between the grey curves passes.", size=10, gap=0.02)
    p.para("**Right:** the total crossing the screenline, which tests the overall pattern "
           "rather than any single road.", size=10)

    p.heading("What the checks say")
    p.table(
        [{"cells": ["Road flows, GEH below 5", f"{share:.0%} of roads", "at least 85%",
                    "fails"], "colours": [INK, BAD, SOFT, BAD]},
         {"cells": ["Screenline total", f"{M['screen_error']:+.1%}", "within 5%", "passes"],
          "colours": [INK, GOOD, SOFT, GOOD]},
         {"cells": ["Journey times", f"{journey['within rule'].mean():.0%} of routes",
                    "at least 85%", "passes"], "colours": [INK, GOOD, SOFT, GOOD]}],
        widths=[0.40, 0.22, 0.22, 0.16],
        header=["Check", "Result", "Rule", ""], size=10, lead=0.245)

    p.y += 0.08

    def times(ax):
        obs = journey["observed"].to_numpy(float)
        mod = journey["modelled"].to_numpy(float)
        xs = np.linspace(15, 32, 50)
        allowed = np.maximum(0.15 * xs, 1.0)
        ax.fill_between(xs, xs - allowed, xs + allowed, color=GOOD, alpha=0.13,
                        label="within 15% or 1 min")
        ax.plot([15, 32], [15, 32], color=RULE, lw=0.8, ls=":")
        ok = journey["within rule"].to_numpy(bool)
        ax.scatter(obs, mod, s=34, c=[GOOD if o else BAD for o in ok], zorder=3)
        ax.set_xlim(15, 32)
        ax.set_ylim(15, 32)
        ax.set_aspect("equal")
        tidy(ax, "observed (minutes)", "modelled (minutes)")
        ax.legend(fontsize=8, frameon=False, loc="upper left",
                  prop={"family": SANS, "size": 8})

    p.figure(times, 1.5, width=TW * 0.50, x=ML + TW * 0.25, below=0.44,
             caption="A to C, C to A and B to D, against the margin TAG allows: 15% of "
                     "the observed time, or one minute, whichever is more generous.")
    p.para(f"The screenline is almost exact, at {M['modelled_screenline']:,.0f} against "
           f"{M['counted_screenline']:,.0f} counted, yet one road inside it is badly wrong. "
           f"Both are true at once, which is why a model is checked road by road as well as "
           f"in total.")
    p.callout("The failure is deliberate and is left in: the counts are invented and the "
              "model was never tuned to hit them. A model that passes every check first time "
              "usually means the checks were not searching. A failing road is a map "
              "reference — it says which part of the model to argue with.",
              label="Note", colour=BAD)


def page_parameters(book):
    p = Page(book, "What is made up, and what the words mean")
    p.title("Every invented number, in one place", eyebrow="Reference")
    p.para("Nothing in this guide is evidence about anywhere. The values below are "
           "placeholders chosen to make the arithmetic work, and each one has to be replaced "
           "with a sourced figure, logged in docs/methodology.md, before the model says "
           "anything about a real town.")
    p.table(
        [["Weight curve, work", f"{M['beta_w']} per minute", "calibrate against trip lengths"],
         ["Weight curve, other", f"{M['beta_o']} per minute", "calibrate against trip lengths"],
         ["Value of time", "£12 per hour", "TAG data book, Table A1.3.2"],
         ["Car money cost", f"£{M['car_money']:.2f} per journey", "parking and fuel data"],
         ["Bus fare", f"£{M['bus_fare']:.2f}", "operator fares"],
         ["Walk weight", f"{M['walk_weight']}", "TAG M3.2 Table 1 (1.5 to 2.0)"],
         ["Wait weight", f"{M['wait_weight']}", "TAG M3.2 Table 1"],
         ["Bus in-vehicle factor", f"{M['bus_ivt_factor']}", "TAG M3.2 Table 1 (0.7 to 1.1)"],
         ["Choice sensitivity", f"{M['lam']} per minute", "TAG M2.1, to be calibrated"],
         ["Bus constant", f"{M['bus_penalty']:.2f} minutes", "fitted to a made-up car share"],
         ["People per car", f"{M['occupancy']}", "TAG data book, Table A1.3.3"],
         ["Congestion curve", f"α = {M['alpha']}, n = {M['bpr_power']}",
          "TAG M3.1 Appendix E instead"],
         ["Counts and journey times", "made up", "DfT counts and journey-time data"]],
        widths=[0.30, 0.26, 0.44],
        header=["Parameter", "Value used", "Where the real one comes from"], size=9.5,
        lead=0.228)

    p.y += 0.16
    p.heading("The words, in the order they appeared")
    terms = [
        ("zone", "a patch of town treated as a single place"),
        ("centroid", "the one point where a zone's journeys start and end"),
        ("link", "a road between two centroids"),
        ("free-flow time", "how long a road takes when it is empty"),
        ("intra-zonal", "a journey that never leaves its own zone"),
        ("productions", "journeys starting in a zone"),
        ("attractions", "journeys ending in a zone"),
        ("deterrence", "how much travel time puts people off a journey"),
        ("gravity model", "size times size, divided down by distance"),
        ("Furness", "fixing rows and columns by turns until both add up"),
        ("doubly constrained", "both ends fixed, as with commuting"),
        ("singly constrained", "the start fixed, the destination chosen"),
        ("generalised cost", "time, money, walking and waiting, all in minutes"),
        ("logit", "the share choosing each option, given the costs"),
        ("occupancy", "people per car"),
        ("assignment", "putting the vehicles onto the roads"),
        ("GEH", "whether a modelled flow is close enough to a counted one"),
        ("screenline", "a line across the town; flows crossing it are totalled"),
    ]
    p.table([[t, d] for t, d in terms], widths=[0.26, 0.74], size=9.5, lead=0.215)

    p.y = PAGE_H - MB - 0.70
    p.rule()
    p.y += 0.26
    p.para("Generated from notebooks/toy_model.ipynb by src/make_visual_guide.py. Rerun it "
           "after changing the model and every figure here follows.", size=9, colour=FAINT)


def main():
    book = Book()
    page_cover(book)
    page_overview(book)
    page_level0_a(book)
    page_level0_b(book)
    page_part_a(book)
    page_part_bc(book)
    page_part_de(book)
    page_matrix(book)
    page_cost_choice(book)
    page_assignment(book)
    page_validation(book)
    page_parameters(book)
    out = book.save(OUT)
    print(f"wrote {out.relative_to(REPO)}  ({len(book.pages)} pages, "
          f"{out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
