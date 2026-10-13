#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = ROOT / "latex_exports"

FIGURE_FILES = [
    ("fig1_model_diagram.pdf", "Fig. 1"),
    ("fig2_main_performance.pdf", "Fig. 2"),
    ("fig3_mechanism_decomposition.pdf", "Fig. 3"),
    ("fig4_robustness_null_stress.pdf", "Fig. 4"),
    ("fig5_external_sensitivity_noise.pdf", "Fig. 5"),
]


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def latex_code(text: str) -> str:
    if "/" in text:
        safe = text.replace("{", r"\{").replace("}", r"\}")
        return r"\path{" + safe + "}"
    return r"\texttt{" + latex_escape(text) + "}"


def latex_math(expr: str) -> str:
    expr = expr.strip()
    replacements = {
        "sum_{e in E_t: i in e}": r"\sum_{e \in E_t: i \in e}",
        "sum_e": r"\sum_e",
        "Pr(": r"\Pr(",
        "exp(": r"\exp(",
        "beta": r"\beta",
        "rho0": r"\rho_0",
        "mu": r"\mu",
        "max(": r"\max(",
    }
    for old, new in replacements.items():
        expr = expr.replace(old, new)
    return expr


def stash_token(tokens: dict[str, str], value: str) -> str:
    token = f"ZZZLATEXTOKEN{len(tokens)}ZZZ"
    tokens[token] = value
    return token


def convert_inline(text: str) -> str:
    tokens: dict[str, str] = {}

    def citation(match: re.Match[str]) -> str:
        raw = match.group(1)
        keys = [part.strip().lstrip("@") for part in raw.split(";")]
        keys = [key for key in keys if key]
        return stash_token(tokens, r"\citep{" + ",".join(keys) + "}")

    text = re.sub(r"\[(@[A-Za-z0-9_:-]+(?:;\s*@[A-Za-z0-9_:-]+)*)\]", citation, text)

    def inline_math(match: re.Match[str]) -> str:
        return stash_token(tokens, r"\(" + match.group(1) + r"\)")

    text = re.sub(r"\\\((.+?)\\\)", inline_math, text)

    def inline_code(match: re.Match[str]) -> str:
        return stash_token(tokens, latex_code(match.group(1)))

    text = re.sub(r"`([^`]+)`", inline_code, text)
    escaped = latex_escape(text)
    for token, value in tokens.items():
        escaped = escaped.replace(token, value)
    return escaped


def markdown_to_latex(markdown: str) -> tuple[str, str, str]:
    lines = markdown.splitlines()
    title = ""
    author_lines: list[str] = []
    body: list[str] = []
    in_abstract = False
    skip_section: str | None = None
    in_display_math = False
    in_front_matter = True

    for raw_line in lines:
        line = raw_line.strip()
        if line == r"\[":
            body.append(r"\[")
            in_display_math = True
            continue
        if line == r"\]":
            body.append(r"\]")
            body.append("")
            in_display_math = False
            continue
        if in_display_math:
            body.append(raw_line)
            continue
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        if in_front_matter and not line.startswith("## "):
            if line:
                author_lines.append(line)
            continue
        if line.startswith("## "):
            in_front_matter = False
            if in_abstract:
                body.append(r"\end{abstract}")
                body.append("")
                in_abstract = False
            section = line[3:].strip()
            if section in {"Figure Legends", "References"}:
                skip_section = section
                continue
            skip_section = None
            if section == "Abstract":
                body.append(r"\begin{abstract}")
                in_abstract = True
            else:
                body.append(r"\section*{" + latex_escape(section) + "}")
            body.append("")
            continue
        if skip_section:
            continue
        if line.startswith("### "):
            body.append(r"\subsection*{" + latex_escape(line[4:].strip()) + "}")
            body.append("")
            continue
        if not line:
            body.append("")
            continue
        if line.startswith("`") and line.endswith("`") and "=" in line:
            body.append(r"\[")
            body.append(latex_math(line.strip("`")))
            body.append(r"\]")
            body.append("")
            continue
        body.append(convert_inline(line))
        body.append("")

    if in_abstract:
        body.append(r"\end{abstract}")
        body.append("")
    author = r" \\ ".join(convert_inline(line) for line in author_lines)
    if not author:
        author = "Author information to be added"
    return title, author, "\n".join(body).strip() + "\n"


