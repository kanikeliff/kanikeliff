import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- elif-dragon:start -->'
END = '<!-- elif-dragon:end -->'
QUERY = """query($start:DateTime!, $end:DateTime!) {
 user(login:"kanikeliff") { contributionsCollection(from:$start,to:$end) {
 contributionCalendar { weeks { contributionDays { date contributionCount } } }
 } } }"""


def count_streak(now):
    cursor = now.date()
    last = now
    streak = 0
    while True:
        first = (last - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
        req = Request('https://api.github.com/graphql', data=json.dumps({
            'query': QUERY, 'variables': {'start': first.isoformat(), 'end': last.isoformat()}
        }).encode(), headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],
                              'Content-Type':'application/json','User-Agent':'Elif-Dragon'})
        with urlopen(req, timeout=30) as response:
            result = json.load(response)
        if result.get('errors'):
            raise RuntimeError('GitHub calendar request failed')
        weeks = result['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
        days = {d['date']:d['contributionCount'] for w in weeks for d in w['contributionDays']}
        if cursor == now.date() and days[cursor.isoformat()] == 0:
            cursor -= timedelta(days=1)
        while cursor >= first.date():
            if not days[cursor.isoformat()]:
                return streak
            streak += 1
            cursor -= timedelta(days=1)
        last = first - timedelta(seconds=1)


def update(n):
    stages = [(14,'adult','Adult'),(7,'young','Young dragon'),(1,'hatchling','Hatchling'),(0,'egg','Egg')]
    _,stage,label = next(row for row in stages if n >= row[0])
    path = ROOT/'README.md'
    md = path.read_text()
    status = f"**{n}-day contribution streak** · {label}"
    future = next((k for k in (1,7,14) if k>n),None)
    if future:
        status += f" · Next stage at {future} days"
    section = f"{START}\n{status}\n\n\n{END}"
    if START in md or END in md:
        if md.count(START)!=1 or md.count(END)!=1 or md.index(START)>=md.index(END):
            raise ValueError('Check dragon section markers in README.md')
        md = md[:md.index(START)] + section + md[md.index(END)+len(END):]
    else:
        md = section+'\n\n'+md
    (ROOT/'assets/dragon.gif').write_bytes((ROOT/'dragon/stages'/f'{stage}.gif').read_bytes())
    path.write_text(md)


if __name__=='__main__':
    update(count_streak(datetime.now(timezone.utc)))
