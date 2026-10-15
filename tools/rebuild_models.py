"""Rerun the unchanged RMT experiment, also retaining its individual model.

The cohort CSV rounds floating-point numbers on roundtrip. Training from raw
inputs preserves the original split thresholds of the Random Forest. Original
RMT files remain untouched; fresh evaluation outputs go to tmp/reproduction.
"""
from pathlib import Path
import json, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'research/rmt/run_pipeline.py'
text=source.read_text(encoding='utf-8')
text=text.replace("OUT = ROOT / 'outputs'; OUT.mkdir(exist_ok=True)","OUT = DIPLOMA_ROOT / 'tmp/reproduction'; OUT.mkdir(parents=True, exist_ok=True)")
text=text.replace("        if name=='formation_rf':", "        joblib.dump(m, DIPLOMA_ROOT/'models'/f'{name}.joblib')\n        if name=='formation_rf':")
scope={'__file__':str(source),'__name__':'rmt_reproduction','DIPLOMA_ROOT':ROOT}
exec(compile(text,str(source),'exec'),scope)
scope['run']()
actual=json.loads((ROOT/'tmp/reproduction/results.json').read_text())
expected=json.loads((ROOT/'research/rmt/outputs/results.json').read_text())
for model in ['individual_rf','formation_rf']:
    for metric in ['MAE','RMSE']:
        assert abs(actual['test'][model][metric]-expected['test'][model][metric])<1e-10,(model,metric)
manifest=json.loads((ROOT/'models/manifest.json').read_text())
manifest['models_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'models').glob('*.joblib'))}
manifest['training_source']='Original raw RMT inputs, full-precision in-memory features; exact benchmark reproduction verified.'
(ROOT/'models/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
shutil.copy2(ROOT/'tmp/reproduction/run_log.txt',ROOT/'data/reproduction_log.txt')
print('Original benchmark reproduced; both models saved.')