def parse_figure_legends(markdown: str) -> list[tuple[str, str, str]]:
    legends: list[tuple[str, str, str]] = []
    pattern = re.compile(r"^\*\*(Fig\.\s*(\d+)\s*\|\s*.*?)\*\*\s*(.*)$")
    figure_map = {
        "1": "fig1_model_diagram.pdf",
        "2": "fig2_main_performance.pdf",
        "3": "fig3_mechanism_decomposition.pdf",
        "4": "fig4_robustness_null_stress.pdf",
        "5": "fig5_external_sensitivity_noise.pdf",
    }
    for line in markdown.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        heading = match.group(1)
        number = match.group(2)
        caption = match.group(3)
        figure_file = figure_map.get(number)
        if figure_file:
            caption_heading = re.sub(r"^Fig\.\s*\d+\s*\|\s*", "", heading).strip()
            legends.append((number, figure_file, f"{caption_heading} {caption}"))
    return legends


def figure_latex(legends: list[tuple[str, str, str]]) -> str:
    blocks: list[str] = [r"\section*{Figure Legends}", ""]
    for number, figure_file, caption in legends:
        short_caption = re.sub(r"`([^`]+)`", r"\1", caption)
        short_caption = re.sub(r"\s+", " ", short_caption).strip()
        blocks.extend(
            [
                r"\begin{figure}[p]",
                r"\centering",
                rf"\includegraphics[width=\textwidth,height=0.78\textheight,keepaspectratio]{{figures/{figure_file}}}",
                r"\caption[" + latex_escape(short_caption) + "]{" + convert_inline(caption) + "}",
                rf"\label{{fig:{number}}}",
                r"\end{figure}",
                r"\clearpage",
                "",
            ]
        )
    return "\n".join(blocks)


def supplementary_assets_note() -> str:
    return r"""
\section*{Supplementary Tables and Source Data}

The LaTeX archive includes the supplementary navigation tables as CSV and Markdown files: Table S1 (formal experiment design), Table S2 (dataset and temporal-hypergraph statistics), Table S3 (baseline and ablation definitions) and Table S4 (completed supplementary robustness and mechanism audits). The archive also includes source-data CSVs, figure manifests, the random-seed manifest, environment files and release/deposition notes.

"""


def build_main_tex(title: str, author: str, manuscript_body: str, figures: str) -> str:
    return rf"""\documentclass[11pt]{{article}}
\usepackage[T1]{{fontenc}}
\usepackage[utf8]{{inputenc}}
\usepackage[a4paper,margin=1in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{longtable}}
\usepackage{{array}}
\usepackage{{caption}}
\usepackage{{float}}
\usepackage[numbers,sort&compress]{{natbib}}
\usepackage{{xurl}}
\usepackage{{hyperref}}
\hypersetup{{colorlinks=true,linkcolor=black,citecolor=blue,urlcolor=blue}}
\Urlmuskip=0mu plus 1mu
\emergencystretch=3em
\sloppy
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0.55em}}
\captionsetup{{font=small,labelfont=bf}}

\title{{{latex_escape(title)}}}
\author{{{author}}}
\date{{Latest preview build: {datetime.now().strftime("%Y-%m-%d %H:%M")}}}

\begin{{document}}
\maketitle

{manuscript_body}

{figures}

{supplementary_assets_note()}

\bibliographystyle{{unsrtnat}}
\bibliography{{references}}

\end{{document}}
"""


def copytree(src: Path, dest: Path) -> None:
    if src.exists():
        shutil.copytree(src, dest)


