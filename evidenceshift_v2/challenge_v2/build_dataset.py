"""Author-specified fictional counterfactuals. No model calls or external data."""
import csv
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFLICT = 'The documents conflict and do not establish a unique applicable answer.'
MISSING = 'The documents do not establish the information needed to answer.'


def doc(title, published, text):
    return {'title': title, 'published': published, 'text': text}


def pair(name, mechanism, question, values, documents, change_index, replacement,
         answers, rationales, evidence, split='test'):
    return dict(name=name, mechanism=mechanism, question=question, values=values,
                documents=documents, change_index=change_index, replacement=replacement,
                answers=answers, rationales=rationales, evidence=evidence, split=split)


SPECS = [
 pair('shuttle_start', 'effective_time',
      'On 15 May 2027, what departure time applies to the Kalo Route M weekday shuttle?', ['07:10','07:40'], [
      doc('Route M operating register','2027-04-02','Kalo Route M weekday departures are at 07:10. Changes in the service register take effect on the commencement date in the signed implementation notice; publication alone does not change the register.'),
      doc('Fleet committee minutes','2027-04-28','The committee voted to move the weekday Route M departure to 07:40. Dispatch is to circulate an implementation notice. Weekend departures remain at 08:20.'),
      doc('Dispatch implementation notice','2027-05-03','Signed by the dispatch manager. The Route M decision recorded on 28 April will commence on 1 June 2027. Until commencement, dispatch will use the existing operating register.'),
      doc('Station web update','2027-05-12','The new Route M timetable has been uploaded to the website. It lists the weekday departure as 07:40. Uploading a timetable does not amend its commencement date.')],2,
      'Signed by the dispatch manager. The Route M decision recorded on 28 April will commence on 1 May 2027. Until commencement, dispatch will use the existing operating register.',
      ['07:10','07:40'], ['The later publication describes a change that has not commenced on the query date.', 'The same decision has commenced before the query date.'], [[0,1,2],[1,2]]),
 pair('membership_cohort', 'effective_time',
      'What annual renewal fee applies on 1 October 2027 to a Rivo Club member admitted on 15 June 2027?', ['NGN 12000','NGN 18000'], [
      doc('Membership schedule','2027-02-01','The annual renewal fee is NGN 12000. A member has a single admission date; renewal does not create a new admission date.'),
      doc('Fee resolution','2027-08-01','From 1 September 2027, the annual renewal fee will be NGN 18000 except for members covered by the transition clause. Covered members retain the February fee for renewals through 31 December 2027.'),
      doc('Transition clause','2027-08-01','The transition clause covers members admitted before 1 July 2027.'),
      doc('Payment desk note','2027-09-20','The payment desk opens at 09:00. A renewal receipt dated in September is evidence of payment date, not of admission date.')],2,
      'The transition clause covers members admitted before 1 June 2027.',
      ['NGN 12000','NGN 18000'], ['The June 15 admission precedes the July cutoff and retains the February fee.', 'The June 15 admission is after the June cutoff, so the September fee applies.'], [[0,1,2],[1,2]]),
 pair('equipment_scope', 'partial_scope',
      'What maximum advance booking period applies to the 3D printer at Varo Workshop on 20 July 2027?', ['7 days','3 days'], [
      doc('Equipment booking rules','2027-03-01','Equipment may be reserved up to 7 days in advance. Devices covered by a later amendment use that amendment; other devices retain this limit.'),
      doc('July booking amendment','2027-07-10','For the laser cutter, the advance booking period is 3 days. This amendment takes effect on 15 July 2027.'),
      doc('Asset register','2027-07-16','The laser cutter and the 3D printer are separate bookable devices. The 3D printer is maintained in Room B; the laser cutter is in Room A.'),
      doc('Booking portal release note','2027-07-18','The portal now supports 3-day booking windows. A supported software setting does not itself select a device policy.')],1,
      'For all bookable equipment, the advance booking period is 3 days. This amendment takes effect on 15 July 2027.',
      ['7 days','3 days'], ['The laser-cutter amendment does not cover the separate 3D printer.', 'The amended scope includes every bookable device, including the printer.'], [[0,1,2],[1,2]]),
 pair('warehouse_exception', 'partial_scope',
      'What handling charge applies to a 120 kg crate at Selo Depot on 12 August 2027?', ['NGN 2000','NGN 5000'], [
      doc('Handling tariff','2027-06-01','The handling charge per crate is NGN 2000. A surcharge schedule may replace that amount for crates within its stated weight band; the amounts are alternatives, not additive.'),
      doc('Heavy crate schedule','2027-08-01','From 5 August, the handling charge is NGN 5000 for crates weighing at least 150 kg. The June tariff remains applicable outside this band.'),
      doc('Weighbridge record','2027-08-12','The crate in this question weighs 120 kg, including its packaging. No separate packaging weight should be added.'),
      doc('Vehicle log','2027-08-12','The truck delivering the crate weighs 1800 kg. Vehicle weight is not crate weight.')],1,
      'From 5 August, the handling charge is NGN 5000 for crates weighing at least 100 kg. The June tariff remains applicable outside this band.',
      ['NGN 2000','NGN 5000'], ['120 kg is outside the 150 kg band, leaving the June tariff applicable.', '120 kg is within the revised 100 kg band.'], [[0,1,2],[1,2]]),
 pair('branch_delegation', 'authority',
      'At what time must the Noma Reading Room close on 18 September 2027?', ['17:00','19:00'], [
      doc('Central operating hours','2027-01-05','Reading rooms close at 17:00. A branch manager may vary hours only within the authority granted by the delegation instrument. A variation outside that authority has no effect; central hours then apply.'),
      doc('Delegation instrument','2027-02-01','A branch manager may extend the closing time by no more than one hour. No other delegation applies to Noma Reading Room.'),
      doc('Noma circular','2027-09-10','Signed by the Noma branch manager: from 15 September through 30 September, Noma Reading Room will close at 19:00.'),
      doc('Public calendar','2027-09-16','The calendar repeats 19:00 from the branch circular. Calendar staff do not issue or approve variations.')],1,
      'A branch manager may extend the closing time by no more than two hours. No other delegation applies to Noma Reading Room.',
      ['17:00','19:00'], ['The two-hour extension exceeds the one-hour delegation and therefore has no effect.', 'The two-hour extension is within the two-hour delegation.'], [[0,1,2],[0,1,2]]),
 pair('acting_officer', 'authority',
      'What loan period applies to a standard tool borrowed from Pavo Tool Library on 11 November 2027?', ['4 days','6 days'], [
      doc('Loan rules','2027-06-01','The standard tool loan period is 4 days. The secretary or an acting secretary within their appointment period may issue a replacement period. A notice signed outside the signatory\'s appointment period has no effect.'),
      doc('Acting appointment register','2027-11-01','Officer K is appointed acting secretary from 1 November through 7 November 2027 inclusive. The register contains no other authority for Officer K to amend loan periods.'),
      doc('Loan-period circular','2027-11-09','Officer K signed this circular on 9 November: for loans made from 10 November onward, the standard tool loan period is 6 days.'),
      doc('Circulation desk log','2027-11-10','The desk received the circular on 10 November. Receipt does not confer an appointment or amend its dates.')],1,
      'Officer K is appointed acting secretary from 1 November through 14 November 2027 inclusive. The register contains no other authority for Officer K to amend loan periods.',
      ['4 days','6 days'], ['The signer lacked amendment authority on November 9, so the replacement has no effect.', 'The signer held amendment authority on November 9 and the circular applies to the November 11 loan.'], [[0,1,2],[0,1,2]]),
 pair('archive_issue', 'version_history',
      'What loading-bay appointment length applies at Leto Storehouse on 25 January 2027?', ['20 minutes','30 minutes'], [
      doc('Register rule','2026-12-01','Loading-bay appointment lengths are governed by the most recently issued service notice whose effective date has passed. Repository upload dates do not establish issue order.'),
      doc('Service notice R7','2027-01-10','Issued 10 January 2027 and effective 10 January: loading-bay appointments last 20 minutes.'),
      doc('Repository object 84','2027-01-22','Repository upload: 22 January. The enclosed service notice was issued on 6 January 2027 and effective that day. Its appointment length is 30 minutes.'),
      doc('Maintenance bulletin','2027-01-23','The repository was migrated this week. Migration preserves each enclosed notice\'s issue and effective dates.')],2,
      'Repository upload: 22 January. The enclosed service notice was issued on 16 January 2027 and effective that day. Its appointment length is 30 minutes.',
      ['20 minutes','30 minutes'], ['The enclosed January 6 notice is older than R7 despite its later upload.', 'The enclosed January 16 notice is newer than R7 and already effective.'], [[0,1,2],[0,1,2]]),
 pair('withdrawal_chain', 'version_history',
      'How long is a standard studio session at Tera Arts on 20 March 2027?', ['45 minutes','60 minutes'], [
      doc('Scheduling instruction','2027-01-01','Use the newest effective session notice that has not been withdrawn. If a newer notice is withdrawn, the preceding unwithdrawn notice continues to apply.'),
      doc('Session notices','2027-03-08','Notice N11 was issued 1 March, effective that day, setting standard sessions to 45 minutes. Notice N12 was issued 8 March, effective 10 March, setting standard sessions to 60 minutes.'),
      doc('Withdrawal record','2027-03-15','The director withdrew notice N12 on 15 March. No other notice in this packet was withdrawn.'),
      doc('Booking page cache','2027-03-19','The cached booking page was refreshed on 19 March from the 8 March release. A cache refresh is not a new session notice.')],2,
      'The director withdrew notice N11 on 15 March. No other notice in this packet was withdrawn.',
      ['45 minutes','60 minutes'], ['Withdrawal of N12 leaves N11 as the newest unwithdrawn effective notice.', 'Withdrawal of N11 leaves N12 applicable.'], [[0,1,2],[0,1,2]]),
 pair('joint_reconciliation', 'unresolved_conflict',
      'What room capacity is established for the Eno Assembly Room on 18 April 2027?', ['70 seats','90 seats'], [
      doc('Records governance','2027-02-01','Facilities and events capacity registers have equal standing. When their active entries disagree, a reconciliation signed by both office heads determines the capacity. A reconciliation with only one signature does not resolve the disagreement.'),
      doc('Active entries','2027-04-02','For the Eno Assembly Room, the facilities register records 70 seats and the events register records 90 seats. Both entries took effect on 2 April and neither has been removed.'),
      doc('Reconciliation sheet','2027-04-14','Room: Eno Assembly Room. Capacity: 90 seats. Signature record: head of facilities only.'),
      doc('Website schedule','2027-04-16','The website copies the events register. Website publication does not change the standing of either register.')],2,
      'Room: Eno Assembly Room. Capacity: 90 seats. Signature record: head of facilities and head of events.',
      [CONFLICT,'90 seats'], ['The active equal-standing records conflict and the required joint reconciliation is absent.', 'The joint signatures make the reconciliation controlling.'], [[0,1,2],[0,2]]),
 pair('revision_priority', 'unresolved_conflict',
      'What weekday opening time is established for Feno Exhibition Hall on 9 December 2027?', ['09:00','10:00'], [
      doc('Notice priority rule','2027-09-01','Notices effective on the same day are ordered by revision number. A higher numbered revision replaces a lower numbered revision. If two differing notices have the same revision number, their order cannot be inferred from the filename, upload date or file size.'),
      doc('Notice file A','2027-12-01','Revision 2. Effective 5 December 2027. Feno Exhibition Hall opens on weekdays at 09:00.'),
      doc('Notice file B','2027-12-03','Revision 2. Effective 5 December 2027. Feno Exhibition Hall opens on weekdays at 10:00.'),
      doc('Upload log','2027-12-04','File B was uploaded after file A and is larger. The log contains no additional revision or withdrawal record.')],2,
      'Revision 3. Effective 5 December 2027. Feno Exhibition Hall opens on weekdays at 10:00.',
      [CONFLICT,'10:00'], ['Same-day, same-revision notices disagree; upload order cannot establish priority.', 'Revision 3 replaces revision 2 for the same effective date.'], [[0,1,2],[0,1,2]]),
 pair('measurement_scope', 'missing_information',
      'Which shelf allocation applies to exhibit E at the Vino Display Workshop?', ['Shelf S','Shelf L'], [
      doc('Allocation rule','2027-01-01','An exhibit with an item width no greater than 30 cm uses Shelf S; an exhibit wider than 30 cm uses Shelf L. Use the item width, not its transport container width. Do not infer one measurement from the other.'),
      doc('Intake record','2027-06-02','Exhibit E: transport container width 28 cm. Item width has not been recorded.'),
      doc('Container specification','2027-06-02','Transport containers may include detachable external fixtures and do not establish the exhibit\'s displayed width.'),
      doc('Inventory status','2027-06-03','Both Shelf S and Shelf L have space available. No allocation has yet been entered for exhibit E.')],1,
      'Exhibit E: transport container width 28 cm. Item width has been recorded as 28 cm.',
      [MISSING,'Shelf S'], ['The only recorded width is for the container, which the rule prohibits using as the item width.', 'The recorded item width is 28 cm, meeting the Shelf S condition.'], [[0,1,2],[0,1]]),
 pair('subscription_record', 'missing_information',
      'What response-time commitment applies to fictional workspace R9 at Aro Support on 12 February 2027?', ['24 hours','3 hours'], [
      doc('Service schedule','2027-01-02','Standard workspaces have a 24-hour response-time commitment; Priority workspaces have a 3-hour commitment. The active-plan register determines the applicable plan. A sales quote does not activate a plan.'),
      doc('Sales quote','2027-02-08','Quote for workspace R9: Priority service, 3-hour response commitment. This document records the offered service, not a plan activation.'),
      doc('Active-plan register extract','2027-02-12','Workspace R9 exists. The plan field is unavailable in this extract. No other active-plan record is included in the packet.'),
      doc('Queue receipt','2027-02-12','A request from R9 was received at 10:00. The receipt lists neither a plan nor a response-time commitment.')],2,
      'Workspace R9 exists. The plan field records Standard, active since 1 February 2027. No other active-plan record is included in the packet.',
      [MISSING,'24 hours'], ['A Priority quote cannot establish the missing active plan.', 'The active register specifies Standard, so the quoted Priority terms do not apply.'], [[0,1,2],[0,2]]),
 pair('garden_timing', 'effective_time',
      'At what time does the Oru Garden gate open on 10 February 2027?', ['08:00','09:00'], [
      doc('Gate schedule','2027-01-01','The gate opens at 08:00. An amendment applies on its stated start date.'),
      doc('Gardener committee record','2027-02-01','The committee selected 09:00 as the amended opening time. The start date is in the gate notice.'),
      doc('Gate notice','2027-02-03','The amended opening time starts on 15 February 2027.'),
      doc('Poster delivery','2027-02-06','Posters showing the amended time were delivered today. Poster delivery does not set the start date.')],2,
      'The amended opening time starts on 5 February 2027.', ['08:00','09:00'],
      ['The start date has not arrived.', 'The start date has passed.'], [[0,1,2],[1,2]],split='dev'),
 pair('museum_exception', 'partial_scope',
      'What is the maximum loan duration for a map at Ulo Museum on 20 May 2027?', ['14 days','5 days'], [
      doc('Loan schedule','2027-01-01','Collection materials may be borrowed for 14 days unless a later amendment covers that material.'),
      doc('Preservation amendment','2027-05-01','From 10 May, photographs may be borrowed for 5 days.'),
      doc('Catalogue taxonomy','2027-05-03','Maps and photographs are distinct material classes. A map is not classified as a photograph.'),
      doc('Desk display','2027-05-15','The display advertises a 5-day loan option. The display does not define the material classes to which it applies.')],1,
      'From 10 May, all collection materials may be borrowed for 5 days.', ['14 days','5 days'],
      ['The photographs-only amendment excludes maps.', 'The amendment now includes maps.'], [[0,1,2],[1,2]],split='dev'),
 pair('scheduling_conflict', 'unresolved_conflict',
      'What start time is established for the Tovo craft session on 8 August 2027?', ['11:00','12:00'], [
      doc('Schedule authority','2027-06-01','Room bookings and instructor schedules have equal authority. Disagreement requires a reconciliation signed by both the room coordinator and instructor. A single signature is insufficient.'),
      doc('Current schedules','2027-08-02','The room booking records 11:00; the instructor schedule records 12:00 for the same Tovo session on 8 August.'),
      doc('Reconciliation form','2027-08-05','Session time: 12:00. Signed by the instructor only.'),
      doc('Reminder queue','2027-08-06','Reminder messages are copied from the instructor schedule. The queue does not resolve schedule disagreements.')],2,
      'Session time: 12:00. Signed by the instructor and room coordinator.', [CONFLICT,'12:00'],
      ['The disagreement has no jointly signed resolution.', 'The jointly signed reconciliation establishes 12:00.'], [[0,1,2],[0,2]],split='dev')
]


