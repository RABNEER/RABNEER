import datetime as dt
import html
import json
import os
import urllib.request

USER = "RABNEER"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def gh(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def esc(value):
    return html.escape(str(value), quote=True)


events = gh(f"/users/{USER}/events/public?per_page=50")
commit = repo = sha = ago = None

for event in events:
    if event.get("type") != "PushEvent":
        continue
    commits = event.get("payload", {}).get("commits") or []
    if not commits:
        continue
    c = commits[-1]
    commit = c.get("message", "").split("\n", 1)[0][:64]
    sha = c.get("sha", "0000000")[:7]
    repo = event.get("repo", {}).get("name", "RABNEER/unknown").split("/", 1)[-1]
    created = event.get("created_at")
    if created:
        when = dt.datetime.fromisoformat(created.replace("Z", "+00:00"))
        delta = dt.datetime.now(dt.timezone.utc) - when
        seconds = max(0, int(delta.total_seconds()))
        if seconds < 60:
            ago = "just now"
        elif seconds < 3600:
            ago = f"{seconds // 60}m ago"
        elif seconds < 86400:
            ago = f"{seconds // 3600}h ago"
        else:
            ago = f"{seconds // 86400}d ago"
    break

if not commit:
    commit, repo, sha, ago = "no public pushes yet — go build something", "—", "0000000", "now"

svg = f'''<svg width="820" height="72" viewBox="0 0 820 72" xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
  <defs><clipPath id="wipe"><rect x="24" y="38" width="0" height="18"><animate attributeName="width" from="0" to="620" begin="0.25s" dur="1s" fill="freeze"/></rect></clipPath></defs>
  <rect width="820" height="72" rx="14" fill="#0B1420"/>
  <rect x="1.5" y="1.5" width="817" height="69" rx="12.5" fill="none" stroke="#2C4257" stroke-width="2"/>
  <circle cx="26" cy="22" r="5" fill="#7EE787"><animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/></circle>
  <text x="40" y="27" font-size="13" fill="#5D7B93">git log -1</text>
  <text x="796" y="27" text-anchor="end" font-size="12" fill="#3A5468">{esc(ago)}</text>
  <g clip-path="url(#wipe)"><text x="24" y="54" font-size="15" fill="#E6EDF3">{esc(commit)}</text></g>
  <text x="796" y="54" text-anchor="end" font-size="13" fill="#567C8D">{esc(repo)}@{esc(sha)}</text>
</svg>\n'''

os.makedirs("assets", exist_ok=True)
with open("assets/ticker.svg", "w", encoding="utf-8") as file:
    file.write(svg)

print(f"ticker: {commit} ({repo}@{sha}, {ago})")
