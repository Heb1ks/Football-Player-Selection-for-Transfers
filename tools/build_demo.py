"""Build reproducible inference assets from the copied, real RMT cohort."""
from pathlib import Path
import hashlib, json, sys, shutil
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/rmt'))
import pandas as pd
import joblib
from run_pipeline import model, BASE, CTX

def main():
    source = ROOT / 'research/rmt/outputs'
    cohort = pd.read_csv(source / 'transfer_cohort.csv')
    train = cohort[cohort.split.eq('train')]
    assert len(train) == 405 and not set(train.player_id) & set(cohort[cohort.split.eq('test')].player_id)
    out = ROOT / 'models'; out.mkdir(exist_ok=True)
    baseline = model(); baseline.fit(train[BASE], train.target_ga90)
    joblib.dump(baseline, out / 'individual_rf.joblib')
    shutil.copy2(source / 'formation_rf.joblib', out / 'formation_rf.joblib')
    # Names are display metadata only. No fee or later market value enters the model.
    transfers = pd.read_csv(ROOT / 'research/rmt/data/transfers.csv.gz', usecols=['from_club_id','to_club_id','from_club_name','to_club_name'])
    names = {}
    for side in ['from', 'to']:
        for key, name in transfers[[f'{side}_club_id',f'{side}_club_name']].dropna().drop_duplicates().itertuples(index=False, name=None):
            names.setdefault(int(key), name)
    cohort['origin_club'] = cohort.from_club_id.map(names).fillna(cohort.from_club_id.astype(str))
    cohort['destination_club'] = cohort.to_club_id.map(names).fillna(cohort.to_club_id.astype(str))
    assets = ROOT / 'data'; assets.mkdir(exist_ok=True)
    cohort.to_csv(assets / 'cohort.csv', index=False)
    shutil.copy2(source / 'results.json', assets / 'results.json')
    hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.joblib'))}
    metadata = {'created_on':'2026-10-15', 'origin':'RMT Assignment 3 snapshot 2026-10-12', 'training_rows':len(train), 'demo_rows':int(cohort.split.eq('test').sum()), 'models_sha256':hashes, 'base_features':BASE, 'context_features':CTX, 'inference':'Historical replay; scenario changes are associative predictions, not causal transfer effects.'}
    (out / 'manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))

if __name__ == '__main__': main()
