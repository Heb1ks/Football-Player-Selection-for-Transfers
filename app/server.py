"""Read-only local HTTP API; accepts no uploads and runs no arbitrary commands."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import sys, json, mimetypes, argparse, csv, io
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core import Engine, ROOT

def make_handler(engine):
    class Handler(BaseHTTPRequestHandler):
        def send(self, body, code=200, mime='application/json; charset=utf-8'):
            if not isinstance(body, bytes): body = body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Cache-Control','no-store')
            self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            url = urlparse(self.path)
            query = {k:v[0] for k,v in parse_qs(url.query).items()}
            try:
                if url.path == '/api/meta': self.send(json.dumps(engine.metadata(),ensure_ascii=False)); return
                if url.path in ['/api/rank','/api/export']:
                    result = engine.rank(query)
                    if url.path.endswith('export'):
                        ids = query.get('ids','')
                        rows = result['rows']
                        if ids:
                            selected = {int(x) for x in ids.split(',')}
                            rows = [r for r in rows if r['player_id'] in selected]
                        stream = io.StringIO()
                        fields = ['player_id','player_name','season','position','age','origin_club','scenario_club','prediction','individual_prediction','context_prediction','pre_last_date','context_last_date','factual_context']
                        writer = csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader()
                        for row in rows:
                            # Neutralise formula-like display text in spreadsheet exports.
                            writer.writerow({k:('\''+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v) for k,v in row.items()})
                        self.send('\ufeff'+stream.getvalue(),mime='text/csv; charset=utf-8');return
                    self.send(json.dumps(result,ensure_ascii=False));return
                if url.path == '/api/tasks':
                    self.send((ROOT / 'docs/tasks.json').read_bytes());return
                allowed = {'/':'index.html','/index.html':'index.html','/app.js':'app.js','/style.css':'style.css','/board':'board.html','/board.js':'board.js'}
                if url.path not in allowed: self.send('{"error":"Not found"}',404);return
                file = ROOT / 'app/static' / allowed[url.path]
                self.send(file.read_bytes(),mime=(mimetypes.guess_type(str(file))[0] or 'text/plain')+'; charset=utf-8')
            except (ValueError,TypeError) as e: self.send(json.dumps({'error':str(e)}),400)
            except Exception:
                self.send('{"error":"Internal error; inspect the server terminal"}',500)
                import traceback;traceback.print_exc()
    return Handler

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(Engine()))
    print(f'TransferLens ready at http://127.0.0.1:{args.port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
