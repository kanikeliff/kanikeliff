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
    stage = "adult" if n >= 14 else "young" if n >= 7 else "hatchling" if n else "egg"
    (ROOT/"assets/dragon.gif").write_bytes((ROOT/"dragon/stages"/(stage+".gif")).read_bytes())
    img = '<img src="assets/dragon.gif" width="420" alt="A pixel dragon growing with my GitHub activity">'
    path = ROOT/"README.md"
    import re
    md = path.read_text()
    md = re.sub(r'<!-- elif-dragon:start -->.*?<!-- elif-dragon:end -->\s*', '', md, flags=re.S)
    md = re.sub(r'<img\b[^>]*src="assets/(?:mascot|dragon)\.gif"[^>]*>\s*', '', md)
    path.write_text(f"{START}\n{img}\n{END}\n\n"+md.lstrip())


if __name__ == "__main__":
    update(count_streak(datetime.now(timezone.utc)))
