"""Copy the relevant RMT snapshot without changing the original project."""
from pathlib import Path
import shutil, hashlib, json
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'rmt' / 'practical'
manifest = []
for relative in ['run_pipeline.py', 'demonstrate_transfer.py', 'requirements.txt', 'README.md']:
    items = [SOURCE / relative]
    for src in items:
        dest = ROOT / 'research' / 'rmt' / src.relative_to(SOURCE)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        manifest.append({'source': 'rmt/practical/' + src.relative_to(SOURCE).as_posix(), 'destination': dest.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
for directory in ['data', 'outputs']:
    for src in (SOURCE / directory).iterdir():
        if not src.is_file(): continue
        dest = ROOT / 'research' / 'rmt' / src.relative_to(SOURCE)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        manifest.append({'source': 'rmt/practical/' + src.relative_to(SOURCE).as_posix(), 'destination': dest.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
(ROOT / 'research' / 'rmt' / 'reuse_manifest.json').write_text(json.dumps({'copied_on': '2026-10-15', 'origin': 'RMT Assignment 3', 'purpose': 'Reuse of team research as a diploma prototype foundation; no claim of new data collection or new RMT results.', 'files': manifest}, indent=2), encoding='utf-8')
print(f'Copied and hashed {len(manifest)} files')
