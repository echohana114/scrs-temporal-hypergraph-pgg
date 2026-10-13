from __future__ import annotations

import csv
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source_data"
SUPPLEMENTARY = SOURCE / "supplementary"
PACKAGE_ROOT = SOURCE / "source_data_packages"


MAIN_FIGURE_FILES = {
    "Source_Data_Fig_1": [
        "fig1_model_diagram_flow.csv",
    ],
    "Source_Data_Fig_2": [
        "fig2a_s20_scrs_tail_by_case.csv",
        "fig2b_s20_gap_cells_for_forest.csv",
        "fig2b_s20_gap_forest_summary.csv",
        "fig2b_s20_mean_gaps_by_source.csv",
        "fig4a_s21_phase_r_rho0.csv",
        "cell_level_inference_summary.csv",
    ],
    "Source_Data_Fig_3": [
        "fig3_s25_mechanism_paired_gaps_by_cell.csv",
        "fig3_s25_mechanism_mean_gaps.csv",
        "cell_level_inference_summary.csv",
    ],
    "Source_Data_Fig_4": [
        "fig4a_s21_robustness_cell_summary.csv",
        "fig4a_s21_robustness_source_summary.csv",
        "fig4a_s21_phase_r_rho0.csv",
        "fig4b_s22_real_nulls_cell_summary.csv",
        "fig4b_s22_real_nulls_mechanism_summary.csv",
        "fig4b_s24_phase_r_mutation.csv",
        "fig4c_s22_real_nulls_gap_cells_long.csv",
        "fig4c_s23_synthetic_stress_cell_summary.csv",
        "fig4c_s23_synthetic_stress_case_summary.csv",
        "cell_level_inference_summary.csv",
    ],
    "Source_Data_Fig_5": [
        "fig5a_s26_external_empirical_cases.csv",
        "fig5a_s26_external_paired_gaps_by_cell.csv",
        "fig5a_s26_external_dataset_manifest.csv",
        "fig5b_s27_payoff_update_source_summary.csv",
        "fig5b_s27_payoff_update_paired_gaps_by_cell.csv",
        "fig5c_s24_noise_horizon_cell_summary.csv",
        "fig5c_s24_noise_horizon_trajectory_summary.csv",
        "cell_level_inference_summary.csv",
    ],
}


def copy_file(src: Path, dest_dir: Path) -> Path:
    if not src.exists():
        raise FileNotFoundError(src)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return dest


def zip_dir(src_dir: Path) -> Path:
    archive = src_dir.with_suffix(".zip")
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(src_dir.parent))
    return archive


def supplementary_files(label: str) -> list[Path]:
    lower = label.lower()
    upper_files = sorted(SUPPLEMENTARY.glob(f"{label}_*"))
    files = upper_files if upper_files else sorted(SUPPLEMENTARY.glob(f"{lower}_*"))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def write_manifest(rows: list[dict[str, str]]) -> Path:
    manifest = SOURCE / "source_data_package_manifest.csv"
    fieldnames = [
        "package",
        "kind",
        "archive",
        "file_count",
        "included_files",
    ]
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return manifest


def main() -> None:
    if PACKAGE_ROOT.exists():
        shutil.rmtree(PACKAGE_ROOT)
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for package, filenames in MAIN_FIGURE_FILES.items():
        package_dir = PACKAGE_ROOT / package
        copied = [copy_file(SOURCE / filename, package_dir) for filename in filenames]
        archive = zip_dir(package_dir)
        rows.append(
            {
                "package": package,
                "kind": "main figure source data",
                "archive": archive.relative_to(SOURCE).as_posix(),
                "file_count": str(len(copied)),
                "included_files": "; ".join(path.relative_to(SOURCE).as_posix() for path in copied),
            }
        )

    supplement_dir = PACKAGE_ROOT / "Source_Data_Supplementary_Figs_S20_S30"
    supplementary_copied: list[Path] = []
    for index in range(20, 31):
        label = f"S{index}"
        target = supplement_dir / label
        files = supplementary_files(label)
        if not files:
            raise FileNotFoundError(f"No supplementary source data found for {label}")
        supplementary_copied.extend(copy_file(path, target) for path in files)

    archive = zip_dir(supplement_dir)
    rows.append(
        {
            "package": "Source_Data_Supplementary_Figs_S20_S30",
            "kind": "supplementary figure source data",
            "archive": archive.relative_to(SOURCE).as_posix(),
            "file_count": str(len(supplementary_copied)),
            "included_files": "; ".join(path.relative_to(SOURCE).as_posix() for path in supplementary_copied),
        }
    )

    manifest = write_manifest(rows)
    print(manifest)


if __name__ == "__main__":
    main()
