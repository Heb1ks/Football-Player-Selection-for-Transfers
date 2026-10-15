"""Restore the exact research inputs, verifying every retained SHA-256 hash."""
from pathlib import Path
import json, hashlib, urllib.request
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'research/rmt/outputs/source_manifest.json').read_text())
data=ROOT/'research/rmt/data';data.mkdir(parents=True,exist_ok=True)
for name,record in manifest['files'].items():
    dest=data/f'{name}.csv.gz'
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()==record['sha256']:
        print(name+': verified existing snapshot');continue
    temp=dest.with_suffix('.download')
    urllib.request.urlretrieve(record['url'],temp)
    if hashlib.sha256(temp.read_bytes()).hexdigest()!=record['sha256']:
        temp.unlink()
        raise SystemExit(name+': upstream snapshot changed; obtain the retained archive, do not silently change the benchmark.')
    temp.replace(dest);print(name+': restored and verified')
