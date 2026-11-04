"""Bounded practice-generation request contract. No filesystem paths from requests."""
import json

MAX_REQUEST = 8192


def parse(raw, practice_ids):
    if len(raw.encode('utf-8')) > MAX_REQUEST:
        raise ValueError('request too large')
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('duplicate key')
            out[key] = value
        return out
    request = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(request, dict) or set(request) != {'ids', 'max_tokens', 'arm'}:
        raise ValueError('exact request fields required')
    ids = request['ids']
    if not isinstance(ids, list) or not 1 <= len(ids) <= 4:
        raise ValueError('one to four practice ids required')
    if any(not isinstance(x, str) or x not in practice_ids for x in ids) or len(set(ids)) != len(ids):
        raise ValueError('unique practice ids only')
    tokens = request['max_tokens']
    if type(tokens) is not int or not 1 <= tokens <= 64:
        raise ValueError('token budget must be integer in 1..64')
    if request['arm'] not in ('unedited', 'staged_edit'):
        raise ValueError('invalid arm')
    return request
