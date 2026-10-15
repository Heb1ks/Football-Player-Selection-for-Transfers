"""Load the executed model and demonstrate prediction for a real cohort row."""
from pathlib import Path
import argparse,sys,json,html
ROOT=Path(__file__).resolve().parent
packages=ROOT.parent/'tmp/python_packages'
if packages.exists():sys.path.insert(0,str(packages))
import pandas as pd
import joblib

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--player-id',type=int,default=132098);args=parser.parse_args()
 cohort=pd.read_csv(ROOT/'outputs/transfer_cohort.csv')
 row=cohort[cohort.player_id.eq(args.player_id)]
 if len(row)!=1:parser.error('Player ID must identify exactly one real retained transfer')
 result=json.loads((ROOT/'outputs/results.json').read_text());features=result['config']['base_features']+result['config']['context_features']
 assert 'target_ga90' not in features and not any(x.startswith('post_') for x in features)
 model=joblib.load(ROOT/'outputs/formation_rf.joblib');prediction=float(model.predict(row[features])[0]);r=row.iloc[0]
 out={'player_id':int(r.player_id),'player_name':r.player_name,'transfer_date':r.transfer_date,'split':r.split,'prediction_ga90':prediction,'observed_ga90':float(r.target_ga90),'absolute_error':abs(prediction-r.target_ga90),'predictor_fields':features,'status':'retrospective demonstration on a real cohort row'}
 (ROOT/'outputs/demo_prediction.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
 page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Transfer prediction demonstration</title><style>body{{font:18px Georgia;max-width:780px;margin:60px auto;color:#172432;line-height:1.5}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:12px;text-align:left}}th{{background:#eee}}</style><h1>Transfer prediction demonstration</h1><p>{html.escape(r.player_name)} · {html.escape(r.transfer_date)} · {html.escape(r.split)} split</p><table><tr><th>Measure</th><th>GA90</th></tr><tr><td>Model prediction</td><td>{prediction:.6f}</td></tr><tr><td>Observed first destination season</td><td>{r.target_ga90:.6f}</td></tr><tr><td>Absolute error</td><td>{out['absolute_error']:.6f}</td></tr></table><p>This is a retrospective demonstration. The model receives 15 historical predictors; the observed outcome is displayed for comparison after prediction.</p><p>Nominal formation is the available context measure. Pressing and possession are absent.</p></html>'''
 (ROOT/'outputs/demo_prediction.html').write_text(page,encoding='utf-8')
 print(json.dumps(out,ensure_ascii=True,indent=2))
if __name__=='__main__':main()
