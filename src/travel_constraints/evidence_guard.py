"""Prospective validation candidate: auditable input-evidence normalization.

This does not change trained weights or add omitted constraints. Raw model
predictions remain unchanged; edits belong only to this separate system version.
No record IDs, family labels, annotations or evaluation scores are consulted.
"""
import copy
import re
import unicodedata


def canonical(text):
    text = unicodedata.normalize('NFKC', str(text)).casefold().replace('&', ' and ')
    return ' '.join(re.findall(r'\w+', text))


def clauses(text):
    return re.split(r'\s*(?:[;,]|\band\b|\bbut\b|\bwhile\b)\s*', text, flags=re.I)


def walking_duration_evidence(text):
    """Do not reuse a museum/lunch duration as a walking restriction."""
    return any(re.search(r'\bwalk\w*\b|\bon foot\b', part, re.I)
               and re.search(r'\b\d+\s*-?\s*(?:minutes?|mins?)\b', part, re.I)
               for part in clauses(text))


def explicit_clock(text):
    matches = list(re.finditer(
        r'(?<![\d:])(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<ampm>[ap]\.?m\.?)?(?!\w|:\d)',
        text, re.I))
    values = []
    for match in matches:
        if match['m'] is None and match['ampm'] is None:
            continue
        hour, minute = int(match['h']), int(match['m'] or 0)
        ampm = (match['ampm'] or '').replace('.', '').lower()
        if minute >= 60 or (ampm and not 1 <= hour <= 12) or (not ampm and hour >= 24):
            continue
        if ampm:
            hour = hour % 12 + (12 if ampm == 'pm' else 0)
        values.append(f'{hour:02d}:{minute:02d}')
    return values[0] if len(values) == 1 else None


def time_operator(sentence):
    text = sentence.casefold()
    if re.search(r'\bexact(?:ly)?\b(?!\s+(?:deadline|cutoff))|\b(precis(?:ely)?|coincide|pinned)\b|no earlier or later', text):
        return '='
    negated_arrival = re.search(
        r"\b(?:do not|don't|must not|mustn't|never|cannot|can't)\s+"
        r'(?:return|arrive|get|be|check\s*in)\b[^.;!?]{0,70}\bbefore\b', text)
    lower = bool(negated_arrival or re.search(
        r'not before|no earlier than|\bor later\b|never sooner|\bearliest\b|'
        r'\b(?:cannot|can not|must not|may not)\s+be\s+earlier\s+than|'
        r'\bfrom\b.*\bonward', text))
    upper = bool(re.search(
        r'\b(?:cutoff|deadline|by|early|latest)\b|no later than|'
        r'\b(?:cannot|can not|must not|may not)\s+be\s+later\s+than|'
        r'\bafter\b[^.;!?]{0,45}\b(?:unacceptable|forbidden|not allowed)\b|'
        r'earlier is acceptable|(?<!not )\bbefore\b', text))
    if lower and upper and not negated_arrival:
        return None
    if lower:
        return '>='
    if upper:
        return '<='
    return None


def walking_scope(sentence):
    text = sentence.casefold()
    daily = bool(re.search(
        r'\b(?:day|daily)\b.*\b(?:total|whole|combined|all|counted)\b|'
        r'\b(?:whole|full|entire) day\b|\b(?:daily|daylong)\b|\b(?:whole|entire) outing\b|'
        r'\ball\b.*\bwalk(?:ing)?\b.*\btoday\b|'
        r'\b(?:total|combined|cumulative)\b.*\b(?:walk|walking|foot)\b|'
        r'\b(?:every|all)\b.*\b(?:walk|walking|foot)\b.*\b(?:together|combined|counted|total)\b|'
        r'\b(?:walk|walking|foot)\b.*\b(?:day|together|combined|total)\b', text))
    segment = bool(re.search(
        r'\b(?:per|each|individual|single|separate|continuous|consecutive|unbroken)\b|'
        r'\bevery\s+(?:walking\s+)?(?:leg|segment|stretch|spell)\b|'
        r'at a (?:stretch|time)|in (?:one|a single) (?:go|stretch)|at once|in a row|'
        r'between (?:(?:any )?two )?(?:breaks|stops|rests)|without (?:a )?(?:break|rest)|'
        r'\bno (?:walking )?(?:leg|segment|stretch)\b', text))
    segment = segment or (not daily and bool(re.search(r'\bwalking\s+(?:legs|segments|stretches)\b', text)))
    if daily and segment:
        return None
    if daily:
        return 'daily_total'
    if segment:
        return 'per_segment'
    return None


def explicit_dry_walk_branch(text):
    """Recognize an explicit dry/otherwise branch, not infer one from a forecast."""
    text = text.casefold()
    if not (re.search(r'\brain\w*\b', text) and re.search(r'\bbook(?:shop)?\s+cafe\b', text)):
        return False
    return bool(re.search(
        r'\bif not\s*[,;:]?\s*(?:keep|retain|leave|preserve)\b[^.;!?]{0,35}\bwalk\b|'
        r'\bif\s+(?:it stays dry|there is no rain|it does not rain)\b[^.;!?]{0,60}\b(?:keep|retain|leave|preserve)\b[^.;!?]{0,35}\bwalk\b',
        text))


