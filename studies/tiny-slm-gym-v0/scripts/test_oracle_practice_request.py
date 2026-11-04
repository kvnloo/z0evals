import json
from oracle_practice_request import parse

base = {'ids': ['practice-a'], 'max_tokens': 16, 'arm': 'unedited'}
checks = {'valid': parse(json.dumps(base), {'practice-a'}) == base}
invalid = {
 'unknown_id': {**base, 'ids': ['dev-id']},
 'duplicate_id': {**base, 'ids': ['practice-a', 'practice-a']},
 'empty': {**base, 'ids': []},
 'too_many': {**base, 'ids': ['practice-a'] * 5},
 'bool_tokens': {**base, 'max_tokens': True},
 'excess_tokens': {**base, 'max_tokens': 65},
 'zero_tokens': {**base, 'max_tokens': 0},
 'path_injection': {**base, 'edit_dir': '/etc'},
 'bad_arm': {**base, 'arm': 'sealed'},
}
for name, req in invalid.items():
    try:
        parse(json.dumps(req), {'practice-a'})
        checks[name] = False
    except ValueError:
        checks[name] = True
for name, raw in [('oversize', ' ' * 8193), ('duplicate_key', '{"ids":[],"ids":[]}')]:
    try:
        parse(raw, {'practice-a'})
        checks[name] = False
    except ValueError:
        checks[name] = True
print(json.dumps({'checks': checks, 'passed': sum(checks.values()), 'n': len(checks), 'ci': None}))
assert all(checks.values())
