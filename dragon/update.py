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
    from PIL import Image, ImageDraw, ImageFont
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=209)).replace(hour=0,minute=0,second=0,microsecond=0)
    req = Request('https://api.github.com/graphql', data=json.dumps({'query':QUERY,'variables':{'start':start.isoformat(),'end':now.isoformat()}}).encode(),
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/json','User-Agent':'Elif-Dragon'})
    with urlopen(req,timeout=30) as response:
        result=json.load(response)
    if result.get('errors'): raise RuntimeError('Calendar unavailable')
    weeks=result['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    counts={d['date']:d['contributionCount'] for w in weeks for d in w['contributionDays']}
    stage=next(s for threshold,s in [(14,'adult'),(7,'young'),(1,'hatchling'),(0,'egg')] if n>=threshold)
    draw_card(counts,start.date(),now.date(),n,stage)
    path=ROOT/'README.md';md=path.read_text()
    import re
    md=re.sub(r'<img[^>]*src="assets/mascot.gif"[^>]*>\s*','',md)
    md=re.sub(r'<!-- elif-dragon:start -->.*?<!-- elif-dragon:end -->\s*','',md,flags=re.S)
    md='<!-- elif-dragon:start -->\n<img src="assets/dragon.gif" width="540" alt="My dragon, current streak and contribution calendar">\n<!-- elif-dragon:end -->\n\n'+md.lstrip()
    path.write_text(md)


def draw_card(counts,start,today,n,stage):
    from PIL import Image,ImageDraw,ImageFont
    import math
    def font(size):
        for path in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/System/Library/Fonts/Supplemental/Arial.ttf']:
            if Path(path).exists(): return ImageFont.truetype(path,size)
        return ImageFont.load_default()
    base=Image.new('RGB',(600,600),'#0d1117');d=ImageDraw.Draw(base)
    d.rounded_rectangle((1,1,598,598),radius=20,fill='#12121e',outline='#45394e',width=2)
    d.text((24,20),'@kanikeliff',font=font(23),fill='#eee6f4')
    d.rounded_rectangle((24,65,576,350),radius=15,fill='#251c38',outline='#5d4677')
    d.text((28,367),str(sum(counts.values()))+' contributions',font=font(24),fill='#e4d5ef')
    d.text((28,405),str(n)+'-day streak',font=font(17),fill='#c4a4e7')
    d.text((28,565),'Last 210 days · UTC',font=font(13),fill='#a497b3')
    d.rounded_rectangle((420,370,571,403),radius=8,fill='#3b2b50',outline='#bd97dc')
    d.text((433,377),stage.upper(),font=font(16),fill='#d7b7ed')
    colors=['#242330','#513764','#795294','#a57ac4','#ceb0ed']
    for i in range(210):
        day=start+timedelta(days=i);c=counts.get(day.isoformat(),0)
        level=0 if c==0 else 1 if c<3 else 2 if c<6 else 3 if c<10 else 4
        x=28+(i//7)*18;y=443+(i%7)*16
        d.rounded_rectangle((x,y,x+13,y+12),radius=2,fill=colors[level])
    sp=Image.open(ROOT/'dragon/mascots'/f'{stage}.gif');frames=[]
    for i in range(64):
        im=base.copy();sp.seek(int(i*sp.n_frames/64)%sp.n_frames)
        sprite=sp.convert('RGBA')
        sprite=sprite.resize((210,210),Image.Resampling.NEAREST)
        x=300+round(35*math.sin(i*2*math.pi/64)) if stage in ('adult','young') else 300
        im.paste(sprite,(x-105,100),sprite)
        frames.append(im.quantize(128))
    frames[0].save(ROOT/'assets/dragon.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=False)


if __name__=='__main__':
    update(count_streak(datetime.now(timezone.utc)))
