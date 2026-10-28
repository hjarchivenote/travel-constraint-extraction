"""Download pinned, public model snapshots into the Hugging Face cache."""

import argparse
import json
from pathlib import Path

from huggingface_hub import snapshot_download

MODELS = {
    "small": {"repo": "Qwen/Qwen2.5-0.5B-Instruct",
              "revision": "7ae557604adf67be50417f59c2c2f167def9a775", "quantization": None},
    "large": {"repo": "mlx-community/Qwen2.5-7B-Instruct-4bit",
              "revision": "c26a38f6a37d0a51b4e9a1eb3026530fa35d9fed", "quantization": "4-bit",
              "source_model": "Qwen/Qwen2.5-7B-Instruct"},
}


def resolve_model_path(value):
    if value not in MODELS:
        return value
    manifest_path = Path("outputs/runtime") / f"{value}_model.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Download the {value} snapshot with travel_constraints.download_models first.")
    manifest = json.loads(manifest_path.read_text())
    if manifest["revision"] != MODELS[value]["revision"] or not Path(manifest["path"]).is_dir():
        raise ValueError("Model manifest does not identify the expected pinned local snapshot.")
    return manifest["path"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=["small", "large", "all"])
    args = parser.parse_args()
    output = Path("outputs/runtime")
    output.mkdir(parents=True, exist_ok=True)
    for name in MODELS if args.model == "all" else [args.model]:
        spec = MODELS[name]
        path = snapshot_download(repo_id=spec["repo"], revision=spec["revision"],
                                 allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "LICENSE", "README.md"])
        manifest = spec | {"path": path}
        (output / f"{name}_model.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps(manifest))


if __name__ == "__main__":
    main()
