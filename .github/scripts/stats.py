"""assets/stats.svg panelini GitHub'daki güncel verilerle yeniden çizer.

GitHub Actions'ta günde bir kez çalışır (bkz. .github/workflows/update.yml).
Yerelde denemek için: GITHUB_TOKEN=... python .github/scripts/stats.py
"""
import json
import os
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape

USER = 'Hud-Alfa'
PORTFOLIO_PROJECTS = 13  # hudalfa.vercel.app'teki proje sayısı; değişince burayı güncelle
TOKEN = os.environ['GITHUB_TOKEN']
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'stats.svg')

W = 840
FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, Inter, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SFMono-Regular', 'JetBrains Mono', Consolas, monospace"
TEAL, BLUE, PURPLE = '#56D0C8', '#4F8DF7', '#8B6CF6'
LANG_COLORS = {
    'TypeScript': '#3178C6', 'Python': '#FFD343', 'JavaScript': '#E9A23B', 'Kotlin': '#A97BFF',
    'CSS': '#663399', 'C#': '#5BCB7A', 'HTML': '#E2669A', 'Java': '#B07219', 'Dart': '#00B4AB',
}
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def api(url, body=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body else None,
        headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/vnd.github+json'},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def contributions(since: datetime) -> int:
    # contributionsCollection en fazla bir yıllık aralık kabul ediyor; yıl yıl toplanıyor.
    total = 0
    now = datetime.now(timezone.utc)
    start = since
    while start < now:
        end = min(start.replace(year=start.year + 1), now)
        q = {
            'query': 'query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){contributionCalendar{totalContributions}}}}',
            'variables': {'u': USER, 'f': start.isoformat(), 't': end.isoformat()},
        }
        d = api('https://api.github.com/graphql', q)
        total += d['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions']
        start = end
    return total


def w_text(s, size):
    return sum(size * (0.36 if c in 'il.,·|' else 0.62 if c.isupper() else 0.55) for c in s)


def main():
    user = api(f'https://api.github.com/users/{USER}')
    created = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
    repos = api(f'https://api.github.com/users/{USER}/repos?per_page=100&type=owner')
    langs = Counter(r['language'] for r in repos if not r['fork'] and r['language']).most_common(5)
    total = contributions(created)

    stats = [
        (str(total), 'Total contributions', f'{MONTHS[created.month - 1]} {created.year} – present', TEAL),
        (str(user['public_repos']), 'Public repositories', f'on github.com/{USER}', BLUE),
        (str(PORTFOLIO_PROJECTS), 'Projects on portfolio', 'web · mobile · AI · systems', PURPLE),
    ]
    col = W / 3
    st = []
    for i, (num, lab, sub, c) in enumerate(stats):
        cx = col * i + col / 2
        st.append(f'<text x="{cx:.0f}" y="104" text-anchor="middle" font-family="{FONT}" font-size="40" font-weight="700" fill="#FFFFFF">{num}</text>')
        st.append(f'<text x="{cx:.0f}" y="132" text-anchor="middle" font-family="{FONT}" font-size="14" font-weight="600" fill="{c}">{escape(lab)}</text>')
        st.append(f'<text x="{cx:.0f}" y="152" text-anchor="middle" font-family="{FONT}" font-size="11.5" fill="#718BA2">{escape(sub)}</text>')
        if i:
            st.append(f'<line x1="{col*i:.0f}" y1="70" x2="{col*i:.0f}" y2="156" stroke="#ffffff" stroke-opacity=".08"/>')

    toplam = sum(n for _, n in langs) or 1
    bx, bw, by = 60, W - 120, 190
    bar = [f'<clipPath id="bar"><rect x="{bx}" y="{by}" width="{bw}" height="8" rx="4"/></clipPath><g clip-path="url(#bar)">']
    x = bx
    for ad, n in langs:
        ww = bw * n / toplam
        bar.append(f'<rect x="{x:.1f}" y="{by}" width="{ww:.1f}" height="8" fill="{LANG_COLORS.get(ad, "#718BA2")}"/>')
        x += ww
    bar.append('</g>')
    items = [f'{ad} {round(100 * n / toplam)}%' for ad, n in langs]
    widths = [w_text(t, 11.5) + 26 for t in items]
    lx = (W - sum(widths)) / 2
    leg = []
    for (ad, _), t, ww in zip(langs, items, widths):
        leg.append(f'<circle cx="{lx+5:.1f}" cy="{by+30}" r="4" fill="{LANG_COLORS.get(ad, "#718BA2")}"/><text x="{lx+14:.1f}" y="{by+34}" font-family="{FONT}" font-size="11.5" fill="#A9BED2">{escape(t)}</text>')
        lx += ww

    h = 250
    glows = ''.join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" opacity="{o}" filter="url(#b)"><animate attributeName="opacity" values="{o};{o*0.55:.2f};{o}" dur="{d}s" repeatCount="indefinite"/></circle>'
        for (x, y, r, c, o, d) in [(140, 40, 150, TEAL, .35, 8), (720, 230, 150, PURPLE, .35, 9)]
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">
<defs>
  <filter id="b" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="60"/></filter>
  <clipPath id="k"><rect x="1" y="1" width="{W-2}" height="{h-2}" rx="18"/></clipPath>
  <pattern id="d" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#fff" opacity=".045"/></pattern>
</defs>
<g clip-path="url(#k)">
  <rect width="{W}" height="{h}" fill="#061219"/>
  {glows}
  <rect width="{W}" height="{h}" fill="url(#d)"/>
</g>
<rect x="1" y="1" width="{W-2}" height="{h-2}" rx="18" fill="none" stroke="#ffffff" stroke-opacity=".09"/>
<text x="{W/2}" y="44" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="4" fill="{TEAL}" opacity=".85">GITHUB</text>
{''.join(st)}
{''.join(bar)}
{''.join(leg)}
</svg>'''
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'contributions={total} repos={user["public_repos"]} langs={langs}')


if __name__ == '__main__':
    main()
