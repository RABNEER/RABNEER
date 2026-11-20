import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.request

TOKEN = os.environ['GITHUB_TOKEN']
USER = os.environ.get('GITHUB_REPOSITORY_OWNER', 'RABNEER')

def query(q, variables):
    req = urllib.request.Request('https://api.github.com/graphql', data=json.dumps({'query': q, 'variables': variables}).encode(), headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json', 'User-Agent': 'profile-telemetry'})
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)
    if result.get('errors'):
        raise RuntimeError(result['errors'])
    return result['data']['user']

user = query('query($login:String!){user(login:$login){createdAt}}', {'login': USER})
if not user:
    raise RuntimeError('GitHub user not found')
start_year = int(user['createdAt'][:4])
today = dt.datetime.now(dt.timezone.utc).date()
counts = {}
q = '''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''
for year in range(start_year, today.year + 1):
    begin = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
    end = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), dt.datetime.now(dt.timezone.utc))
    data = query(q, {'login': USER, 'from': begin.isoformat(), 'to': end.isoformat()})
    for week in data['contributionsCollection']['contributionCalendar']['weeks']:
        for day in week['contributionDays']:
            date = dt.date.fromisoformat(day['date'])
            if date <= today:
                counts[date] = day['contributionCount']
if not counts:
    raise RuntimeError('No contribution calendar data returned')
longest = run = 0
for date in sorted(counts):
    run = run + 1 if counts[date] else 0
    longest = max(longest, run)
last = today if counts.get(today, 0) else today - dt.timedelta(days=1)
current = 0
while counts.get(last, 0):
    current += 1
    last -= dt.timedelta(days=1)
values = {'total': sum(counts.values()), 'current': current, 'longest': longest}
p = Path('assets/profile.svg')
s = p.read_text(encoding='utf-8')
for key, value in values.items():
    s, n = re.subn(r'(id="stat-' + key + r'">)[^<]*(</text>)', lambda m: m[1] + f'{value:,}' + m[2], s)
    if n != 1:
        raise RuntimeError(f'Expected one stat-{key} element, got {n}')
p.write_text(s, encoding='utf-8')
print('Updated contribution telemetry:', values)
