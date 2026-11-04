"""Retry only explicit request categories missing from an accepted extraction.

Coverage cues inspect the input, never evaluation labels. Retry generations use
the same model/prompt with fewer request sentences and the full reference plan.
Weather alternatives stay together. This is a bounded heuristic, not proof that
every natural-language condition has been found.
"""
import copy
import json
import re

from .contract import validate_output
from .evidence_guard import normalize, walking_duration_evidence


def category(item):
    return item['type'], item['target']


def request_groups(model_input):
    groups = {}
    for sentence in re.split(r'(?<=[.!?])\s+', model_input['change_request'].strip()):
        text = sentence.casefold()
        keys = []
        lunch = bool(re.search(r'\blunch\b|midday meal', text))
        walking = bool(re.search(r'\bwalk\w*\b|\bon foot\b', text))
        if re.search(r'\bhotel\b', text) and re.search(r'\breturn\w*|\barriv\w*|\bback\b|check.?in|cutoff|deadline', text):
            keys.append(('time', 'hotel_return'))
        if walking_duration_evidence(sentence):
            keys.append(('walking', 'walking_duration'))
        elif walking and re.search(r'\bless\b|\bleast\b|\bminim\w*|\breduc\w*|\bspare\b|unnecessary', text):
            keys.append(('walking', 'walking_amount'))
        if lunch and re.search(r'\bnear\w*|\bclose\b|\baround\b|vicinity|\barea\b', text):
            keys.append(('place', 'lunch'))
        if not lunch and re.search(r'\bvisit\w*|\bkeep\b|\bretain\w*|\bpreserv\w*|\binclude\b|\bdrop\w*|\bremov\w*|\bexclude\b', text):
            if re.search(r'\bmuseum\b|\bgallery\b|\btate\b|\bcourtauld\b', text):
                keys.append(('place', 'place_visit'))
        rain_independent = re.search(r'rain or shine|regardless|any weather|whatever the weather', text)
        if not rain_independent and re.search(r'\brain\w*|\bdry\b|\bwet\b', text):
            if re.search(r'\bkeep\b|\bretain\w*|\breplac\w*|\bswap\w*|\bavoid\w*|\bskip\b|\buse\b|\bpreserv\w*', text):
                keys.append(('weather', '*'))
        for key in keys:
            groups.setdefault(key, []).append(sentence)
    return groups


def present_categories(payload):
    result = {category(item) for item in payload['constraints']}
    if any(item['type'] == 'weather' for item in payload['constraints']):
        result.add(('weather', '*'))
    return result


def complete_extraction(model_input, first_result, extract_chunk, max_retries=2):
    """Retain valid initial conditions; accept only missing categories on retry."""
    initial, normalization = normalize(model_input, first_result['parsed_output'])
    output = copy.deepcopy(first_result)
    output.update(model_parsed_output=first_result['parsed_output'], parsed_output=initial,
                  normalization_audit=normalization, coverage_attempts=[], coverage_unresolved=[])
    if initial is None:
        return output
    groups, tried = request_groups(model_input), set()
    for _ in range(max_retries):
        missing = set(groups) - present_categories(output['parsed_output'])
        if not missing:
            break
        selected = {s for key in missing for s in groups[key]}
        # Retain source order, deduplicating sentences selected for two categories.
        sentences = re.split(r'(?<=[.!?])\s+', model_input['change_request'].strip())
        request = ' '.join(dict.fromkeys(s for s in sentences if s in selected))
        if request in tried or request == model_input['change_request'].strip():
            break  # Repeating identical deterministic input cannot fix an omission.
        tried.add(request)
        result = extract_chunk(model_input | {'change_request': request})
        attempt = {'request': request, 'missing_categories': sorted(missing),
                   'raw_output': result['raw_output'], 'parsed_output': result['parsed_output'],
                   'validation_errors': result['validation_errors'],
                   'model_used': result['model_used'], 'fallback_used': result['fallback_used'],
                   'attempts': result.get('attempts', [])}
        output['coverage_attempts'].append(attempt)
        if result['parsed_output'] is None:
            continue
        additions = [c for c in result['parsed_output']['constraints'] if category(c) in missing
                     or (c['type'] == 'weather' and ('weather', '*') in missing)]
        merged = {'constraints': output['parsed_output']['constraints'] + additions}
        merged, edits = normalize(model_input, merged)
        unique = {json.dumps(c, sort_keys=True, ensure_ascii=False): c for c in merged['constraints']}
        merged['constraints'] = list(unique.values())
        errors = validate_output(merged)
        if errors:
            attempt['merge_errors'] = errors
            continue
        output['parsed_output'] = merged
        output['normalization_audit'].extend(edits)
    output['coverage_unresolved'] = sorted(set(groups) - present_categories(output['parsed_output']))
    return output
