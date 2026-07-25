class Counter:
    def __init__(self, start):
        self.total = start
        self.log = []

    def add(self, amount):
        self.total = self.total + amount
        self.log.append(amount)
        return self.total

def describe(c):
    parts = []
    for a in c.log:
        parts.append(str(a))
    return ', '.join(parts)

c = Counter(10)
c.add(5)
c.add(7)
print('total', c.total)
print('log', describe(c))
n = 0
n += 3
n += 4
print('n', n)
try:
    raise Exception('boom')
except Exception as err:
    print('caught', err)
words = ['alpha', 'beta', 'gamma']
print('len', len(words))
for w in words:
    print('word', w)
text = 'abcdefg'
print('slice', text[2:5])
d = {}
d['x'] = 1
d['y'] = 2
total = 0
for k, v in d.items():
    total += v
print('sum', total)
print('has x', 'x' in d)
if words[0] is None:
    pass
else:
    print('first', words[0])
try:
    if d is None:
        raise ValueError
    print('d exists')
except (ValueError, AttributeError):
    pass
try:
    print('missing', d['missing'])
except Exception:
    pass
print('done')
