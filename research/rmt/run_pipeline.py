"""Real transfer cohort and paired formation-context benchmark. No synthetic rows."""
from pathlib import Path
import sys, json, hashlib, platform, time
ROOT = Path(__file__).resolve().parent
local_packages = ROOT.parent / 'tmp' / 'python_packages'
if local_packages.exists(): sys.path.insert(0, str(local_packages))
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.inspection import permutation_importance
import joblib

OUT = ROOT / 'outputs'; OUT.mkdir(exist_ok=True)
LEAGUES = ['GB1', 'ES1', 'L1', 'IT1', 'FR1']
SEED = 42
BASE = ['pre_goals90', 'pre_assists90', 'pre_minutes', 'pre_appearances', 'pre_yellows90', 'pre_reds90', 'age', 'position_attack', 'position_midfield']
CTX = ['share_433', 'share_4231', 'share_442', 'share_three_back', 'formation_entropy', 'formation_coverage']

def score(y, p):
    return {'MAE': float(mean_absolute_error(y,p)), 'RMSE': float(np.sqrt(mean_squared_error(y,p)))}

def model(seed=SEED):
    return make_pipeline(SimpleImputer(strategy='median'), RandomForestRegressor(n_estimators=200, max_depth=8, min_samples_leaf=5, max_features=1.0, random_state=seed, n_jobs=1))

