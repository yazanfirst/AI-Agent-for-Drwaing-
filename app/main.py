from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.schemas import ProjectInput
from app.tools.exporter import export_all
from app.tools.layout_adapter import adapt_layout
from app.tools.lod_renderer import render_lod
from app.tools.pattern_miner import mine_patterns
from app.tools.reference_extractor import extract_all_reference_cases
from app.tools.site_reader import read_site_dxf
from app.tools.template_matcher import match_pattern
from app.tools.validator import validate_layout


def run_pipeline(project: ProjectInput) -> dict:
    repo_root = Path(__file__).resolve().parents[1]

    site = read_site_dxf(project.site_dxf_path)
    site["site_type"] = project.site_type

    cases_dir = repo_root / "data/extracted_cases"
    pattern_file = repo_root / "data/patterns/patterns.json"

    if project.force_refresh or not any(cases_dir.glob("*.json")):
        extract_all_reference_cases(repo_root)

    if project.force_refresh or not pattern_file.exists():
        mine_patterns(repo_root)

    matched = match_pattern(site, repo_root)
    plan = adapt_layout(matched, project.project_id, project.requested_lod, repo_root)
    rendered = render_lod(plan, project.requested_lod)
    report = validate_layout(rendered)
    exports = export_all(rendered, repo_root / project.output_dir)

    patterns = json.loads(pattern_file.read_text()) if pattern_file.exists() else {}
    unresolved = [e.canonical_name for e in rendered.equipment if e.cad_block_name == "UNRESOLVED"]

    summary = {
        "exports": exports,
        "validation": report.model_dump(),
        "final_output_summary": {
            "extracted_block_names": sorted({e.canonical_name for e in rendered.equipment}),
            "number_of_reference_cases": len(list(cases_dir.glob('*.json'))),
            "learned_patterns": {
                "common_block_clusters": len(patterns.get("common_block_clusters", [])),
                "adjacency_patterns": len(patterns.get("adjacency_patterns", [])),
            },
            "unresolved_cad_blocks": unresolved,
            "supported_lod_capabilities": {
                "100": "zoning only",
                "200": "zones + key equipment",
                "300": "full layout with equipment, seating, doors",
            },
        },
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Restaurant fitout AI pipeline")
    parser.add_argument("site_dxf_path")
    parser.add_argument("--project-id", default="project-001")
    parser.add_argument("--lod", type=int, choices=[100, 200, 300], default=300)
    parser.add_argument("--site-type", default=None)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    project = ProjectInput(
        project_id=args.project_id,
        site_dxf_path=args.site_dxf_path,
        requested_lod=args.lod,
        site_type=args.site_type,
        output_dir=args.output_dir,
        force_refresh=args.force_refresh,
    )
    print(json.dumps(run_pipeline(project), indent=2))


if __name__ == "__main__":
    main()
