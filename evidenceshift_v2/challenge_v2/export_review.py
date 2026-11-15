"""Export a completed challenge run for human review, without condition labels."""
import csv
import json
import random
import sys
from pathlib import Path
import challenge as c


def export(run_path,out_path):
    run=Path(run_path);out=Path(out_path)
    c.analyze(run)  # Reject incomplete or changed evidence before exporting.
    manifest=json.loads((run/'manifest.json').read_text())
    rows=c.client.read_jsonl(run/'responses.jsonl')
    bycase={x['id']:x for x in c.cases(manifest['split'])}
    out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Choose an empty directory; do not overwrite completed ratings.')
    random.Random(919).shuffle(rows)
    review=[];private={}
    for i,r in enumerate(rows,1):
        token=f'R{i:04}'
        packet=json.loads(c.messages(bycase[r['case_id']],r['condition'],r['order'])[1]['content'])
        review.append({'review_id':token,'packet':json.dumps(packet,ensure_ascii=False),
                       'response':r['raw_output'],'justification_supported':'','no_unsupported_claims':'','notes':''})
        private[token]=r['job_id']
    with (out/'review_blinded.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(review[0]));w.writeheader();w.writerows(review)
    c.client.save_json(out/'review_private_key.json',private)
    print(f'Exported {len(review)} responses; share only review_blinded.csv with reviewers.')


if __name__=='__main__':export(sys.argv[1],sys.argv[2])
