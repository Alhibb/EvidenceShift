"""Rebuild the fictional pilot; do not regenerate after freezing an experiment."""
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FAMILIES = [
    ('school', 'Koru Learning Centre', 'the January 2027 term resumption date', '12 January 2027', '19 January 2027'),
    ('delivery', 'Nera Dispatch', 'the Zone R parcel collection point', 'Cedar Depot', 'Maple Depot'),
    ('library', 'Tavi Reading Room', 'the weekday closing time', '17:00', '18:30'),
    ('workshop', 'Luma Makers Club', 'the Saturday workshop room', 'Room 14', 'Room 22'),
    ('membership', 'Sora Community Club', 'the annual adult membership fee', 'NGN 12000', 'NGN 15000'),
    ('booking', 'Pela Studios', 'the maximum booking duration', '2 hours', '3 hours'),
    ('support', 'Vela Helpdesk', 'the support contact email', 'help@vela.example', 'care@vela.example'),
    ('transport', 'Daro Shuttle', 'the Route Q departure time', '07:15', '07:45'),
    ('equipment', 'Miro Tool Library', 'the standard drill borrowing period', '3 days', '5 days'),
    ('venue', 'Rena Arts Hall', 'the small hall seating limit', '60 people', '80 people'),
]
DEV = [
    ('garden', 'Telu Garden', 'the visitor gate opening time', '08:00', '09:00'),
    ('museum', 'Nilo Museum', 'the guided tour meeting point', 'North Lobby', 'East Lobby'),
]


def make_case(family, index, category, split):
    key, org, attribute, a, b = family
    case_id = hashlib.sha256(f'{split}:{key}:{category}'.encode()).hexdigest()[:12]
    rng = random.Random(case_id)
    query_date = '2027-01-10'
    old = f'For {org}, {attribute} is {a}.'
    new = f'For {org}, {attribute} is {b}.'
    d1 = {'publisher': f'{org} operations office', 'published': '2027-01-02', 'text': old}
    d2 = {'publisher': f'{org} operations office', 'published': '2027-01-08', 'text': new}
    if category == 'resolved':
        mode = index % 5
        if mode == 0:
            d1['text'] += ' This notice is effective from 2 January 2027.'
            d2['text'] += ' Approved correction: this replaces the 2 January notice, effective immediately.'
            target, rationale, support = b, 'An approved immediate correction supersedes the earlier notice.', [1]
            mechanism = 'explicit_supersession'
        elif mode == 1:
            d1['text'] += ' This rule is approved and remains in force until 31 January 2027.'
            d2['text'] += ' Approved change effective 1 February 2027. The current rule remains in force until then.'
            target, rationale, support = a, 'The approved change has not yet taken effect on the query date.', [0, 1]
            mechanism = 'future_effective_date'
        elif mode == 2:
            d1['text'] += ' This is the current approved rule, effective 2 January 2027.'
            d2['text'] += ' DRAFT FOR DISCUSSION ONLY. Not approved; does not change the current rule.'
            target, rationale, support = a, 'A newer draft cannot replace an approved current rule.', [0, 1]
            mechanism = 'draft_authority'
        elif mode == 3:
            d1['text'] += ' This current approved notice replaces all notices dated before 2 January 2027.'
            d2['text'] += ' Archive reproduction of a notice originally issued 1 December 2026. The upload date is not an effective date.'
            target, rationale, support = a, 'A recent archive upload is an old notice, already superseded.', [0, 1]
            mechanism = 'archive_republication'
        else:
            d1['publisher'] = f'Unofficial {org} fan forum'
            d1['published'] = '2027-01-09'
            d1['text'] += ' A member speculates that this might be the new rule; no official confirmation is available.'
            d2['text'] += ' Official approved rule, effective 8 January 2027. No subsequent approved amendment exists in this packet.'
            target, rationale, support = b, 'An unconfirmed newer forum claim does not supersede an approved rule.', [1]
            mechanism = 'unofficial_newer_claim'
        status = 'answer'
    elif category == 'conflict':
        d1['published'] = d2['published'] = '2027-01-08'
        d1['text'] += ' Approved notice effective 8 January 2027; document version is unspecified.'
        d2['text'] += ' Approved notice effective 8 January 2027; document version is unspecified.'
        target = 'The supplied evidence conflicts and does not establish which value applies.'
        status, support = 'conflict', [0, 1]
        rationale = 'Equally authoritative, simultaneously effective notices disagree with no supersession rule.'
        mechanism = 'equal_authority_conflict'
    elif category == 'insufficient':
        d1['text'] = f'{org} has not yet published {attribute} for the requested service. A decision is pending.'
        d2['text'] = f'A different organisation, {org} Annex, lists {attribute} as {b}. The Annex is separately operated; its rules do not apply to {org}.'
        target = 'The supplied evidence is insufficient to determine the requested value.'
        status, support = 'insufficient', [0]
        rationale = 'The target value is unpublished; the other entity cannot establish it.'
        mechanism = 'missing_target_with_scope_distractor'
    else:
        d1['text'] += ' Approved rule effective from 2 January 2027.'
        d2['text'] = old + ' Operations confirmation: this rule is still in effect on 10 January 2027.'
        target, status, support = a, 'answer', [0]
        rationale = 'Both current documents agree on the same value.'
        mechanism = 'consistent_control'
    values = [a, b, 'The supplied evidence conflicts and does not establish which value applies.',
              'The supplied evidence is insufficient to determine the requested value.']
    rng.shuffle(values)
    options = [{'id': f'O{i+1}', 'text': v} for i, v in enumerate(values)]
    doc_ids = rng.sample(['D1', 'D2', 'D3', 'D4', 'D5', 'D6'], 2)
    docs = [dict(d, id=doc_ids[i]) for i, d in enumerate([d1, d2])]
    acceptable = [[doc_ids[i] for i in support]]
    if category == 'consistent':
        acceptable.append([doc_ids[1]])
    rng.shuffle(docs)
    return {'id': case_id, 'split': split, 'family': key, 'category': category,
            'mechanism': mechanism, 'as_of': query_date,
            'question': f'As of {query_date}, what is {attribute} for {org}? Use only this fictional document packet.',
            'options': options, 'documents': docs,
            'gold': {'option_id': next(o['id'] for o in options if o['text'] == target),
                     'status': status, 'acceptable_evidence_sets': acceptable, 'rationale': rationale},
            'provenance': 'AI-assisted fictional construction; no real policy or personal data; independent human review pending'}


def main():
    for split, families in [('test', FAMILIES), ('dev', DEV)]:
        cases = [make_case(f, i, c, split) for i, f in enumerate(families)
                 for c in ['resolved', 'conflict', 'insufficient', 'consistent']]
        random.Random(20261114).shuffle(cases)
        (ROOT / 'data' / f'{split}.jsonl').write_text(
            ''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in cases), encoding='utf-8')
    print('Wrote 40 test cases and 8 development cases. Human review remains required.')


if __name__ == '__main__':
    main()
