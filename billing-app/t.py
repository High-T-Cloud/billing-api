import json

b = [
    {'a': 'b', 'b': 'c'},
    {'a': 'b', 'b': 'c'},
    {'a': 'b', 'b': 'c'},
    {'a': 'b', 'b': 'c'},
]

j = json.dumps(b)
print(j)