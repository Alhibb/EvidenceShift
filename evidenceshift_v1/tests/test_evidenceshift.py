import argparse
import contextlib
import csv
import io
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

import evidenceshift as e


def oracle(case):
    """Test fixture with gold access. NEVER an empirical model response."""
    ids = case['gold']['acceptable_evidence_sets'][0]
    docs = {d['id']: d for d in case['documents']}
    return {'option_id': case['gold']['option_id'], 'status': case['gold']['status'],
            'justification': 'TEST FIXTURE ONLY; not a model finding.',
            'citations': [{'doc_id': i, 'quote': docs[i]['text']} for i in ids]}


class DatasetAndScoring(unittest.TestCase):
    def setUp(self):
        self.case = e.dataset('test')[0]

    def test_all_dataset_constraints(self):
        self.assertEqual(e.validate()['test_cases'], 40)

    def test_rate_limiter_spaces_attempts(self):
        clock = [100.0]
        with patch.object(e.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(e.time, 'sleep', side_effect=lambda n: clock.__setitem__(0, clock[0] + n)):
            limiter = e.RateLimiter(10)
            limiter.acquire(); self.assertEqual(clock[0], 100)
            limiter.acquire(); self.assertEqual(clock[0], 106)
            limiter.acquire(); self.assertEqual(clock[0], 112)

    def test_server_cooldown_spans_jobs(self):
        clock = [100.0]
        cfg = {'base_url': 'http://localhost:1234/v1', 'model': 'test', 'max_attempts': 1}
        opener = unittest.mock.Mock()
        opener.open.side_effect = e.urllib.error.HTTPError('url', 429, 'quota', {'Retry-After': '30'}, io.BytesIO(b'{}'))
        with patch.object(e.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(e.time, 'sleep', side_effect=lambda n: clock.__setitem__(0, clock[0] + n)), patch.object(e.urllib.request, 'build_opener', return_value=opener):
            limiter = e.RateLimiter(10)
            response = e.call_model(cfg, [], limiter)
            self.assertEqual(response['retry_deferred_seconds'], 30)
            limiter.acquire()
            self.assertEqual(clock[0], 130)

    def test_long_cooldown_blocks_resume(self):
        with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
            root = Path(td); config = root/'config.json'; frozen = root/'freeze.json'; out = root/'run'
            e.save_json(config, {'base_url': 'http://localhost:1234/v1', 'model': 'test', 'max_retry_wait_seconds': 120})
            e.freeze(frozen)
            args = argparse.Namespace(config=config, freeze=frozen, split='dev', repeats=1, seed=1, out=out, plan=False)
            failed = {'raw_output': '', 'transport_error': 'HTTP_429', 'attempts': 1, 'retry_deferred_seconds': 600, 'latency_seconds': 0}
            with patch.object(e, 'call_model', return_value=failed) as provider:
                with self.assertRaisesRegex(ValueError, 'long provider cooldown'): e.run(args)
                self.assertEqual(provider.call_count, 1)
            with patch.object(e, 'call_model') as provider:
                with self.assertRaisesRegex(ValueError, 'cooldown still active'): e.run(args)
                provider.assert_not_called()

    def test_retry_after_header_and_google_body(self):
        body = json.dumps({'error': {'details': [{'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '42s'}]}})
        self.assertEqual(e.retry_after_seconds({'Retry-After': '30'}, body), 42)
        self.assertEqual(e.retry_after_seconds({'Retry-After': '80'}, body), 80)
        self.assertEqual(e.retry_after_seconds({'Retry-After': 'invalid'}, 'invalid'), 0)

    def test_long_server_cooldown_does_not_retry_early(self):
        cfg = {'base_url': 'http://localhost:1234/v1', 'model': 'test', 'max_attempts': 3, 'max_retry_wait_seconds': 120}
        opener = unittest.mock.Mock()
        opener.open.side_effect = e.urllib.error.HTTPError('url', 429, 'quota', {'Retry-After': '600'}, io.BytesIO(b'{}'))
        with patch.object(e.urllib.request, 'build_opener', return_value=opener), patch.object(e.time, 'sleep') as sleeper:
            r = e.call_model(cfg, [])
        self.assertEqual(r['attempts'], 1)
        sleeper.assert_not_called()

    def test_all_gold_fixtures_score_correct(self):
        for case in e.dataset('test') + e.dataset('dev'):
            s = e.score(case, json.dumps(oracle(case)))
            self.assertEqual(s['decision_correct'], 1, case['id'])
            self.assertEqual(s['grounded_decision_proxy'], 1, case['id'])

    def test_no_gold_or_category_reaches_model(self):
        for c in e.dataset('test'):
            for condition in e.CONDITIONS:
                msgs = e.messages(c, condition, 'original')
                payload = json.loads(msgs[1]['content'])
                self.assertEqual(set(payload), {'as_of', 'question', 'options', 'documents'})
                self.assertNotIn(c['gold']['rationale'], msgs[1]['content'])

    def test_order_reversal_preserves_every_other_input(self):
        a, b = e.packet(self.case, 'original'), e.packet(self.case, 'reverse')
        self.assertEqual(a['documents'], list(reversed(b['documents'])))
        a.pop('documents'); b.pop('documents')
        self.assertEqual(a, b)

    def test_malformed_output_fails(self):
        for raw in ['', 'null', '[]', '{', '```json\n{}\n```']:
            self.assertEqual(e.score(self.case, raw)['decision_correct'], 0)

    def test_wrong_choice_not_rewarded(self):
        o = oracle(self.case)
        o['option_id'] = next(x['id'] for x in self.case['options'] if x['id'] != o['option_id'])
        self.assertEqual(e.score(self.case, json.dumps(o))['decision_correct'], 0)

    def test_wrong_status_not_rewarded(self):
        o = oracle(self.case)
        o['status'] = 'conflict' if o['status'] != 'conflict' else 'answer'
        self.assertEqual(e.score(self.case, json.dumps(o))['decision_correct'], 0)

    def test_fabricated_quote_not_rewarded(self):
        o = oracle(self.case)
        o['citations'][0]['quote'] = 'Invented quote absent from every source.'
        s = e.score(self.case, json.dumps(o))
        self.assertEqual(s['decision_correct'], 1)
        self.assertEqual(s['grounded_decision_proxy'], 0)

    def test_unknown_document_not_rewarded(self):
        o = oracle(self.case)
        o['citations'][0]['doc_id'] = 'FAKE'
        self.assertEqual(e.score(self.case, json.dumps(o))['grounded_decision_proxy'], 0)

    def test_conflict_requires_both_sources_for_coverage(self):
        c = next(c for c in e.dataset('test') if c['category'] == 'conflict')
        o = oracle(c); o['citations'] = o['citations'][:1]
        self.assertEqual(e.score(c, json.dumps(o))['evidence_set_covered'], 0)

    def test_consistent_alternative_citation_accepted(self):
        c = next(c for c in e.dataset('test') if c['category'] == 'consistent')
        o = oracle(c)
        alternative = c['gold']['acceptable_evidence_sets'][1][0]
        doc = next(d for d in c['documents'] if d['id'] == alternative)
        o['citations'] = [{'doc_id': alternative, 'quote': doc['text']}]
        self.assertEqual(e.score(c, json.dumps(o))['grounded_decision_proxy'], 1)

    def test_schedule_balanced_unique_reproducible(self):
        a = e.make_jobs(e.dataset('test'), 1, 42)
        self.assertEqual(len(a), 160)
        self.assertEqual(len({j['job_id'] for j in a}), 160)
        self.assertEqual(a, e.make_jobs(e.dataset('test'), 1, 42))
        self.assertNotEqual(a, e.make_jobs(e.dataset('test'), 1, 43))

    def test_bootstrap_known_effect(self):
        self.assertEqual(e.cluster_bootstrap([.25] * 10, draws=100), [.25, .25])
        self.assertEqual(e.cluster_bootstrap([0] * 10, draws=100), [0, 0])

    def test_strict_justification_and_extra_fields(self):
        o = oracle(self.case); o['extra'] = 'unexpected'
        self.assertEqual(e.score(self.case, json.dumps(o))['schema_valid'], 0)
        o = oracle(self.case); o['justification'] = 'word ' * 121
        self.assertEqual(e.score(self.case, json.dumps(o))['schema_valid'], 0)

    def test_freeze_detects_drift(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'freeze.json'; e.freeze(p)
            self.assertIn('sha256', e.verify_freeze(p))
            with patch.object(e, 'frozen_files', return_value={'changed': 'hash'}):
                with self.assertRaises(ValueError): e.verify_freeze(p)

    def test_config_rejects_secrets_and_remote_http(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'config.json'
            for cfg in [{'base_url': 'http://example.org/v1', 'model': 'test'},
                        {'base_url': 'https://x:secret@example.org/v1', 'model': 'test'},
                        {'base_url': 'https://example.org/v1', 'model': 'test', 'api_key': 'not-a-real-secret'},
                        {'base_url': 'https://example.org/v1', 'model': 'test', 'request_parameters': {'messages': []}}]:
                e.save_json(p, cfg)
                with self.assertRaises(ValueError): e.load_config(p)

    def test_api_rejection_is_redacted_and_not_retried(self):
        cfg = {'base_url': 'http://localhost:1234/v1', 'model': 'test', 'max_attempts': 3}
        opener = unittest.mock.Mock()
        opener.open.side_effect = e.urllib.error.HTTPError('url', 401, 'secret provider body', {}, None)
        with patch.object(e.urllib.request, 'build_opener', return_value=opener):
            r = e.call_model(cfg, [])
        self.assertEqual(r['transport_error'], 'HTTP_401')
        self.assertEqual(opener.open.call_count, 1)
        self.assertNotIn('secret', json.dumps(r))

    def test_transient_network_failure_retries_bounded(self):
        cfg = {'base_url': 'http://localhost:1234/v1', 'model': 'test', 'max_attempts': 3}
        opener = unittest.mock.Mock()
        opener.open.side_effect = e.urllib.error.URLError('failure')
        with patch.object(e.urllib.request, 'build_opener', return_value=opener), patch.object(e.time, 'sleep'):
            r = e.call_model(cfg, [])
        self.assertEqual(r['attempts'], 3)
        self.assertEqual(opener.open.call_count, 3)


class EndToEnd(unittest.TestCase):
    def test_local_mock_run_resume_analysis_and_review(self):
        lookup = {e.canonical(e.packet(c, order)): c for c in e.dataset('dev')
                  for order in ('original', 'reverse')}
        calls = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                calls.append(body)
                packet = json.loads(body['messages'][1]['content'])
                response = {'id': 'LOCAL-MOCK-NOT-EMPIRICAL', 'model': 'local-test-fixture',
                            'choices': [{'message': {'content': json.dumps(oracle(lookup[e.canonical(packet)]))}, 'finish_reason': 'stop'}],
                            'usage': {'total_tokens': 0}}
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            def log_message(self, *args):
                pass

        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()), patch.object(e.RateLimiter, 'acquire'):
                root = Path(td); config = root / 'config.json'; freeze = root / 'freeze.json'; out = root / 'run'
                e.save_json(config, {'base_url': f'http://127.0.0.1:{server.server_port}/v1', 'model': 'local-test-fixture'})
                e.freeze(freeze)
                args = argparse.Namespace(config=config, freeze=freeze, split='dev', repeats=1, seed=1, out=out, plan=True)
                e.run(args); self.assertEqual(len(calls), 0)
                args.plan = False; e.run(args); self.assertEqual(len(calls), 32)
                e.run(args); self.assertEqual(len(calls), 32)  # resume does not rebill completed jobs
                e.analyze(out)
                summary = json.loads((out / 'summary.json').read_text())
                self.assertEqual(summary['primary_effect']['difference'], 0)
                self.assertEqual(summary['conditions']['baseline']['decision_correct'], 1)
                self.assertEqual(summary['order_invariance_valid_decisions']['baseline'], 1)
                review = root / 'review'; e.export_review(out, review, 1)
                with (review / 'review_blinded.csv').open(newline='') as f:
                    rows = list(csv.DictReader(f))
                self.assertNotIn('condition', rows[0]); self.assertEqual(len(rows), 32)
                with self.assertRaises(ValueError):
                    e.review_summary(out, review / 'review_blinded.csv', review / 'review_private_key.json')
                for row in rows:
                    row['justification_supported'] = '0'; row['no_unsupported_claims'] = '0'
                with (review / 'review_blinded.csv').open('w', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
                e.review_summary(out, review / 'review_blinded.csv', review / 'review_private_key.json')
                self.assertTrue((out / 'human_review_summary.json').exists())
                original = (out / 'responses.jsonl').read_text()
                (out / 'responses.jsonl').write_text('\n'.join(original.splitlines()[:-1]) + '\n')
                with self.assertRaises(ValueError): e.analyze(out)
                (out / 'responses.jsonl').write_text(original)
                args.seed = 2
                with self.assertRaises(ValueError): e.run(args)
                logs = e.read_jsonl(out / 'responses.jsonl'); logs[0]['request_hash'] = 'tampered'
                (out / 'responses.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in logs))
                with self.assertRaises(ValueError): e.load_run(out)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
