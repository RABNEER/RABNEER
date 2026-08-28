import datetime as dt
import json
import os
import urllib.request

USER = "RABNEER"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def gh(path: str):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


user = gh(f"/users/{USER}")
repos = gh(f"/users/{USER}/repos?per_page=100&sort=updated")

stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos)
public_repos = int(user.get("public_repos", len(repos)))
followers = int(user.get("followers", 0))

# Small fixed scales keep the panel visually stable as numbers grow.
metrics = [
    ("STARGAZERS", stars, 150, "#567C8D"),
    ("FOLLOWERS", followers, 80, "#79C0FF"),
    ("PUBLIC REPOS", public_repos, 40, "#7EE787"),
    ("CURIOSITY", 99.9, 100, "#F0B429"),
    ("CAFFEINE", 97.3, 100, "#FF6B6B"),
]

W, ROW_H, Y0 = 820, 46, 96
H = Y0 + len(metrics) * ROW_H + 24
parts = []

for i, (label, value, cap, color) in enumerate(metrics):
    y = Y0 + i * ROW_H
    ratio = min(1.0, float(value) / cap)
    width = max(12.0, 240.0 * ratio)
    begin = 0.2 * i + 0.15
    display = f"{value:.1f}" if isinstance(value, float) else str(value)
    parts.append(f'''  <g opacity="0">
    <set attributeName="opacity" to="1" begin="{begin:.2f}s" dur="0.1s" fill="freeze"/>
    <text x="30" y="{y+14}" font-size="14" fill="#5D7B93">{label}</text>
    <rect x="220" y="{y}" width="260" height="14" rx="7" fill="#16283A"/>
    <rect x="220" y="{y}" width="0" height="14" rx="7" fill="{color}">
      <animate attributeName="width" from="0" to="{width:.1f}" begin="{begin:.2f}s" dur="0.9s" fill="freeze"/>
    </rect>
    <text x="496" y="{y+13}" font-size="14" fill="#E6EDF3">{display}</text>
  </g>''')

svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
  <rect width="{W}" height="{H}" rx="14" fill="#0B1420"/>
  <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="12.5" fill="none" stroke="#2C4257" stroke-width="2"/>
  <circle cx="26" cy="24" r="5" fill="#27C93F"/>
  <text x="42" y="29" font-size="14" fill="#8BABC9">ranveer@github — system monitor</text>
  <text x="{W-26}" y="29" text-anchor="end" font-size="12" fill="#3A5468">last sync {dt.date.today().isoformat()}</text>
  <line x1="0" y1="44" x2="{W}" y2="44" stroke="#1D2F40"/>
{''.join(parts)}
</svg>
'''

os.makedirs("assets", exist_ok=True)
with open("assets/panel.svg", "w", encoding="utf-8") as file:
    file.write(svg)

print(f"panel written: {stars} stars, {followers} followers, {public_repos} public repos")
