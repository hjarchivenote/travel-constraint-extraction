"""Check the final metrics against the frozen outputs, without model inference."""
import json
import hashlib
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from travel_constraints.metrics import summarize

def rows(p):
    return [json.loads(l) for l in p.read_text().splitlines()]

def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    targets = ROOT/'data/expanded/records.jsonl'
    assert hashlib.sha256(targets.read_bytes()).hexdigest()==protocol['dataset_sha256']
    assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h for n,h in protocol['file_sha256'].items())
    test = [r for r in rows(targets) if r['split']=='test']
    assert len(test)==100 and [r['id'] for r in test]==protocol['test_ids']
    frozen = json.loads((HERE/'results.json').read_text())['test100']
    for role in ('baseline','candidate'):
        predictions = rows(HERE/f'{role}_test100.jsonl')
        for stage in ('raw_primary','full_system'):
            values = [{'id':p['id'],'parsed_output':p[stage]['parsed_output'],'inference_seconds':p['inference_seconds']} for p in predictions]
            actual = summarize(test,values)
            assert actual == frozen[stage][role], (stage,role)
            print(f'{role:9s} {stage:12s} F1={actual["f1"]:.3f} exact={actual["exact_record_accuracy"]:.0%}')

if __name__=='__main__':
    main()
