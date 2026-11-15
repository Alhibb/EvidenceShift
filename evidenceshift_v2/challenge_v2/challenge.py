"""Three-arm challenge study. All commands except run are offline."""
import argparse
import importlib.util
import json
import os
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('evidenceshift_client', ROOT.parent/'evidenceshift.py')
client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
CONDITIONS=('baseline','generic_control','evidence_checks')


def cases(split):return client.read_jsonl(ROOT/'data'/f'{split}.jsonl')
def keys():return {k['id']:k for k in client.read_jsonl(ROOT/'data'/'answer_key.jsonl')}


def validate():
    gold=keys();seen=set();pairs=defaultdict(list)
    for split,n in [('dev',6),('test',24)]:
        items=cases(split);assert len(items)==n
        for c in items:
            assert c['id'] not in seen;seen.add(c['id'])
            assert set(c)=={'id','question','options','documents'}
            g=gold[c['id']];assert g['split']==split
            assert g['option_id'] in {o['id'] for o in c['options']}
            assert len({o['id'] for o in c['options']})==4
            assert len({o['text'] for o in c['options']})==4
            assert len(c['documents'])==4 and len({d['id'] for d in c['documents']})==4
            assert set(g['evidence_doc_ids']) <= {d['id'] for d in c['documents']}
            assert g['status'] in ('answer','conflict','insufficient')
            pairs[g['pair_id']].append(c)
    assert seen==set(gold)
    for pair in pairs.values():
        assert len(pair)==2
        a,b=sorted(pair,key=lambda c:gold[c['id']]['variant'])
        assert a['question']==b['question'] and a['options']==b['options']
        assert gold[a['id']]['option_id']!=gold[b['id']]['option_id']
        assert gold[a['id']]['split']==gold[b['id']]['split']
        da,db=a['documents'],b['documents']
        assert sum(x!=y for x,y in zip(da,db))==1
        for x,y in zip(da,db):
            assert {k:v for k,v in x.items() if k!='text'}=={k:v for k,v in y.items() if k!='text'}
    counts={c:len((ROOT/'prompts'/f'{c}.txt').read_text().split()) for c in CONDITIONS}
    assert counts['generic_control']==counts['evidence_checks']
    return {'test_cases':24,'test_pairs':12,'dev_cases':6,'dev_pairs':3,'instruction_word_counts':counts,
            'test_status_counts':dict(Counter(g['status'] for g in gold.values() if g['split']=='test')),
            'review_status':'Independent human review pending; structural checks passed.'}


