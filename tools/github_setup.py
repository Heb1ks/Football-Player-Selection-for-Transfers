"""Create the real issue tracker using the user's existing Git authentication.

Credentials stay in subprocess memory and are never printed or stored here.
Run with --check for read-only access verification. No token is required in files.
"""
from pathlib import Path
import subprocess, os, json, urllib.request, urllib.error, argparse, shutil
ROOT=Path(__file__).resolve().parents[1]
REPO='Heb1ks/Football-Player-Selection-for-Transfers'
GIT=shutil.which('git') or 'git'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--open-pr',action='store_true');parser.add_argument('--link-evidence',action='store_true');parser.add_argument('--status',action='store_true');args=parser.parse_args()
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never')
    found=subprocess.run([GIT,'credential','fill'],input='protocol=https\nhost=github.com\nusername=Heb1ks\n\n',text=True,capture_output=True,env=env)
    credential=dict(line.split('=',1) for line in found.stdout.splitlines() if '=' in line)
    token=credential.get('password')
    if not token:print('No reusable GitHub authentication found. No remote changes made.');return
    def request(path,method='GET',data=None):
        req=urllib.request.Request('https://api.github.com'+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json','User-Agent':'TransferLens-diploma-setup'})
        with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
    try:
        repo=request('/repos/'+REPO)
        print(json.dumps({'repository':repo['html_url'],'can_push':repo.get('permissions',{}).get('push',False),'issues_enabled':repo['has_issues']}))
        if args.check:return
        if args.status:
            runs=request('/repos/'+REPO+'/actions/runs?branch=testing-mvp-eskeN&per_page=5')['workflow_runs']
            result=[{'name':r['name'],'status':r['status'],'conclusion':r['conclusion'],'url':r['html_url'],'commit':r['head_sha']} for r in runs]
            (ROOT/'output/ci-status.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            print(json.dumps(result));return
        if args.link_evidence:
            pr=json.loads((ROOT/'output/pull-request.json').read_text())['url']
            links=json.loads((ROOT/'docs/github-issues.json').read_text())
            for task_id in ['DIP-01','DIP-02','DIP-03','DIP-04','DIP-05']:
                number=links[task_id]['number'];issue=request('/repos/'+REPO+'/issues/'+str(number))
                if pr not in (issue.get('body') or ''):
                    body=(issue.get('body') or '')+'\n\n## Implementation and review\n'+pr+'\n\nEvidence is available on branch testing-mvp-eskeN. This issue remains open pending team review.\n'
                    request('/repos/'+REPO+'/issues/'+str(number),'PATCH',{'body':body})
            print('Linked the actual draft PR to five implementation/documentation issues; all remain open.');return
        if args.open_pr:
            branch='testing-mvp-eskeN'
            existing=request('/repos/'+REPO+'/pulls?state=open&head=Heb1ks:'+branch)
            if existing:pr=existing[0]
            else:
                body=(ROOT/'docs/pull-request-body.md').read_text(encoding='utf-8')
                pr=request('/repos/'+REPO+'/pulls','POST',{'title':'DIP-01 to DIP-05 Add TransferLens prototype and approbation materials','head':branch,'base':'main','body':body,'draft':True})
            (ROOT/'output/pull-request.json').write_text(json.dumps({'url':pr['html_url'],'number':pr['number'],'draft':pr['draft']},indent=2),encoding='utf-8')
            print(json.dumps({'url':pr['html_url'],'draft':pr['draft']}));return
        tasks=json.loads((ROOT/'docs/tasks.json').read_text(encoding='utf-8'))
        existing=request('/repos/'+REPO+'/issues?state=all&per_page=100')
        links={}
        for task in tasks['tasks']:
            title=f"{task['id']} {task['title']}"
            matching=next((i for i in existing if i['title']==title),None)
            body=f"## Expected outcome\n{task['outcome']}\n\n## Acceptance criteria\n"+'\n'.join('- [ ] '+x for x in task['acceptance'])
            body+=f"\n\n## Planning\nPriority: {task['priority']}\nDue: {task['due']}\nPersonal owner: requires team confirmation.\n"
            body+='\n## Evidence\n'+('\n'.join('- `'+x+'`' for x in task['evidence']) or 'Pending')
            body+='\n\n## Status disclosure\n'+('Artifact implementation has been checked locally. Individual authorship and team review remain to be confirmed. This issue records the actual present status; it does not imply earlier progressive development.' if task['status']=='Done' else 'Current local status: '+task['status']+'. Completion evidence and review are required before closure.')
            if matching is None:matching=request('/repos/'+REPO+'/issues','POST',{'title':title,'body':body})
            links[task['id']]={'number':matching['number'],'url':matching['html_url']}
            task['issue_url']=matching['html_url']
            (ROOT/'docs/github-issues.json').write_text(json.dumps(links,indent=2),encoding='utf-8')
            (ROOT/'docs/tasks.json').write_text(json.dumps(tasks,indent=2,ensure_ascii=False),encoding='utf-8')
        team=json.loads((ROOT/'docs/team.json').read_text(encoding='utf-8'));team['shared_tracker']='https://github.com/'+REPO+'/issues'
        (ROOT/'docs/team.json').write_text(json.dumps(team,indent=2,ensure_ascii=False),encoding='utf-8')
        print(f'Created or reused {len(links)} real GitHub issues. No issues were closed or assigned without personal review.')
    except urllib.error.HTTPError as e:print(f'GitHub API access failed with HTTP {e.code}; existing local work is retained.');raise SystemExit(1)

if __name__=='__main__':main()
