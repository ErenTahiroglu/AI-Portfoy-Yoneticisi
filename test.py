import re, json
html = open('fintables.html', 'r', encoding='utf-8').read()
m = re.search(r'\"prices\":(\[.*?\])', html)
print('Found prices?', bool(m))
if m:
    prices = json.loads(m.group(1))
    print(prices[:2])