def copy_formal_experiment_drivers(out_dir: Path) -> None:
    repo_root = ROOT.parent
    driver_dir = out_dir / "formal_experiment_drivers"
    driver_dir.mkdir(exist_ok=True)
    for pattern in [
        "scrs_nc_experiment_common.py",
        "prepare_scrs_external_real_data_s26.py",
        "run_scrs_formal_nc_validation.py",
        "run_scrs_nc_*.py",
    ]:
        for src in sorted(repo_root.glob(pattern)):
            shutil.copy2(src, driver_dir / src.name)


def copy_submission_experiment_specs(out_dir: Path) -> None:
    specs_out = out_dir / "experiment_specs"
    specs_out.mkdir(exist_ok=True)
    for filename in [
        "completed_supplemental_audits_s28_s30.csv",
        "completed_supplemental_audits_s28_s30.json",
    ]:
        src = ROOT / "experiment_specs" / filename
        if src.exists():
            shutil.copy2(src, specs_out / filename)


def refresh_source_data_packages() -> None:
    script = ROOT / "scripts" / "package_source_data.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)], check=True)


def write_manifest(out_dir: Path, stamp: str) -> None:
    manifest = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "stamp": stamp,
        "source_manuscript": "manuscript.md",
        "latex_entrypoint": "main.tex",
        "preview_pdf_expected": "main.pdf",
        "figures": [name for name, _label in FIGURE_FILES],
        "notes": [
            "Compile with latexmk -pdf -interaction=nonstopmode main.tex.",
            "DOI and GitHub placeholders remain in Data Availability and Code Availability until public deposits are minted.",
            "formal_experiment_drivers/ contains the formal runner scripts and shared simulation library included for reviewer-facing reproducibility.",
        ],
    }
    (out_dir / "build_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def create_package(stamp: str | None) -> Path:
    if stamp is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = EXPORT_ROOT / f"SCRS_NC_latex_latest_{stamp}"
    if out_dir.exists():
        raise FileExistsError(f"Export directory already exists: {out_dir}")
    out_dir.mkdir(parents=True)

    manuscript_md = (ROOT / "manuscript.md").read_text(encoding="utf-8")
    legends_md = (ROOT / "figure_legends.md").read_text(encoding="utf-8")
    title, author, manuscript_body = markdown_to_latex(manuscript_md)
    legends = parse_figure_legends(legends_md)
    main_tex = build_main_tex(title, author, manuscript_body, figure_latex(legends))
    (out_dir / "main.tex").write_text(main_tex, encoding="utf-8")
    shutil.copy2(ROOT / "references_verified.bib", out_dir / "references.bib")

    shutil.copytree(ROOT / "figures", out_dir / "figures")

    for filename in [
        "manuscript.md",
        "figure_legends.md",
        "README.md",
        "qc_report.md",
        "reference_verification.csv",
        "reference_verification.md",
        "requirements.txt",
        "environment.yml",
    ]:
        src = ROOT / filename
        if src.exists():
            shutil.copy2(src, out_dir / filename)

    copytree(ROOT / "tables", out_dir / "tables")
    copy_submission_experiment_specs(out_dir)
    refresh_source_data_packages()
    copytree(ROOT / "source_data", out_dir / "source_data")
    copytree(ROOT / "scripts", out_dir / "scripts")
    release_out = out_dir / "release"
    release_out.mkdir(exist_ok=True)
    for filename in ["deposition_manifest.csv", "deposition_checklist.md"]:
        src = ROOT / "release" / filename
        if src.exists():
            shutil.copy2(src, release_out / filename)
    copy_formal_experiment_drivers(out_dir)
    write_manifest(out_dir, stamp)
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stamp", default=None, help="Optional export stamp, for example 20260915_153000.")
    args = parser.parse_args()
    out_dir = create_package(args.stamp)
    print(out_dir)


if __name__ == "__main__":
    main()
