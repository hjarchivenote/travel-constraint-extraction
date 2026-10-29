"""Package completed deliverables and verify contents without shipping caches."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    result=json.loads((ROOT/'experiments/results/comparison.json').read_text())
    assert result['records_per_model']==80 and len(result['metrics'])==3
    required=['docs/travel_constraint_report.pdf','docs/travel_constraint_presentation.pptx',
              'docs/travel_constraint_presentation.pdf','docs/presentation_script.md',
              'docs/understanding_ko.md','artifacts/qwen05_lora/adapters.safetensors']
    assert all((ROOT/p).is_file() for p in required)
    from pypdf import PdfReader
    assert len(PdfReader(ROOT/required[0]).pages)>=5
    assert len(PdfReader(ROOT/required[2]).pages)==6
    with zipfile.ZipFile(ROOT/required[1]) as z:
        slides=[n for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml') and '/_rels/' not in n]
        assert len(slides)==6
    files=[]
    for folder in ('src','tests','data','artifacts','experiments','demo','docs'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith(('.pyc','.pyo')) and p.name!='submission_manifest.json':
                files.append(p)
    for name in ('README.md','requirements.txt','.gitignore','LICENSE_SCOPE.md','THIRD_PARTY_NOTICES.md','SUBMISSION.md'):
        files.append(ROOT/name)
    files=sorted(set(files))
    manifest={'format':'sha256','dataset_sha256':result['dataset_sha256'],
              'annotation_review':'AI-reviewed synthetic; zero human-verified records',
              'files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    manifest_path=ROOT/'docs/submission_manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    files.append(manifest_path)
    archive=ROOT/'submission_Hyojin_Lee_Travel_Constraint_Extraction.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            name='Hyojin_Lee_Travel_Constraint_Extraction/'+p.relative_to(ROOT).as_posix()
            info=zipfile.ZipInfo(name,date_time=(2026,10,29,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest['files'].items():
            assert hashlib.sha256(z.read('Hyojin_Lee_Travel_Constraint_Extraction/'+name)).hexdigest()==digest
        assert not any('/.venv/' in n or '/.git/' in n or '/outputs/' in n or n.endswith('.env') for n in z.namelist())
    print(json.dumps({'archive':str(archive),'files':len(files),'bytes':archive.stat().st_size,
                      'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))


if __name__=='__main__':main()