def hashes():
    paths=[ROOT/'challenge.py',ROOT/'build_dataset.py',ROOT/'PROTOCOL.md',ROOT/'REVIEW_RUBRIC.md',
           ROOT.parent/'evidenceshift.py',ROOT.parent/'config.gemini.json']
    paths+=sorted((ROOT/'data').glob('*.jsonl'))+sorted((ROOT/'prompts').glob('*.txt'))
    import hashlib
    return {os.path.relpath(p,ROOT):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def freeze(path):
    validate()
    if Path(path).exists():raise ValueError('Preserve existing freezes; choose a new path.')
    client.save_json(path,{'created_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashes(),
                          'status':'Candidate version; not publicly preregistered or human-approved.'})


def messages(c,condition,order):
    docs=c['documents'] if order=='original' else list(reversed(c['documents']))
    packet={'question':c['question'],'options':c['options'],'documents':docs}
    text=(ROOT/'prompts'/f'{condition}.txt').read_text()+'\n'+(ROOT/'prompts'/'format.txt').read_text()
    return [{'role':'system','content':text},{'role':'user','content':client.canonical(packet)}]


def jobs(split):
    result=[]
    for c in cases(split):
        for order in ('original','reverse'):
            for condition in CONDITIONS:
                row={'case_id':c['id'],'order':order,'condition':condition}
                row['job_id']=client.digest(row)[:20];result.append(row)
    random.Random(20261115).shuffle(result)
    return result


def score(c,g,raw):
    adapted=dict(c,gold={'option_id':g['option_id'],'status':g['status'],
                         'acceptable_evidence_sets':[g['evidence_doc_ids']]})
    return client.score(adapted,raw)


def run(args):
    validate()
    f=json.loads(Path(args.freeze).read_text())
    if f['sha256']!=hashes():raise ValueError('Frozen files changed; create a separately versioned study.')
    cfg=client.load_config(ROOT.parent/'config.gemini.json')
    planned=jobs(args.split)
    if args.plan:
        print(json.dumps({'calls':len(planned),'conditions':CONDITIONS,'model':cfg['model'],
                          'rpm':cfg['requests_per_minute'],'network_calls_sent':0},indent=2));return
    if not os.environ.get(cfg.get('api_key_env','EVIDENCESHIFT_API_KEY')):
        raise ValueError('Set the API-key environment variable; do not put the credential in files.')
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    manifest={'freeze':f,'config':cfg,'split':args.split,'jobs':planned,'origin':'provider'}
    p=out/'manifest.json'
    if p.exists():
        if json.loads(p.read_text())!=manifest:raise ValueError('This directory belongs to a different configuration.')
    elif (out/'responses.jsonl').exists():raise ValueError('Responses exist without a manifest.')
    else:client.save_json(p,manifest)
    old=client.read_jsonl(out/'responses.jsonl');done={r['job_id'] for r in old}
    assert len(done)==len(old) and done<={j['job_id'] for j in planned}
    limiter=client.RateLimiter(cfg['requests_per_minute'])
    now=datetime.now(timezone.utc).timestamp()
    remaining=max([0.0]+[datetime.fromisoformat(r['recorded_utc']).timestamp()+r.get('retry_deferred_seconds',0)-now for r in old])
    if remaining>cfg['max_retry_wait_seconds']:raise ValueError('Provider cooldown is still active; resume later.')
    limiter.defer(remaining);consecutive=0;by_id={c['id']:c for c in cases(args.split)}
    with (out/'responses.jsonl').open('a',encoding='utf-8') as stream:
        for j in planned:
            if j['job_id'] in done:continue
            msg=messages(by_id[j['case_id']],j['condition'],j['order'])
            response=client.call_model(cfg,msg,limiter)
            row={**j,**response,'request_hash':client.digest(msg),'recorded_utc':datetime.now(timezone.utc).isoformat()}
            stream.write(json.dumps(row)+'\n');stream.flush();os.fsync(stream.fileno());done.add(j['job_id'])
            print(f'{len(done)}/{len(planned)} {response.get("transport_error") or "received"}',flush=True)
            consecutive=consecutive+1 if response.get('transport_error') else 0
            if response.get('transport_error') in {'HTTP_400','HTTP_401','HTTP_403','HTTP_404'}:
                raise ValueError('Provider configuration rejected. Preserve the run; fix config in a new version.')
            if response.get('retry_deferred_seconds',0)>cfg['max_retry_wait_seconds']:
                raise ValueError('Paused for provider cooldown; remaining duration is recorded.')
            if consecutive>=cfg['max_consecutive_errors']:raise ValueError('Paused after consecutive provider failures.')


def analyze(path):
    out=Path(path);m=json.loads((out/'manifest.json').read_text())
    if m['freeze']['sha256']!=hashes():raise ValueError('Use the source version frozen for this run.')
    expected=jobs(m['split'])
    if m['jobs']!=expected:raise ValueError('Manifest does not match the planned schedule.')
    rows=client.read_jsonl(out/'responses.jsonl');byjob={r['job_id']:r for r in rows}
    if len(byjob)!=len(rows) or set(byjob)!={j['job_id'] for j in expected}:
        raise ValueError('Incomplete or duplicate schedule; no primary analysis produced.')
    gold=keys();bycase={c['id']:c for c in cases(m['split'])};scored=[]
    for j in expected:
        row=byjob[j['job_id']]
        if any(row[k]!=v for k,v in j.items()):raise ValueError('Job metadata mismatch.')
        c=bycase[j['case_id']];g=gold[c['id']]
        if row['request_hash']!=client.digest(messages(c,j['condition'],j['order'])):raise ValueError('Request hash mismatch.')
        scored.append({**row,**score(c,g,row['raw_output']),'pair_id':g['pair_id'],'variant':g['variant']})
    pair_scores={}
    for pair_id in sorted({r['pair_id'] for r in scored}):
        pair_scores[pair_id]={}
        for condition in CONDITIONS:
            successes=[]
            for order in ('original','reverse'):
                rr=[r for r in scored if r['pair_id']==pair_id and r['condition']==condition and r['order']==order]
                assert len(rr)==2
                successes.append(int(all(r['decision_correct'] for r in rr)))
            pair_scores[pair_id][condition]=sum(successes)/2
    summary={'origin':m.get('origin'),'split':m['split'],'responses':len(rows),'independent_pair_units':len(pair_scores),
             'conditions':{},'contrasts':{},'pair_scores':pair_scores,'human_semantic_review':'not measured',
             'caution':'Small synthetic candidate study; pairs share mechanisms. Intervals are exploratory.'}
    metrics=['decision_correct','schema_valid','quote_valid_fraction','evidence_set_covered','grounded_decision_proxy']
    for condition in CONDITIONS:
        rr=[r for r in scored if r['condition']==condition]
        summary['conditions'][condition]={k:client.mean(r[k] for r in rr) for k in metrics}
        summary['conditions'][condition].update(pair_joint_accuracy=client.mean(p[condition] for p in pair_scores.values()),
          transport_errors=sum(bool(r.get('transport_error')) for r in rr),
          reported_total_tokens=sum((r.get('usage') or {}).get('total_tokens',0) for r in rr))
    for comparator,label in [('generic_control','primary'),('baseline','secondary')]:
        differences=[p['evidence_checks']-p[comparator] for p in pair_scores.values()]
        summary['contrasts'][label]={'comparator':comparator,'pair_accuracy_difference':client.mean(differences),
                                    'exploratory_bootstrap_interval':client.cluster_bootstrap(differences)}
    client.save_json(out/'summary.json',summary)
    print(json.dumps(summary,indent=2));return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('validate')
    f=sub.add_parser('freeze');f.add_argument('--out',default=str(ROOT/'freeze.json'))
    r=sub.add_parser('run');r.add_argument('--split',choices=['dev','test'],default='dev');r.add_argument('--freeze',default=str(ROOT/'freeze.json'))
    r.add_argument('--out',required=True);r.add_argument('--plan',action='store_true')
    a=sub.add_parser('analyze');a.add_argument('run_dir')
    args=p.parse_args()
    try:
        if args.command=='validate':print(json.dumps(validate(),indent=2))
        elif args.command=='freeze':freeze(args.out)
        elif args.command=='run':run(args)
        else:analyze(args.run_dir)
    except (ValueError,AssertionError,OSError) as ex:
        print(f'ERROR: {ex}',file=sys.stderr);return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
