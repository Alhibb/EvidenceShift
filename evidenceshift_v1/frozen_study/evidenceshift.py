"""EvidenceShift: dependency-free controlled evidence-use experiments (Python 3.10+)."""
import argparse
import csv
import hashlib
import json
import math
import os
import random
import statistics
import sys
import time
from email.utils import parsedate_to_datetime
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONDITIONS = ('baseline', 'evidence_checks')


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def read_jsonl(path):
    if not Path(path).exists():
        return []
    rows = []
    for i, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f'{path}: invalid JSON on line {i}; preserve the file and repair the interrupted final line before resuming') from exc
    return rows


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def dataset(split):
    return read_jsonl(ROOT / 'data' / f'{split}.jsonl')


def validate():
    all_ids, family_sets = set(), {}
    for split, n in [('test', 40), ('dev', 8)]:
        cases = dataset(split)
        if len(cases) != n:
            raise ValueError(f'{split}: expected {n} cases')
        family_sets[split] = {c['family'] for c in cases}
        for c in cases:
            if c['id'] in all_ids:
                raise ValueError('Duplicate case ID')
            all_ids.add(c['id'])
            assert c['split'] == split
            assert len(c['options']) == 4 and len({o['id'] for o in c['options']}) == 4
            assert len({o['text'] for o in c['options']}) == 4
            assert c['gold']['option_id'] in {o['id'] for o in c['options']}
            assert c['gold']['status'] in {'answer', 'conflict', 'insufficient'}
            doc_ids = {d['id'] for d in c['documents']}
            assert len(doc_ids) == len(c['documents']) == 2
            assert all(d['text'].strip() for d in c['documents'])
            for group in c['gold']['acceptable_evidence_sets']:
                assert group and set(group) <= doc_ids
            expected_status = {'resolved': 'answer', 'consistent': 'answer',
                               'conflict': 'conflict', 'insufficient': 'insufficient'}[c['category']]
            assert c['gold']['status'] == expected_status
        assert Counter(c['category'] for c in cases) == {k: n // 4 for k in ['resolved', 'conflict', 'insufficient', 'consistent']}
        for family in family_sets[split]:
            assert len([c for c in cases if c['family'] == family]) == 4
    assert not family_sets['test'] & family_sets['dev']
    return {'valid': True, 'test_cases': 40, 'dev_cases': 8,
            'test_families': 10, 'human_review': 'pending; structural validation is not independent annotation'}


def frozen_files():
    paths = [ROOT / 'evidenceshift.py', ROOT / 'make_dataset.py', ROOT / 'docs' / 'PROTOCOL.md']
    paths += sorted((ROOT / 'data').glob('*.jsonl')) + sorted((ROOT / 'prompts').glob('*.txt'))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def freeze(path):
    validate()
    if Path(path).exists():
        raise ValueError('Freeze file already exists; preserve it and use a new filename for a new version.')
    save_json(path, {'created_utc': datetime.now(timezone.utc).isoformat(), 'sha256': frozen_files(),
                     'status': 'Local protocol freeze; not a public preregistration or human review approval.'})


def verify_freeze(path):
    f = json.loads(Path(path).read_text(encoding='utf-8'))
    if f['sha256'] != frozen_files():
        raise ValueError('Frozen files changed. Restore them or freeze a new experiment version.')
    return f


def packet(case, order):
    docs = list(case['documents'])
    if order == 'reverse':
        docs.reverse()
    # Deliberate allowlist: no labels, family/category, gold, or rationale reach the model.
    return {'as_of': case['as_of'], 'question': case['question'],
            'options': case['options'], 'documents': docs}


def messages(case, condition, order):
    instruction = (ROOT / 'prompts' / f'{condition}.txt').read_text(encoding='utf-8')
    formatting = (ROOT / 'prompts' / 'format.txt').read_text(encoding='utf-8')
    return [{'role': 'system', 'content': instruction + '\n' + formatting},
            {'role': 'user', 'content': canonical(packet(case, order))}]


def parse_output(text, case):
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return None, 'not_json'
    if not isinstance(obj, dict) or set(obj) != {'option_id', 'status', 'justification', 'citations'}:
        return None, 'wrong_fields'
    if obj['option_id'] not in [o['id'] for o in case['options']]:
        return None, 'invalid_option'
    if obj['status'] not in ('answer', 'conflict', 'insufficient'):
        return None, 'invalid_status'
    if not isinstance(obj['justification'], str) or not obj['justification'].strip() or len(obj['justification'].split()) > 120:
        return None, 'invalid_justification'
    cites = obj['citations']
    if not isinstance(cites, list) or not 1 <= len(cites) <= 4:
        return None, 'invalid_citations'
    for cite in cites:
        if not isinstance(cite, dict) or set(cite) != {'doc_id', 'quote'}:
            return None, 'invalid_citation_fields'
        if not all(isinstance(cite[k], str) and cite[k].strip() for k in cite):
            return None, 'empty_citation'
    return obj, None


def score(case, raw):
    obj, error = parse_output(raw, case)
    if obj is None:
        return {'schema_valid': 0, 'decision_correct': 0, 'quote_valid_fraction': 0,
                'evidence_set_covered': 0, 'grounded_decision_proxy': 0, 'parse_error': error}
    docs = {d['id']: d['text'] for d in case['documents']}
    valid = [c['doc_id'] in docs and c['quote'] in docs[c['doc_id']] for c in obj['citations']]
    supported_ids = {c['doc_id'] for c, good in zip(obj['citations'], valid) if good}
    coverage = any(set(s) <= supported_ids for s in case['gold']['acceptable_evidence_sets'])
    correct = obj['option_id'] == case['gold']['option_id'] and obj['status'] == case['gold']['status']
    return {'schema_valid': 1, 'decision_correct': int(correct),
            'quote_valid_fraction': sum(valid) / len(valid), 'evidence_set_covered': int(coverage),
            'grounded_decision_proxy': int(correct and all(valid) and coverage), 'parse_error': None}


def make_jobs(cases, repeats, seed):
    jobs = []
    for c in cases:
        for rep in range(repeats):
            for order in ['original', 'reverse']:
                for condition in CONDITIONS:
                    j = {'case_id': c['id'], 'repeat': rep, 'order': order, 'condition': condition}
                    j['job_id'] = digest(j)[:20]
                    jobs.append(j)
    random.Random(seed).shuffle(jobs)
    return jobs


def load_config(path):
    cfg = json.loads(Path(path).read_text(encoding='utf-8'))
    allowed = {'base_url', 'model', 'api_key_env', 'request_parameters', 'timeout_seconds', 'max_attempts',
               'requests_per_minute', 'backoff_initial_seconds', 'max_retry_wait_seconds', 'max_consecutive_errors'}
    if set(cfg) - allowed:
        raise ValueError('Unknown config fields; credentials must be supplied via an environment variable.')
    url = urllib.parse.urlsplit(cfg['base_url'])
    local = url.hostname in ('localhost', '127.0.0.1', '::1')
    if url.username or url.password or url.query or url.fragment or not url.hostname:
        raise ValueError('Base URL must not contain credentials, query parameters, or fragments.')
    if url.scheme != 'https' and not (url.scheme == 'http' and local):
        raise ValueError('Use HTTPS, except for a local model server.')
    if not isinstance(cfg.get('model'), str) or not cfg['model'] or cfg['model'].startswith('REPLACE_'):
        raise ValueError('Set a real available model ID in the config.')
    params = cfg.get('request_parameters', {})
    if not isinstance(params, dict) or set(params) - {'temperature', 'top_p', 'max_tokens', 'max_completion_tokens', 'seed', 'response_format', 'reasoning_effort'}:
        raise ValueError('Unsupported request parameters; do not override model/messages/stream.')
    if not 1 <= cfg.get('max_attempts', 3) <= 5 or not 1 <= cfg.get('timeout_seconds', 60) <= 300:
        raise ValueError('Use 1–5 attempts and 1–300 second timeout.')
    for field, default, low, high in [('requests_per_minute', 10, 1, 120),
                                      ('backoff_initial_seconds', 5, 1, 60),
                                      ('max_retry_wait_seconds', 120, 1, 600),
                                      ('max_consecutive_errors', 3, 1, 10)]:
        value = cfg.get(field, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{field} must be finite and between {low} and {high}.')
    return cfg


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def sleep_in_chunks(seconds):
    while seconds > 0:
        chunk = min(seconds, 30)
        time.sleep(chunk)
        seconds -= chunk


class RateLimiter:
    """Single-process start-to-start pacing; retries consume the same quota."""
    def __init__(self, rpm):
        self.interval = 60.0 / rpm
        self.next_start = 0.0

    def acquire(self):
        sleep_in_chunks(max(0, self.next_start - time.monotonic()))
        self.next_start = time.monotonic() + self.interval


def retry_after_seconds(headers, body):
    delays = [0.0]
    raw = headers.get('Retry-After', '') if headers else ''
    try:
        delays.append(float(raw))
    except (ValueError, TypeError):
        try:
            delays.append(parsedate_to_datetime(raw).timestamp() - time.time())
        except (ValueError, TypeError, OverflowError):
            pass
    try:
        details = json.loads(body).get('error', {}).get('details', [])
        for detail in details:
            if detail.get('@type', '').endswith('google.rpc.RetryInfo'):
                value = detail.get('retryDelay', '')
                if isinstance(value, str) and value.endswith('s'):
                    delays.append(float(value[:-1]))
    except (ValueError, TypeError, AttributeError):
        pass
    return max(v for v in delays if math.isfinite(v))


def call_model(cfg, msgs, limiter=None):
    body = {'model': cfg['model'], 'messages': msgs, **cfg.get('request_parameters', {})}
    key = os.environ.get(cfg.get('api_key_env', 'EVIDENCESHIFT_API_KEY'), '')
    local = urllib.parse.urlsplit(cfg['base_url']).hostname in ('localhost', '127.0.0.1', '::1')
    if not key and not local:
        raise ValueError('API key environment variable is empty. Do not paste secrets into source or config.')
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    request = urllib.request.Request(cfg['base_url'].rstrip('/') + '/chat/completions',
                                     data=canonical(body).encode(), headers=headers, method='POST')
    opener = urllib.request.build_opener(NoRedirect())
    start, attempts = time.monotonic(), cfg.get('max_attempts', 3)
    limiter = limiter or RateLimiter(cfg.get('requests_per_minute', 10))
    for attempt in range(attempts):
        limiter.acquire()
        requested_delay = 0
        try:
            with opener.open(request, timeout=cfg.get('timeout_seconds', 60)) as response:
                result = json.load(response)
            choice = result['choices'][0]
            content = choice['message'].get('content')
            return {'raw_output': content if isinstance(content, str) else '',
                    'served_model': result.get('model'), 'response_id': result.get('id'),
                    'system_fingerprint': result.get('system_fingerprint'), 'usage': result.get('usage'),
                    'finish_reason': choice.get('finish_reason'), 'attempts': attempt + 1,
                    'latency_seconds': time.monotonic() - start, 'transport_error': None}
        except urllib.error.HTTPError as exc:
            error = f'HTTP_{exc.code}'
            retryable = exc.code == 429 or 500 <= exc.code < 600
            requested_delay = retry_after_seconds(exc.headers, exc.read(65536))
        except (urllib.error.URLError, TimeoutError, OSError):
            error, retryable = 'network_error', True
        except (KeyError, IndexError, TypeError, ValueError):
            error, retryable = 'invalid_provider_response', False
        if not retryable or attempt + 1 == attempts:
            break
        delay = max(requested_delay, cfg.get('backoff_initial_seconds', 5) * 2 ** attempt + random.uniform(0, 1))
        if delay > cfg.get('max_retry_wait_seconds', 120):
            break  # Never retry earlier than a server-mandated long cooldown.
        sleep_in_chunks(delay)
    # Provider response bodies are deliberately not logged: they may echo credentials.
    return {'raw_output': '', 'transport_error': error, 'attempts': attempt + 1,
            'latency_seconds': time.monotonic() - start}


def run(args):
    validate()
    f = verify_freeze(args.freeze)
    cfg = load_config(args.config)
    cases = dataset(args.split)
    by_id = {c['id']: c for c in cases}
    jobs = make_jobs(cases, args.repeats, args.seed)
    if args.plan:
        print(json.dumps({'scheduled_calls': len(jobs), 'max_http_attempts': len(jobs) * cfg.get('max_attempts', 3),
                          'model': cfg['model'], 'split': args.split,
                          'note': 'No requests sent. Billing depends on provider, tokens and retries.'}, indent=2))
        return
    local = urllib.parse.urlsplit(cfg['base_url']).hostname in ('localhost', '127.0.0.1', '::1')
    if not local and not os.environ.get(cfg.get('api_key_env', 'EVIDENCESHIFT_API_KEY')):
        raise ValueError('No API key configured; no experiment requests sent.')
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / 'manifest.json'
    specification = {'freeze': f, 'config': cfg, 'split': args.split, 'seed': args.seed,
                     'repeats': args.repeats, 'jobs': jobs, 'protocol_version': '1.0'}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['specification'] != specification:
            raise ValueError('Run directory belongs to a different experiment; use a new directory.')
    else:
        if (out / 'responses.jsonl').exists():
            raise ValueError('Responses exist without a manifest; preserve them and use a fresh run directory.')
        save_json(manifest_path, {'created_utc': datetime.now(timezone.utc).isoformat(),
                                 'specification': specification, 'python': sys.version})
    rows = read_jsonl(out / 'responses.jsonl')
    limiter = RateLimiter(cfg.get('requests_per_minute', 10))
    consecutive_errors = 0
    done = {r['job_id'] for r in rows}
    if len(done) != len(rows) or not done <= {j['job_id'] for j in jobs}:
        raise ValueError('Duplicate or unknown logged job IDs.')
    with (out / 'responses.jsonl').open('a', encoding='utf-8') as stream:
        for job in jobs:
            if job['job_id'] in done:
                continue
            msgs = messages(by_id[job['case_id']], job['condition'], job['order'])
            response = call_model(cfg, msgs, limiter)
            record = {**job, **response, 'request_hash': digest(msgs),
                      'recorded_utc': datetime.now(timezone.utc).isoformat()}
            stream.write(json.dumps(record, ensure_ascii=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
            done.add(job['job_id'])
            consecutive_errors = consecutive_errors + 1 if response.get('transport_error') else 0
            print(f'{len(done)}/{len(jobs)} {job["job_id"]} {response.get("transport_error") or "received"}', flush=True)
            if response.get('transport_error') in {'HTTP_400', 'HTTP_401', 'HTTP_403', 'HTTP_404'}:
                raise ValueError('Provider rejected the request. Fix configuration and start a NEW run directory; failure was retained.')
            if consecutive_errors >= cfg.get('max_consecutive_errors', 3):
                raise ValueError('Paused after consecutive provider/network failures. Preserve this run and investigate quota or connectivity before resuming.')


def load_run(path, allow_partial=False):
    out = Path(path)
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    spec = manifest['specification']
    if spec['freeze']['sha256'] != frozen_files():
        raise ValueError('Source/data differs from run freeze; analyze using the original version.')
    rows = read_jsonl(out / 'responses.jsonl')
    jobs = {j['job_id']: j for j in spec['jobs']}
    cases = {c['id']: c for c in dataset(spec['split'])}
    if len({r['job_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate response IDs.')
    for r in rows:
        if r['job_id'] not in jobs or any(r.get(k) != v for k, v in jobs[r['job_id']].items()):
            raise ValueError('Response metadata does not match planned job.')
        expected = digest(messages(cases[r['case_id']], r['condition'], r['order']))
        if r.get('request_hash') != expected:
            raise ValueError('Request hash mismatch.')
    if not allow_partial and len(rows) != len(jobs):
        raise ValueError(f'Incomplete run ({len(rows)}/{len(jobs)}). Resume before analysis; do not silently drop missing responses.')
    return manifest, rows, cases


def mean(values):
    values = list(values)
    return statistics.mean(values) if values else None


def cluster_bootstrap(differences, draws=10000, seed=711):
    vals = list(differences)
    rng = random.Random(seed)
    estimates = sorted(mean(rng.choices(vals, k=len(vals))) for _ in range(draws))
    return [estimates[int(draws * .025)], estimates[min(draws - 1, int(draws * .975))]]


def analyze(path):
    manifest, rows, cases = load_run(path)
    scored = [{**r, **score(cases[r['case_id']], r['raw_output']),
               'family': cases[r['case_id']]['family'], 'category': cases[r['case_id']]['category']} for r in rows]
    metrics = ['decision_correct', 'schema_valid', 'quote_valid_fraction', 'evidence_set_covered', 'grounded_decision_proxy']
    result = {'status': 'EMPIRICAL MODEL RUN; assess review and provider errors before making claims',
              'model': manifest['specification']['config']['model'], 'split': manifest['specification']['split'],
              'scheduled_responses': len(rows), 'cases': len(cases), 'families': len({c['family'] for c in cases.values()}),
              'transport_errors': sum(bool(r.get('transport_error')) for r in rows),
              'conditions': {}, 'categories': {}, 'served_models': dict(Counter(str(r.get('served_model')) for r in rows)),
              'finish_reasons': dict(Counter(str(r.get('finish_reason')) for r in rows)),
              'warning': 'Quote matching and source coverage are mechanical proxies, not semantic entailment. Synthetic pilot; human review pending.'}
    for condition in CONDITIONS:
        subset = [r for r in scored if r['condition'] == condition]
        result['conditions'][condition] = {m: mean(r[m] for r in subset) for m in metrics}
        result['conditions'][condition]['transport_errors'] = sum(bool(r.get('transport_error')) for r in subset)
        result['conditions'][condition]['mean_latency_seconds'] = mean(r.get('latency_seconds', 0) for r in subset)
        result['conditions'][condition]['reported_total_tokens'] = sum((r.get('usage') or {}).get('total_tokens', 0) for r in subset)
    for category in sorted({r['category'] for r in scored}):
        result['categories'][category] = {c: mean(r['decision_correct'] for r in scored if r['category'] == category and r['condition'] == c) for c in CONDITIONS}
    by_family = defaultdict(lambda: defaultdict(list))
    for r in scored:
        by_family[r['family']][r['condition']].append(r['decision_correct'])
    diffs = {f: mean(v['evidence_checks']) - mean(v['baseline']) for f, v in by_family.items()}
    result['primary_effect'] = {'metric': 'evidence_checks minus baseline decision accuracy',
                                'difference': mean(diffs.values()), 'family_differences': diffs,
                                'paired_family_bootstrap_95_percentile_interval': cluster_bootstrap(diffs.values()),
                                'bootstrap_draws': 10000, 'bootstrap_seed': 711,
                                'caution': 'Only 10 test families (2 dev); templated families are still related. Exploratory interval, not population evidence.'}
    invariance = {}
    for condition in CONDITIONS:
        groups = defaultdict(dict)
        for r in scored:
            if r['condition'] == condition:
                parsed, _ = parse_output(r['raw_output'], cases[r['case_id']])
                groups[(r['case_id'], r['repeat'])][r['order']] = None if parsed is None else (parsed['option_id'], parsed['status'])
        invariance[condition] = mean(v['original'] is not None and v['original'] == v['reverse'] for v in groups.values())
    result['order_invariance_valid_decisions'] = invariance
    out = Path(path)
    save_json(out / 'summary.json', result)
    fields = ['job_id', 'case_id', 'family', 'category', 'condition', 'order', 'repeat'] + metrics + ['parse_error', 'transport_error']
    with (out / 'scores.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(scored)
    lines = ['# EvidenceShift run summary', '', '**Exploratory synthetic pilot. Human semantic review required.**', '',
             f'Model: {result["model"]}; split: {result["split"]}; transport failures: {result["transport_errors"]}.', '',
             '| Metric | Baseline | Evidence checks |', '|---|---:|---:|']
    for m in metrics:
        lines.append(f'| {m} | {result["conditions"]["baseline"][m]:.3f} | {result["conditions"]["evidence_checks"][m]:.3f} |')
    lines += ['', f'Paired family mean difference: {result["primary_effect"]["difference"]:.3f}.',
              f'Exploratory bootstrap interval: {result["primary_effect"]["paired_family_bootstrap_95_percentile_interval"]}.',
              '', 'Do not count document orders or repeated calls as independent test cases. See summary.json for category and order-sensitivity results.']
    (out / 'summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


def export_review(path, destination, seed):
    _, rows, cases = load_run(path)
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError('Review destination must be empty to avoid overwriting annotations.')
    random.Random(seed).shuffle(rows)
    private, review = {}, []
    for i, r in enumerate(rows):
        token = f'R{i+1:04}'
        private[token] = r['job_id']
        review.append({'review_id': token, 'question': cases[r['case_id']]['question'],
                       'packet': canonical(packet(cases[r['case_id']], r['order'])), 'response': r['raw_output'],
                       'justification_supported': '', 'no_unsupported_claims': '', 'notes': ''})
    with (out / 'review_blinded.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(review[0]))
        w.writeheader()
        w.writerows(review)
    save_json(out / 'review_private_key.json', private)
    print('Created review_blinded.csv and review_private_key.json. Share only the blinded CSV with reviewers.')


def review_summary(path, csv_path, key_path):
    _, rows, cases = load_run(path)
    key = json.loads(Path(key_path).read_text(encoding='utf-8'))
    by_job = {r['job_id']: r for r in rows}
    if set(key.values()) != set(by_job) or len(key) != len(rows):
        raise ValueError('Review key does not match this run.')
    with Path(csv_path).open(newline='', encoding='utf-8-sig') as f:
        reviewed = list(csv.DictReader(f))
    if len(reviewed) != len(key) or {r['review_id'] for r in reviewed} != set(key):
        raise ValueError('Review IDs missing, duplicated, or unknown.')
    totals = defaultdict(list)
    for r in reviewed:
        job = by_job[key[r['review_id']]]
        for field in ['justification_supported', 'no_unsupported_claims']:
            if r[field] not in ('0', '1'):
                raise ValueError('Complete all review scores with 0 or 1; blanks are not zero.')
            totals[(job['condition'], field)].append(int(r[field]))
    result = {c: {field: mean(totals[(c, field)]) for field in ['justification_supported', 'no_unsupported_claims']} for c in CONDITIONS}
    save_json(Path(path) / 'human_review_summary.json', result)
    print(json.dumps(result, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('validate')
    f = sub.add_parser('freeze'); f.add_argument('--out', default='freeze.json')
    r = sub.add_parser('run')
    r.add_argument('--config', required=True); r.add_argument('--freeze', default='freeze.json')
    r.add_argument('--out', default='runs/test'); r.add_argument('--split', choices=['test', 'dev'], default='test')
    r.add_argument('--repeats', type=int, default=1); r.add_argument('--seed', type=int, default=20261114)
    r.add_argument('--plan', action='store_true')
    a = sub.add_parser('analyze'); a.add_argument('run_dir')
    e = sub.add_parser('export-review'); e.add_argument('run_dir'); e.add_argument('--out', required=True); e.add_argument('--seed', type=int, default=919)
    h = sub.add_parser('review-summary'); h.add_argument('run_dir'); h.add_argument('--csv', required=True); h.add_argument('--key', required=True)
    args = p.parse_args()
    try:
        if args.command == 'validate': print(json.dumps(validate(), indent=2))
        elif args.command == 'freeze': freeze(args.out)
        elif args.command == 'run':
            if not 1 <= args.repeats <= 20: raise ValueError('Repeats must be between 1 and 20.')
            run(args)
        elif args.command == 'analyze': analyze(args.run_dir)
        elif args.command == 'export-review': export_review(args.run_dir, args.out, args.seed)
        elif args.command == 'review-summary': review_summary(args.run_dir, args.csv, args.key)
    except (ValueError, AssertionError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
