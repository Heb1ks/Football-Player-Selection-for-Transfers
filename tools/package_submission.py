"""Bundle the runnable source and exact raw research snapshot, without environments."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
paths=[]
for directory in ['app','data','models','research','docs','diagrams','tests','tools','.github']:
    paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith(('.pyc','.download')))
for name in ['README.md','.gitignore','requirements.txt','requirements-docs.txt','requirements-lock.txt','start.ps1']:
    p=ROOT/name
    if p.exists():paths.append(p)
paths.extend((ROOT/'output/pdf').glob('*.pdf'))
for name in ['test-results.txt','latency.json','pull-request.json','ci-status.json']:
    p=ROOT/'output'/name
    if p.exists():paths.append(p)
paths=sorted(set(paths))
records=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
manifest=ROOT/'output/submission-manifest.json'
manifest.write_text(json.dumps({'created':'2026-10-15','status':'Initial prototype package for review, not a completed academic submission','files':records},indent=2),encoding='utf-8')
dest=ROOT/'output/TransferLens_PreDefense_Package.zip'
with ZipFile(dest,'w',compression=ZIP_DEFLATED,compresslevel=5) as z:
    for p in paths:z.write(p,p.relative_to(ROOT).as_posix())
    z.write(manifest,'output/submission-manifest.json')
with ZipFile(dest) as z:
    assert z.testzip() is None
    assert 'research/rmt/data/appearances.csv.gz' in z.namelist()
    assert 'models/individual_rf.joblib' in z.namelist()
    assert not any('/.venv/' in x or '/.git/' in x for x in z.namelist())
print(json.dumps({'file':str(dest),'files':len(paths)+1,'megabytes':round(dest.stat().st_size/1e6,2),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},indent=2))
