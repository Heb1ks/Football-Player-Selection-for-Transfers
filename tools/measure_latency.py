from pathlib import Path
import urllib.request, time, json, statistics
ROOT=Path(__file__).resolve().parents[1]
url='http://127.0.0.1:8765/api/rank?season=2023&position=All&max_age=50'
with urllib.request.urlopen(url) as r:json.load(r)
times=[]
for _ in range(30):
    start=time.perf_counter()
    with urllib.request.urlopen(url) as r:data=json.load(r)
    times.append((time.perf_counter()-start)*1000)
result={'date':'2026-10-15','scope':'30 warm serial local HTTP requests; 2023 all-position test pool; not a production load test','rows':data['count'],'requests':len(times),'p50_ms':statistics.median(times),'p95_ms':sorted(times)[28],'maximum_ms':max(times),'target_p95_ms':2000,'pass':sorted(times)[28]<2000}
(ROOT/'output/latency.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
