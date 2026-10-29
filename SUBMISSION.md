# Recent Areas of AI — Hyojin Lee

**Travel Constraint Extraction: small-model fine-tuning for changes to a London itinerary**

## Course deliverables

- [Seven-page report (PDF)](docs/travel_constraint_report.pdf)
- [Six-slide presentation (PPTX)](docs/travel_constraint_presentation.pptx)
- [Presentation (PDF)](docs/travel_constraint_presentation.pdf)

The English speaking script is in `docs/presentation_script.md` and the PPTX speaker notes. It is intended for a presentation of at most five minutes; rehearse with a timer.

## Implementation

Public code and artifacts: <https://github.com/hjarchivenote/travel-constraint-extraction>.

The archive includes the source, 400-record synthetic dataset and splits, trained LoRA adapter, pinned experiment protocol, all final raw predictions and metrics, and a runnable demonstration. The root README explains installation and reproduction. Downloaded base weights and the Python environment are excluded.

To view recorded model outputs without installation, run `python3 demo/app.py` from this directory and open <http://127.0.0.1:8765>. New-text inference requires the MLX environment and small-model download described in the README.

## Interpretation

The NLP task is constraint extraction. The downstream planner performs illustrative edits, without verifying routes, opening hours, or booking availability. Labels are AI-reviewed synthetic annotations with zero human-verified records. AI assistance and all third-party sources are disclosed in the report and repository notices.

`docs/submission_manifest.json` records SHA-256 hashes for the packaged project files, excluding the manifest itself.