def build():
    all_cases=[]; keys=[]; review=[]
    for spec in SPECS:
        rng=random.Random(spec['name'])
        values=spec['values']+[CONFLICT,MISSING];rng.shuffle(values)
        options=[{'id':f'O{i+1}','text':v} for i,v in enumerate(values)]
        ids=rng.sample([f'D{i}' for i in range(1,10)],4)
        order=list(range(4));rng.shuffle(order)
        for variant in range(2):
            case_id=hashlib.sha256(f"v2:{spec['name']}:{variant}".encode()).hexdigest()[:16]
            documents=[dict(d,id=ids[i]) for i,d in enumerate(spec['documents'])]
            if variant:documents[spec['change_index']]['text']=spec['replacement']
            documents=[documents[i] for i in order]
            answer=spec['answers'][variant]
            status='conflict' if answer==CONFLICT else 'insufficient' if answer==MISSING else 'answer'
            public={'id':case_id,'question':spec['question'], 'options':options, 'documents':documents}
            gold={'id':case_id,'split':spec['split'],'pair_id':spec['name'],'variant':variant,'mechanism':spec['mechanism'],
                  'option_id':next(o['id'] for o in options if o['text']==answer),'status':status,
                  'evidence_doc_ids':[ids[i] for i in spec['evidence'][variant]],'rationale':spec['rationales'][variant],
                  'provenance':'AI-authored fictional scenario; no external or private data; independent human review pending'}
            all_cases.append((spec['split'],public));keys.append(gold)
            review.append({**gold,'question':public['question'],'options':json.dumps(options),
                           'documents':json.dumps(documents),'reviewer':'','review_status':'pending','notes':''})
    for split in ['dev','test']:
        cases=[c for s,c in all_cases if s==split];random.Random(20261115).shuffle(cases)
        (ROOT/'data'/f'{split}.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases))
    (ROOT/'data'/'answer_key.jsonl').write_text(''.join(json.dumps(k,ensure_ascii=False)+'\n' for k in keys))
    with (ROOT/'data'/'review_checklist.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(review[0]));w.writeheader();w.writerows(review)
    pack=['# EvidenceShift challenge review pack','','All records are fictional. Independent human review is pending. Solve each packet before consulting the answer-key appendix. The appendix is author-supplied, not an independent adjudication.','']
    for split in ('dev','test'):
        pack+=['## '+split.title()+' packets','']
        packets=[c for s,c in all_cases if s==split]
        random.Random(20261115).shuffle(packets)
        for c in packets:
            pack+=['### Case '+c['id'],'',c['question'],'']
            for o in c['options']:pack.append('- **'+o['id']+':** '+o['text'])
            pack+=['']
            for d in c['documents']:
                pack+=['**'+d['id']+' | '+d['title']+' | Published '+d['published']+'**','',d['text'],'']
    pack+=['## Answer key appendix','','Stop here until you have recorded your own decisions. These labels are AI-assisted and await independent review.','']
    for g in keys:
        pack+=['### '+g['id'],'',f"Option {g['option_id']}; status {g['status']}; comparison evidence {', '.join(g['evidence_doc_ids'])}.",'',g['rationale'],'']
    (ROOT/'REVIEW_PACK.md').write_text('\n'.join(pack),encoding='utf-8')
    print('Built 24 test cases in 12 counterfactual pairs and 6 development cases in 3 pairs.')


if __name__=='__main__':build()
