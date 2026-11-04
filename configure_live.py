"""Resolve pinned base models locally and configure the final browser demo."""
import argparse
import json
from pathlib import Path

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cached', action='store_true', help='Use local snapshots only.')
    args = parser.parse_args()
    protocol = json.loads((ROOT/'experiments/final100/protocol.json').read_text())
    config = {k:protocol[k] for k in ('max_tokens','evidence_checks','coverage_retries')}
    for role in ('primary','fallback'):
        spec = protocol['models'][role]
        path = snapshot_download(repo_id=spec['repo'],revision=spec['revision'],local_files_only=args.cached,
                                 allow_patterns=['*.json','*.safetensors','*.txt','*.model','LICENSE'])
        config[role]={'model':path,'adapter':str(ROOT/spec['adapter']),'label':spec['label']}
    output = ROOT/'outputs/runtime/extractor_config.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(config,indent=2)+'\n')
    print('Final model configured. Start the demo with python demo/app.py.')

if __name__=='__main__':
    main()
