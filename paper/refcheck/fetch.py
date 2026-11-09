# Crossref records of the DOIs cited in the paper (writes crossref.json next to this file).
import json, urllib.request, urllib.parse, sys, csv, io, os
dois = """10.1109/PIMRC.2018.8580946
10.1109/IWCMC55113.2022.9824571
10.1109/PIMRC54779.2022.9977719
10.1109/ACCESS.2023.3260630
10.1109/GLOBECOM46510.2021.9685348
10.1109/MVT.2019.2959065
10.1109/WCNC57260.2024.10570840
10.1109/ICC.2013.6655592
10.1109/ACCESS.2024.3491500
10.1109/OJCOMS.2024.3373368
10.1109/ACCESS.2016.2642538
10.1109/ACCESS.2019.2937405
10.1109/ACCESS.2021.3067503
10.1038/s41598-026-73269-1
10.1007/978-3-642-12331-3_2
10.1016/j.simpat.2019.101933
10.1049/el:19911328
10.1109/TWC.2012.051512.111532""".split()
rows = list(csv.DictReader(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'survey_2026.csv'), encoding='utf-8-sig')))
for r in rows:
    u = r['doi_or_url']
    if 'doi.org/' in u: dois.append(u.split('doi.org/')[1])
out = {}
for d in dois:
    try:
        m = json.load(urllib.request.urlopen('https://api.crossref.org/works/' + urllib.parse.quote(d), timeout=30))['message']
        out[d] = dict(title=m.get('title'), authors=[(a.get('given',''), a.get('family','')) for a in m.get('author', [])],
                      cont=m.get('container-title'), vol=m.get('volume'), issue=m.get('issue'), page=m.get('page'),
                      art=m.get('article-number'), year=(m.get('published') or m.get('issued'))['date-parts'][0], type=m.get('type'), event=(m.get('event') or {}).get('name'))
    except Exception as e:
        out[d] = dict(error=str(e))
json.dump(out, io.open('crossref.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for d, v in out.items(): print(d, '|', 'ERR '+v['error'] if 'error' in v else (v['title'][0][:80] if v['title'] else '?', v['year'], (v['cont'] or [''])[0][:50], v['vol'], v['page'], v['art']))