def run():
    started = time.time()
    manifest = {'retrieved_date': '2026-10-12', 'source': 'https://github.com/dcaribou/transfermarkt-datasets', 'files': {}}
    for name in ['appearances', 'games', 'players', 'transfers']:
        p = ROOT/'data'/f'{name}.csv.gz'
        manifest['files'][name] = {'url': f'https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/{name}.csv.gz', 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    (OUT/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
    games = pd.read_csv(ROOT/'data/games.csv.gz', parse_dates=['date'])
    games = games[games.competition_id.isin(LEAGUES) & games.season.between(2017,2024)].copy()
    players = pd.read_csv(ROOT/'data/players.csv.gz', usecols=['player_id','date_of_birth','position'])
    players.date_of_birth = pd.to_datetime(players.date_of_birth, errors='coerce')
    transfers = pd.read_csv(ROOT/'data/transfers.csv.gz', parse_dates=['transfer_date'])
    transfers = transfers[transfers.transfer_date.dt.year.between(2018,2024) & transfers.transfer_date.dt.month.between(6,9) & (transfers.from_club_id != transfers.to_club_id)].copy()
    audit = {'summer_transfer_rows_2018_2024_all_leagues': len(transfers)}
    transfers['season'] = transfers.transfer_date.dt.year
    transfers = transfers.drop_duplicates(['player_id','transfer_date','from_club_id','to_club_id'])
    apps = pd.read_csv(ROOT/'data/appearances.csv.gz', parse_dates=['date'], usecols=['appearance_id','game_id','player_id','player_club_id','date','minutes_played','goals','assists','yellow_cards','red_cards'])
    apps = apps.merge(games[['game_id','season','competition_id']], on='game_id', how='inner', validate='many_to_one')
    audit['top5_appearance_rows_before_cleaning'] = len(apps)
    dup = apps.duplicated('appearance_id'); audit['duplicate_appearances_removed'] = int(dup.sum()); apps = apps[~dup].copy()
    valid = apps.minutes_played.between(1,120) & apps[['goals','assists','yellow_cards','red_cards']].notna().all(axis=1) & apps[['goals','assists','yellow_cards','red_cards']].ge(0).all(axis=1)
    audit['invalid_appearance_rows_removed'] = int((~valid).sum()); apps = apps[valid]
    agg = apps.groupby(['player_id','player_club_id','season','competition_id']).agg(minutes=('minutes_played','sum'),appearances=('game_id','nunique'),goals=('goals','sum'),assists=('assists','sum'),yellows=('yellow_cards','sum'),reds=('red_cards','sum'),first_date=('date','min'),last_date=('date','max')).reset_index()
    before = agg.rename(columns={'player_club_id':'from_club_id','competition_id':'origin_league',**{x:'pre_'+x for x in ['minutes','appearances','goals','assists','yellows','reds','first_date','last_date']}})
    before['season'] += 1
    after = agg.rename(columns={'player_club_id':'to_club_id','competition_id':'destination_league',**{x:'post_'+x for x in ['minutes','appearances','goals','assists','yellows','reds','first_date','last_date']}})
    cohort = transfers.merge(before,on=['player_id','from_club_id','season'],how='inner').merge(after,on=['player_id','to_club_id','season'],how='inner').merge(players,on='player_id',validate='many_to_one')
    audit['linked_pre_post_top5_rows'] = len(cohort)
    cohort['age'] = (cohort.transfer_date-cohort.date_of_birth).dt.days/365.25
    eligible = (cohort.pre_minutes>=900) & (cohort.post_minutes>=450) & (cohort.age>=18) & cohort.position.isin(['Attack','Midfield','Defender']) & (cohort.pre_last_date<cohort.transfer_date) & (cohort.post_first_date>=cohort.transfer_date)
    cohort = cohort[eligible].sort_values(['transfer_date','player_id','from_club_id','to_club_id']).copy()
    audit['eligible_before_repeated_player_removal'] = len(cohort)
    cohort = cohort.drop_duplicates('player_id',keep='first').copy()
    audit['first_eligible_transfer_per_player'] = len(cohort)
    team_parts = []
    for side in ['home','away']:
        t=games[['season','competition_id','date',f'{side}_club_id',f'{side}_club_formation']].copy()
        t.columns=['season','league','date','club_id','formation']; team_parts.append(t)
    team = pd.concat(team_parts,ignore_index=True)
    context=[]
    for (club, season, league), t in team.groupby(['club_id','season','league']):
        # Provider appends labels such as 'Attacking' and 'double 6'.
        # Canonicalise the numerical scheme before calculating shares.
        f=t.formation.dropna().astype(str).str.extract(r'^(\d+(?:-\d+)+)',expand=False).dropna()
        freqs=f.value_counts(normalize=True)
        n=len(f)
        context.append({'to_club_id':club,'season':season+1,'destination_league':league,'context_last_date':t.date.max(),'context_matches':len(t),'share_433':float(f.eq('4-3-3').mean()) if n else np.nan,'share_4231':float(f.eq('4-2-3-1').mean()) if n else np.nan,'share_442':float(f.eq('4-4-2').mean()) if n else np.nan,'share_three_back':float(f.str.startswith('3-').mean()) if n else np.nan,'formation_entropy':float(-(freqs*np.log(freqs)).sum()) if n else np.nan,'formation_coverage':n/len(t)})
    cohort=cohort.merge(pd.DataFrame(context),on=['to_club_id','season','destination_league'],how='inner',validate='many_to_one')
    cohort=cohort[(cohort.context_matches>=20) & (cohort.formation_coverage>=0.8) & (cohort.context_last_date<cohort.transfer_date)].copy()
    for x in ['goals','assists','yellows','reds']:cohort['pre_'+x+'90']=90*cohort['pre_'+x]/cohort.pre_minutes
    cohort['target_ga90']=90*(cohort.post_goals+cohort.post_assists)/cohort.post_minutes
    cohort['position_attack']=cohort.position.eq('Attack').astype(int);cohort['position_midfield']=cohort.position.eq('Midfield').astype(int)
    cohort['cross_league']=cohort.origin_league.ne(cohort.destination_league)
    cohort['split']=np.select([cohort.season<=2021,cohort.season==2022],['train','validation'],default='test')
    audit['final_cohort']=len(cohort)
    assert not cohort.player_id.duplicated().any()
    assert (cohort.pre_last_date<cohort.transfer_date).all()
    assert (cohort.context_last_date<cohort.transfer_date).all()
    assert (cohort.post_first_date>=cohort.transfer_date).all()
    assert cohort[BASE+CTX+['target_ga90']].notna().all().all()
    cols=['player_id','player_name','transfer_date','from_club_id','to_club_id','season','origin_league','destination_league','position','cross_league','split','pre_last_date','context_last_date','post_first_date','post_minutes','post_goals','post_assists']+BASE+CTX+['target_ga90']
    cohort[cols].to_csv(OUT/'transfer_cohort.csv',index=False)
    train=cohort[cohort.split=='train']; val=cohort[cohort.split=='validation']; test=cohort[cohort.split=='test']
    results={'audit':audit,'split_counts':cohort.split.value_counts().to_dict(),'destination_counts':cohort.destination_league.value_counts().to_dict(),'position_counts':cohort.position.value_counts().to_dict(),'within_cross_counts':cohort.cross_league.value_counts().rename(index={True:'cross',False:'within'}).to_dict(),'validation':{},'test':{},'test_subgroups':{},'leave_league_out':{},'tests':{'unique_players':True,'predictors_before_transfer':True,'context_before_transfer':True,'outcomes_after_transfer':True,'no_missing_model_values':True},'software':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scikit-learn':sklearn.__version__},'config':{'seed':SEED,'n_estimators':200,'max_depth':8,'min_samples_leaf':5,'n_jobs':1,'base_features':BASE,'context_features':CTX}}
    preds=test[['player_id','player_name','season','destination_league','cross_league','position','target_ga90']].copy()
    for name,features in [('individual_rf',BASE),('formation_rf',BASE+CTX)]:
        m=model();m.fit(train[features],train.target_ga90)
        results['validation'][name]=score(val.target_ga90,m.predict(val[features]))
        p=m.predict(test[features]);preds[name]=p;results['test'][name]=score(test.target_ga90,p)
        for grp,mask in [('within',~test.cross_league),('cross',test.cross_league)]:
            results['test_subgroups'].setdefault(grp,{'n':int(mask.sum())})[name]=score(test.target_ga90[mask],p[mask])
        if name=='formation_rf':
            joblib.dump(m,OUT/'formation_rf.joblib')
            imp=permutation_importance(m,test[features],test.target_ga90,scoring='neg_mean_absolute_error',n_repeats=20,random_state=SEED,n_jobs=1)
            pd.DataFrame({'feature':features,'MAE_increase_mean':imp.importances_mean,'MAE_increase_std':imp.importances_std}).sort_values('MAE_increase_mean',ascending=False).to_csv(OUT/'permutation_importance.csv',index=False)
    dummy=DummyRegressor(strategy='mean');dummy.fit(train[BASE],train.target_ga90);results['test']['training_mean']=score(test.target_ga90,dummy.predict(test[BASE]))
    results['test']['persistence']=score(test.target_ga90,test.pre_goals90+test.pre_assists90)
    preds['abs_error_baseline']=abs(preds.target_ga90-preds.individual_rf);preds['abs_error_extended']=abs(preds.target_ga90-preds.formation_rf)
    preds.to_csv(OUT/'test_predictions.csv',index=False)
    preds.sort_values('abs_error_extended',ascending=False).head(10).to_csv(OUT/'largest_errors.csv',index=False)
    rng=np.random.default_rng(SEED); deltas=[]
    for _ in range(2000):
        ii=rng.integers(0,len(preds),len(preds)); q=preds.iloc[ii]
        deltas.append(score(q.target_ga90,q.individual_rf)['RMSE']-score(q.target_ga90,q.formation_rf)['RMSE'])
    results['paired_bootstrap_delta_RMSE']={'baseline_minus_extended':results['test']['individual_rf']['RMSE']-results['test']['formation_rf']['RMSE'],'ci95':np.quantile(deltas,[.025,.975]).tolist(),'resamples':2000,'unit':'unique player transfer'}
    results['seed_sensitivity']={}
    for seed in [7,2026]:
        r={}
        for name,features in [('individual_rf',BASE),('formation_rf',BASE+CTX)]:
            m=model(seed);m.fit(train[features],train.target_ga90);r[name]=score(test.target_ga90,m.predict(test[features]))
        results['seed_sensitivity'][str(seed)]=r
    results['test_position_metrics']={}
    for pos in ['Attack','Midfield','Defender']:
        q=preds[preds.position.eq(pos)]
        results['test_position_metrics'][pos]={'n':len(q),'individual_rf':score(q.target_ga90,q.individual_rf),'formation_rf':score(q.target_ga90,q.formation_rf)}
    higher_minutes=test.post_minutes>=900
    results['test_900_minutes_sensitivity']={'n':int(higher_minutes.sum()),'individual_rf':score(test.target_ga90[higher_minutes],preds.individual_rf[higher_minutes]),'formation_rf':score(test.target_ga90[higher_minutes],preds.formation_rf[higher_minutes])}
    for league in LEAGUES:
        tr=train[train.destination_league.ne(league) & train.origin_league.ne(league)]
        te=test[test.destination_league.eq(league) & test.origin_league.ne(league)]
        r={'n_train':len(tr),'n_test':len(te)}
        if len(te)<30:r['status']='too few test rows; descriptive only'
        for name,features in [('individual_rf',BASE),('formation_rf',BASE+CTX)]:
            m=model();m.fit(tr[features],tr.target_ga90);r[name]=score(te.target_ga90,m.predict(te[features]))
        results['leave_league_out'][league]=r
    results['seconds']=round(time.time()-started,2)
    (OUT/'results.json').write_text(json.dumps(results,indent=2))
    lines=[f'COHORT {len(cohort)} real transfers',f'SPLITS {results["split_counts"]}',f'TEST {results["test"]}',f'BOOTSTRAP {results["paired_bootstrap_delta_RMSE"]}',f'CHECKS {results["tests"]}',f'SOFTWARE {results["software"]}',f'RUNTIME {results["seconds"]} seconds']
    (OUT/'run_log.txt').write_text('\n'.join(lines));print('\n'.join(lines))

if __name__=='__main__':run()
