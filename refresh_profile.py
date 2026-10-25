"""Refresh the public-only GitHub profile panels. Python standard library only."""
import json, re, os, sys
from datetime import datetime, timezone
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
USER = 'adkhan001'

def get(url):
    headers={'User-Agent':'adkhan001-profile','Accept':'application/vnd.github+json'}
    # Only send the ephemeral token to api.github.com, never to another host.
    if url.startswith('https://api.github.com/') and os.getenv('GH_TOKEN'):
        headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
    with urlopen(Request(url,headers=headers),timeout=40) as response:
        return response.read().decode()

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__(); self.days={}
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('data-date') and a.get('data-level'):
            self.days[a['data-date']]=int(a['data-level'])

def label(x,y,value,size=16,color='#9dacc9',attrs=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}" {attrs}>{escape(str(value))}</text>'

def shell(body,height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img">
<defs><linearGradient id="line"><stop stop-color="#63eaf2"/><stop offset="1" stop-color="#ac79f4"/></linearGradient></defs>
<rect width="1200" height="{height}" rx="18" fill="#080f20"/><rect x="1" y="1" width="1198" height="{height-2}" rx="17" fill="none" stroke="#263855"/>{body}</svg>'''

def render(user,repos,calendar_html):
    cal=Calendar();cal.feed(calendar_html)
    days=sorted(cal.days.items())
    if len(days)<350: raise RuntimeError('Calendar incomplete; preserving previous panels.')
    heading=re.search(r'([\d,]+)\s+contributions?\s+in the last year',calendar_html)
    if not heading: raise RuntimeError('Contribution total missing; preserving previous panels.')
    total=heading.group(1)
    stars=sum(r['stargazers_count'] for r in repos if not r['fork'])
    b=label(30,36,'01  /  SIGNAL FROM GITHUB',13,'#79e9ee','letter-spacing="2"')
    date=datetime.now(timezone.utc).strftime('%d %b %Y')
    b+=label(1170,36,'PUBLIC DATA  ·  '+date,11,'#8b9bbc','text-anchor="end" letter-spacing="1"')
    for i,(value,name) in enumerate([(user['public_repos'],'PUBLIC REPOSITORIES'),(total,'CONTRIBUTIONS / YEAR'),(stars,'STARS · ORIGINAL REPOS'),(user['followers'],'FOLLOWERS')]):
        x=24+i*294
        b+=f'<rect x="{x}" y="58" width="282" height="100" rx="10" fill="#101a30" stroke="#293e5e"/>'
        b+=label(x+19,103,value,32,'#e8f8ff','font-weight="bold"')+label(x+19,136,name,11,'#8db3ce','letter-spacing="1"')
        b+=f'<path d="M{x+245} 87 l8 -8 8 8 -8 8 Z" fill="none" stroke="#86a2e9"/>'
    b+=label(30,199,'THE CONTRIBUTION CONSTELLATION',12,'#bdacf4','letter-spacing="1.5"')
    colors=['#152239','#244a65','#2c7a99','#4cb7c7','#86efe0']
    start=datetime.fromisoformat(days[0][0]);offset=(start.weekday()+1)%7
    for i,(date_str,level) in enumerate(days):
        col=(i+offset)//7; row=(i+offset)%7
        b+=f'<rect x="{30+col*20}" y="{218+row*18}" width="15" height="13" rx="3" fill="{colors[max(0,min(level,4))]}"><title>{date_str}: GitHub activity level {level}/4</title></rect>'
    b+=label(30,374,'One square. One day. Keep building.',13,'#8ea2be')
    b+=label(954,374,'LESS',10,'#8ea2be')
    for i,c in enumerate(colors): b+=f'<rect x="{990+i*21}" y="363" width="15" height="13" rx="3" fill="{c}"/>'
    b+=label(1104,374,'MORE',10,'#8ea2be')
    (ROOT/'mission-stats.svg').write_text(shell(b,400))
    # Store only public fields required to audit the generated panel.
    (ROOT/'profile-snapshot.json').write_text(json.dumps({'updated_utc':datetime.now(timezone.utc).isoformat(),'public_repos':user['public_repos'],'followers':user['followers'],'stars_original_repositories':stars,'contributions_last_year':int(total.replace(',','')),'calendar_source':f'https://github.com/users/{USER}/contributions'},indent=2)+'\n')

if __name__=='__main__':
    if '--offline' in sys.argv:
        user=json.loads((ROOT/'user.json').read_text());repos=json.loads((ROOT/'repos.json').read_text());html=(ROOT/'contributions.html').read_text()
    else:
        user=json.loads(get(f'https://api.github.com/users/{USER}'))
        repos=[];page=1
        while True:
            batch=json.loads(get(f'https://api.github.com/users/{USER}/repos?per_page=100&page={page}'))
            repos.extend(batch)
            if len(batch)<100: break
            page+=1
        html=get(f'https://github.com/users/{USER}/contributions')
    render(user,repos,html)