def priority(sentence):
    text = sentence.casefold()
    soft = bool(re.search(
        r'if possible|\bprefer\b|\boptional\b|not essential|would welcome|would like|'
        r'not\s+(?:strictly\s+)?(?:required|mandatory|compulsory)|'
        r'if (?:it is |it.s |time |there.s )?(?:manageable|possible|allows|permits|time)', text))
    hard_text = re.sub(r'not\s+(?:strictly\s+)?(?:required|mandatory|compulsory)', '', text)
    hard = bool(re.search(
        r'\bmust\b|\brequir(?:e|es|ed|ing)\b|\b(?:have|has) to\b|\bneed\b|'
        r'\bcompulsory\b|\bmandatory\b|not optional|will not accept|no later than', hard_text))
    imperative = bool(re.search(
        r'^\s*(?:please\s+)?(?:keep|retain|preserve|include|remove|exclude|put|choose|make)\b|'
        r'\b(?:means|then)\s+(?:retain|keep|replace|preserve|use)\b', hard_text))
    if soft:
        return None if hard else 'soft'
    return 'hard' if hard or imperative else None


def normalize(model_input, prediction):
    """Return a separate payload and audit; refuse ambiguous clause assignment."""
    if prediction is None:
        return None, []
    result = copy.deepcopy(prediction)
    request = model_input['change_request']
    # Sentence boundaries keep a deadline's semicolon qualification attached.
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', request) if s.strip()]
    hotel = [s for s in sentences if re.search(r'\bhotel\b', s, re.I)]
    walks = [s for s in sentences if re.search(r'\bwalk(?:ing)?\b|\bon foot\b', s, re.I)]
    duration = [(s, re.findall(r'\b(\d+)\s*-?\s*(?:minutes?|mins?)\b', s, re.I))
                for s in walks if walking_duration_evidence(s)]
    duration = [(s, int(nums[0])) for s, nums in duration if len(nums) == 1]
    request_minutes = {int(n) for n in re.findall(r'\b(\d+)\s*-?\s*(?:minutes?|mins?)\b', request, re.I)}
    audit, accepted = [], []
    for index, item in enumerate(result['constraints']):
        before, evidence, reasons = copy.deepcopy(item), None, []
        if item['type'] == 'time' and item['target'] == 'hotel_return' and len(hotel) == 1:
            hotel_parts = [part for part in clauses(hotel[0]) if re.search(r'\bhotel\b', part, re.I)]
            evidence = hotel_parts[0] if len(hotel_parts) == 1 else None
            clock = explicit_clock(evidence) if evidence else None
            operator = time_operator(evidence) if evidence else None
            if clock is not None:
                item['value'] = clock
                item['needs_clarification'] = False
                reasons.append('single explicit clock in hotel-return sentence')
            if operator is not None:
                item['operator'] = operator
                reasons.append('explicit deadline, exactness or lower-bound wording')
        elif item['type'] == 'walking':
            matching = [(s, n) for s, n in duration if n == item.get('value')]
            selected = matching[0] if len(matching) == 1 else None
            if selected is None and len(duration) == 1 and item.get('value') not in request_minutes:
                selected = duration[0]
            if selected is not None:
                evidence, number = selected
                scope = walking_scope(evidence)
                if item['target'] == 'walking_amount':
                    # A numeric limit has replaced a subjective minimize intent;
                    # use the limit's own priority, not the old intent's label.
                    item['priority'] = priority(evidence) or 'hard'
                # A duration alone does not establish per-leg versus daily scope.
                # Ask for confirmation instead of retaining an unsupported guess.
                item.update(target='walking_duration', operator='<=', value=number,
                            unit='minutes', scope=scope, needs_clarification=scope is None)
                reasons.append('single explicit walking duration and its stated scope')
            # A paraphrase may express minimization without any fixed keyword.
            # Missing keywords are not evidence that a model condition is false.
            # Leave that semantic decision to the model when no duration is given.
        elif item['type'] == 'weather':
            candidates = [s for s in sentences if re.search(r'\brain\w*|\bdry\b|\bwet\b', s, re.I)
                          and re.search(r'\bwalk\b|\bactivity\b|\boutdoor\b', s, re.I)]
            if len(candidates) == 1:
                evidence = candidates[0]
                if (item['target'] == 'outdoor_walk' and item['operator'] == 'keep'
                        and explicit_dry_walk_branch(evidence)):
                    item['condition'] = {'weather': 'rain', 'occurs': False}
                    reasons.append('explicit complementary no-rain branch retains the walk')
        elif item['type'] == 'place' and item['target'] == 'place_visit':
            value = canonical(item.get('value') or '')
            candidates = [s for s in sentences if value and value in canonical(s)]
            if len(candidates) == 1:
                evidence = candidates[0]
            elif not candidates and value:
                # A clear gallery/museum reference can legitimately name an
                # itinerary entity that does not occur literally in the request.
                pronoun_reference = bool(re.search(
                    r'\b(?:the|that|original|scheduled)\s+(?:gallery|museum|visit)\b', request, re.I))
                itinerary_entity = any(value == canonical(stop.get('place', ''))
                                       for stop in model_input.get('reference_itinerary', []))
                if not pronoun_reference and itinerary_entity:
                    audit.append({'index': index, 'action': 'drop', 'before': before,
                                  'reason': 'place name absent from request and no resolvable visit reference',
                                  'evidence': request})
                    continue
        if evidence is not None:
            label = priority(evidence)
            if label is not None and item['target'] != 'walking_amount':
                item['priority'] = label
                reasons.append('explicit requirement or optional-preference wording in assigned sentence')
        if item != before:
            audit.append({'index': index, 'action': 'normalize', 'before': before,
                          'after': copy.deepcopy(item), 'reasons': reasons, 'evidence': evidence})
        accepted.append(item)
    result['constraints'] = accepted
    return result, audit
