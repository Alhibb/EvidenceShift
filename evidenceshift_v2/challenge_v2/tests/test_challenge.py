import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import challenge as c


def oracle(case,gold):
    docs={d['id']:d['text'] for d in case['documents']}
    return json.dumps({'option_id':gold['option_id'],'status':gold['status'],
                      'justification':'Offline gold-aware fixture; not a model result.',
                      'citations':[{'doc_id':i,'quote':docs[i]} for i in gold['evidence_doc_ids']]})


class ChallengeTests(unittest.TestCase):
    def test_structure_counterfactuals_and_lengths(self):
        self.assertEqual(c.validate()['test_pairs'],12)

    def test_schedules(self):
        self.assertEqual(len(c.jobs('test')),144)
        self.assertEqual(len(c.jobs('dev')),36)
        self.assertEqual(len({j['job_id'] for j in c.jobs('test')}),144)
        self.assertEqual({j['condition'] for j in c.jobs('test')},set(c.CONDITIONS))

    def test_private_labels_never_transmitted(self):
        gold=c.keys()
        for case in c.cases('test')+c.cases('dev'):
            for condition in c.CONDITIONS:
                msg=c.messages(case,condition,'original')
                packet=json.loads(msg[1]['content'])
                self.assertEqual(set(packet),{'question','options','documents'})
                self.assertNotIn(gold[case['id']]['rationale'],msg[1]['content'])
                self.assertNotIn(gold[case['id']]['pair_id'],msg[1]['content'])

    def test_reversal_only_changes_order(self):
        case=c.cases('test')[0]
        a=json.loads(c.messages(case,'baseline','original')[1]['content'])
        b=json.loads(c.messages(case,'baseline','reverse')[1]['content'])
        self.assertEqual(a['documents'],list(reversed(b['documents'])))
        self.assertEqual(a['options'],b['options'])

    def test_all_gold_fixtures(self):
        gold=c.keys()
        for case in c.cases('test')+c.cases('dev'):
            result=c.score(case,gold[case['id']],oracle(case,gold[case['id']]))
            self.assertEqual(result['decision_correct'],1)
            self.assertEqual(result['grounded_decision_proxy'],1)

    def test_incomplete_and_frozen_drift_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            c.client.save_json(root/'manifest.json',{'freeze':{'sha256':c.hashes()},'split':'test','jobs':c.jobs('test'),'origin':'mock'})
            with self.assertRaisesRegex(ValueError,'Incomplete'):c.analyze(root)
            with patch.object(c,'hashes',return_value={'changed':'yes'}):
                with self.assertRaisesRegex(ValueError,'source version'):c.analyze(root)

    def test_pair_metric_requires_both_variants(self):
        gold=c.keys();cases={x['id']:x for x in c.cases('test')}
        broken_pair=next(g['pair_id'] for g in gold.values() if g['split']=='test')
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)
            c.client.save_json(root/'manifest.json',{'freeze':{'sha256':c.hashes()},'split':'test','jobs':c.jobs('test'),'origin':'mock'})
            rows=[]
            for j in c.jobs('test'):
                case=cases[j['case_id']];g=gold[j['case_id']];raw=oracle(case,g)
                if g['pair_id']==broken_pair and g['variant']==0 and j['condition']=='generic_control':raw='malformed'
                rows.append({**j,'raw_output':raw,'transport_error':None,
                             'request_hash':c.client.digest(c.messages(case,j['condition'],j['order']))})
            (root/'responses.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            summary=c.analyze(root)
            self.assertEqual(summary['origin'],'mock')
            self.assertEqual(summary['pair_scores'][broken_pair]['generic_control'],0)
            self.assertEqual(summary['conditions']['evidence_checks']['pair_joint_accuracy'],1)
            self.assertAlmostEqual(summary['contrasts']['primary']['pair_accuracy_difference'],1/12)
            self.assertEqual(summary['contrasts']['secondary']['pair_accuracy_difference'],0)


if __name__=='__main__':unittest.main()
