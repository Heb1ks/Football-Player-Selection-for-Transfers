from pathlib import Path
import json, math
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parents[1]
BASE = ['pre_goals90','pre_assists90','pre_minutes','pre_appearances','pre_yellows90','pre_reds90','age','position_attack','position_midfield']
CTX = ['share_433','share_4231','share_442','share_three_back','formation_entropy','formation_coverage']
LEAGUES = {'GB1':'Premier League','ES1':'La Liga','L1':'Bundesliga','IT1':'Serie A','FR1':'Ligue 1'}

def number(value, name, low, high):
    try: result = float(value)
    except (ValueError, TypeError): raise ValueError(f'{name} must be a number')
    if not math.isfinite(result) or not low <= result <= high: raise ValueError(f'{name} must be between {low} and {high}')
    return result

class Engine:
    def __init__(self):
        self.cohort = pd.read_csv(ROOT / 'data/cohort.csv')
        self.models = {key:joblib.load(ROOT / 'models' / f'{key}.joblib') for key in ['individual_rf','formation_rf']}
        self.metrics = json.loads((ROOT / 'data/results.json').read_text(encoding='utf-8'))

    def metadata(self):
        clubs = self.cohort[self.cohort.split.eq('test')][['season','to_club_id','destination_club','context_last_date']].drop_duplicates().sort_values(['season','destination_club'])
        return {'leagues':LEAGUES, 'clubs':clubs.to_dict(orient='records'), 'metrics':self.metrics, 'total':len(self.cohort), 'test_rows':242, 'version':'0.1.0', 'snapshot':'2026-10-12'}

    def rank(self, query):
        season = int(number(query.get('season',2023),'season',2023,2024))
        if str(query.get('season',2023)) not in ['2023','2024']: raise ValueError('season must be 2023 or 2024')
        max_age = number(query.get('max_age',40),'max_age',18,50)
        minutes = number(query.get('min_minutes',900),'min_minutes',900,5000)
        position = query.get('position','Attack')
        if position not in ['All','Attack','Midfield','Defender']: raise ValueError('Unknown position')
        league = query.get('league','All')
        if league not in ['All',*LEAGUES]: raise ValueError('Unknown league')
        model_name = query.get('model','individual_rf')
        if model_name not in self.models: raise ValueError('Unknown model')
        q = self.cohort[self.cohort.split.eq('test') & self.cohort.season.eq(season)].copy()
        q = q[q.age.le(max_age) & q.pre_minutes.ge(minutes)]
        if position != 'All': q = q[q.position.eq(position)]
        if league != 'All': q = q[q.origin_league.eq(league)]
        search = str(query.get('search','')).strip()[:100]
        if search: q = q[q.player_name.str.contains(search, case=False, regex=False)]
        destination = query.get('club','')
        context_label = 'Recorded destination'
        if destination:
            club = int(number(destination,'club',1,10000000))
            candidates = self.cohort[self.cohort.split.eq('test') & self.cohort.season.eq(season) & self.cohort.to_club_id.eq(club)]
            if candidates.empty: raise ValueError('No eligible historical context for this club and season')
            context = candidates.iloc[0]
            q = q[q.from_club_id.ne(club) & q.transfer_date.gt(context.context_last_date)].copy()
            for col in CTX: q[col] = context[col]
            q['context_last_date'] = context.context_last_date
            q['scenario_club_id'] = club
            q['scenario_club'] = context.destination_club
            context_label = context.destination_club
        else:
            q['scenario_club_id'] = q.to_club_id
            q['scenario_club'] = q.destination_club
        if q.empty: return {'rows':[], 'count':0, 'context':context_label, 'model':model_name}
        # Explicit feature allowlists prevent observed post-transfer outputs entering inference.
        q['individual_prediction'] = self.models['individual_rf'].predict(q[BASE])
        q['context_prediction'] = self.models['formation_rf'].predict(q[BASE+CTX])
        q['prediction'] = q.individual_prediction if model_name == 'individual_rf' else q.context_prediction
        q['persistence'] = q.pre_goals90 + q.pre_assists90
        q['factual_context'] = q.scenario_club_id.eq(q.to_club_id)
        q['observed_original_ga90'] = q.target_ga90
        q = q.sort_values(['prediction','player_id'], ascending=[False,True])
        cols = ['player_id','player_name','season','age','position','origin_league','destination_league','origin_club','destination_club','scenario_club','transfer_date','pre_last_date','context_last_date','pre_minutes','pre_appearances','pre_goals90','pre_assists90','prediction','individual_prediction','context_prediction','persistence','factual_context','observed_original_ga90',*CTX]
        return {'rows':json.loads(q[cols].to_json(orient='records')), 'count':len(q), 'context':context_label, 'model':model_name}
