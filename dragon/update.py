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


def get_days(now):
    cursor = now.date()
    last = now
    first = (now - timedelta(days=(now.weekday()+1)%7+29*7)).replace(hour=0, minute=0, second=0, microsecond=0)
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
    return first.date(), days


def render_calendar(first, today, days):
    colors = ['#292336', '#59406e', '#80559c', '#aa78c6', '#dab0eb']
    cells = []
    for i in range((today-first).days+1):
        day = first + timedelta(days=i)
        count = days[day.isoformat()]
        level = sum(count >= threshold for threshold in (1,3,6,10))
        cells.append(f'<rect x="{3+i//7*14}" y="{3+i%7*14}" width="11" height="11" rx="2" fill="{colors[level]}"><title>{day}: {count}</title></rect>')
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 100"><title>GitHub contribution calendar</title>' + ''.join(cells) + '</svg>'
    (ROOT/'assets/calendar.svg').write_text(svg)


def update(n):
    stage = "adult" if n >= 14 else "young" if n >= 7 else "hatchling" if n else "egg"
    (ROOT/"assets/dragon.gif").write_bytes((ROOT/"dragon/stages"/(stage+".gif")).read_bytes())
    img = '<img src="assets/dragon.gif" width="420" alt="A pixel dragon growing with my GitHub activity">'
    img += '<br>\n<img src="assets/calendar.svg" width="420" alt="GitHub contributions over the last 30 weeks">'
    path = ROOT/"README.md"
    import re
    md = path.read_text()
    md = re.sub(r'<!-- elif-dragon:start -->.*?<!-- elif-dragon:end -->\s*', '', md, flags=re.S)
    md = re.sub(r'<img\b[^>]*src="assets/(?:mascot|dragon)\.gif"[^>]*>\s*', '', md)
    path.write_text(f"{START}\n{img}\n{END}\n\n"+md.lstrip())


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    first, days = get_days(now)
    render_calendar(first, now.date(), days)
    day = now.date()
    if days[day.isoformat()] == 0:
        day -= timedelta(days=1)
    n = 0
    while n < 14 and days[day.isoformat()] > 0:
        n += 1
        day -= timedelta(days=1)
    update(n)
