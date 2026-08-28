import datetime as dt
import html
import json
import os
import urllib.request
from xml.sax.saxutils import escape

USER = "RABNEER"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def graphql(query):
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, method="POST")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]


query = f'''{{ user(login: "{USER}") {{ contributionsCollection {{ contributionCalendar {{ totalContributions weeks {{ contributionDays {{ contributionCount date color }} }} }} }} }} }}'''
data = graphql(query)
calendar = data["contributionCalendar"]
weeks = calendar["weeks"]
total = calendar["totalContributions"]

CELL = 11
GAP = 3
LEFT = 34
TOP = 48
WIDTH = LEFT + len(weeks) * (CELL + GAP) + 24
HEIGHT = 118

rects = []
for x, week in enumerate(weeks):
    for y, day in enumerate(week["contributionDays"]):
        fill = day["color"]
        rx = LEFT + x * (CELL + GAP)
        ry = TOP + y * (CELL + GAP)
        rects.append(f'<rect x="{rx}" y="{ry}" width="{CELL}" height="{CELL}" rx="2" fill="{escape(fill)}"><title>{escape(day["date"])} · {day["contributionCount"]} contributions</title></rect>')

# simple month labels from the first week of each month
months = []
seen = set()
for x, week in enumerate(weeks):
    if not week["contributionDays"]:
        continue
    d = dt.date.fromisoformat(week["contributionDays"][0]["date"])
    key = (d.year, d.month)
    if key not in seen:
        seen.add(key)
        months.append((x, d.strftime("%b")))
labels = []
for x, label in months:
    labels.append(f'<text x="{LEFT + x * (CELL + GAP)}" y="28" font-size="10" fill="#5D7B93">{label}</text>')

svg = f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="#0B1420"/>
  <rect x="1.5" y="1.5" width="{WIDTH-3}" height="{HEIGHT-3}" rx="12.5" fill="none" stroke="#2C4257" stroke-width="2"/>
  <text x="24" y="26" font-size="13" fill="#8BABC9">ranveer@github — contributions</text>
  <text x="{WIDTH-24}" y="26" text-anchor="end" font-size="12" fill="#7EE787">{total} contributions</text>
  {''.join(labels)}
  {''.join(rects)}
  <text x="24" y="108" font-size="10" fill="#3A5468">less</text>
  <rect x="54" y="101" width="10" height="10" rx="2" fill="#161B22"/>
  <rect x="69" y="101" width="10" height="10" rx="2" fill="#0E4429"/>
  <rect x="84" y="101" width="10" height="10" rx="2" fill="#006D32"/>
  <rect x="99" y="101" width="10" height="10" rx="2" fill="#26A641"/>
  <rect x="114" y="101" width="10" height="10" rx="2" fill="#39D353"/>
  <text x="132" y="110" font-size="10" fill="#3A5468">more</text>
</svg>\n'''

os.makedirs("assets", exist_ok=True)
with open("assets/activity.svg", "w", encoding="utf-8") as file:
    file.write(svg)

print(f"activity: {total} contributions")
