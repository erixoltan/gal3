def greet(name):
    print('Hello, ' + name)

i = 0
while i < 3:
    greet(str(i))
    i = i + 1

for j in range(4):
    if j % 2 == 0:
        print(j, 'even')
    else:
        print(j, 'odd')

print(6 * 7, 10 - 3, 7 / 2, -5)
print(1 <= 1 and (2 > 3 or 1 != 2))
print(not (2 >= 3))
