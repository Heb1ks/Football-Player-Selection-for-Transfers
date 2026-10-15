import unittest, json, threading, urllib.request, urllib.error
import numpy as np
from app.core import Engine, BASE, CTX, ROOT
from app.server import make_handler
from http.server import ThreadingHTTPServer

class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.e=Engine()
    def test_chronology_and_unique_players(self):
        c=self.e.cohort
        self.assertEqual(len(c),781);self.assertFalse(c.player_id.duplicated().any())
        self.assertTrue((c.pre_last_date<c.transfer_date).all())
        self.assertTrue((c.context_last_date<c.transfer_date).all())
        self.assertTrue((c.post_first_date>=c.transfer_date).all())
        self.assertEqual(c.groupby('split').size().to_dict(),{'test':242,'train':405,'validation':134})
    def test_saved_predictions_match_original_benchmark(self):
        import pandas as pd
        truth=pd.read_csv(ROOT/'research/rmt/outputs/test_predictions.csv').set_index('player_id')
        for season in [2023,2024]:
            rows=self.e.rank({'season':season,'position':'All','max_age':50})['rows']
            for r in rows:
                self.assertAlmostEqual(r['individual_prediction'],truth.loc[r['player_id'],'individual_rf'],places=8)
                self.assertAlmostEqual(r['context_prediction'],truth.loc[r['player_id'],'formation_rf'],places=8)
    def test_filter_and_order(self):
        rows=self.e.rank({'season':2024,'max_age':25,'position':'Attack'})['rows']
        self.assertTrue(rows)
        self.assertTrue(all(r['age']<=25 and r['position']=='Attack' and r['season']==2024 for r in rows))
        self.assertEqual([r['prediction'] for r in rows],sorted([r['prediction'] for r in rows],reverse=True))
    def test_target_is_not_a_predictor(self):
        self.assertFalse(set(BASE+CTX)&{'target_ga90','post_minutes','post_goals','post_assists'})
        before=self.e.rank({})['rows']
        original=self.e.cohort.target_ga90.copy()
        try:
            self.e.cohort['target_ga90']=999
            after=self.e.rank({})['rows']
            self.assertEqual([x['prediction'] for x in before],[x['prediction'] for x in after])
        finally:self.e.cohort['target_ga90']=original
    def test_changed_club_uses_prior_context(self):
        club=self.e.metadata()['clubs'][0]
        rows=self.e.rank({'season':club['season'],'club':club['to_club_id'],'position':'All'})['rows']
        self.assertTrue(rows)
        self.assertTrue(all(r['scenario_club']==club['destination_club'] and r['context_last_date']<r['transfer_date'] for r in rows))
        self.assertTrue(any(not r['factual_context'] for r in rows))
    def test_invalid_parameters(self):
        for q in [{'season':2022},{'season':2023.5},{'max_age':'nan'},{'max_age':17},{'min_minutes':1},{'position':'Keeper'},{'league':'XX'},{'model':'evil'},{'club':9999999}]:
            with self.subTest(q=q),self.assertRaises(ValueError):self.e.rank(q)
    def test_empty_and_literal_search(self):
        self.assertEqual(self.e.rank({'search':'<no-player>'})['rows'],[])
        self.assertEqual(self.e.rank({'search':'.*'})['rows'],[])

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(Engine()))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def get(self,path):return urllib.request.urlopen(self.base+path)
    def test_pages_and_metadata(self):
        for p in ['/','/board','/app.js','/board.js','/style.css','/api/meta','/api/tasks']:
            with self.subTest(path=p),self.get(p) as r:self.assertEqual(r.status,200)
    def test_rank_and_export(self):
        with self.get('/api/rank?season=2024&position=Attack') as r: data=json.load(r)
        self.assertGreater(data['count'],0)
        with self.get('/api/export?season=2024&position=Attack') as r:
            text=r.read().decode('utf-8-sig');self.assertEqual(len(text.splitlines()),data['count']+1)
            self.assertIn('scenario_club',text);self.assertNotIn('observed_original_ga90',text)
    def test_invalid_request(self):
        with self.assertRaises(urllib.error.HTTPError) as c:self.get('/api/rank?max_age=nan')
        self.assertEqual(c.exception.code,400)
    def test_private_files_unreachable(self):
        for p in ['/../docs/team.json','/models/individual_rf.joblib','/.git/config']:
            with self.subTest(path=p),self.assertRaises(urllib.error.HTTPError) as c:self.get(p)
            self.assertEqual(c.exception.code,404)

if __name__=='__main__':unittest.main(verbosity=2)
