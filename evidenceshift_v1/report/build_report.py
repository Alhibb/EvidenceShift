"""Build a review draft from a completed, verified experiment; optional docx/matplotlib deps."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'frozen_study' if (ROOT / 'frozen_study').exists() else ROOT))
import evidenceshift as e
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def build(run_dir):
    e.load_run(run_dir)
    s = json.loads((Path(run_dir) / 'summary.json').read_text())
    if s['split'] != 'test' or s['cases'] != 40 or s['scheduled_responses'] != 160:
        raise ValueError('This report builder requires the planned 40-case, 160-response test run.')
    manifest = json.loads((Path(run_dir) / 'manifest.json').read_text())
    a, b = (s['conditions'][k] for k in e.CONDITIONS)
    delta = s['primary_effect']['difference'] * 100
    lo, hi = [x * 100 for x in s['primary_effect']['paired_family_bootstrap_95_percentile_interval']]
    pct = lambda x: f'{100*x:.1f}%'
    outcome = ('No improvement was observed' if delta == 0 else 'Higher accuracy was observed with evidence checks' if delta > 0 else 'Lower accuracy was observed with evidence checks')
    ceiling = a['decision_correct'] == b['decision_correct'] == 1
    fig, ax = plt.subplots(figsize=(6.4, 2.5))
    labels = ['Resolved', 'Conflicting', 'Insufficient', 'Consistent']
    keys = ['resolved', 'conflict', 'insufficient', 'consistent']
    x = list(range(4)); w = .34
    ax.bar([i-w/2 for i in x], [100*s['categories'][k]['baseline'] for k in keys], w, label='Baseline', color='#8b98a9')
    ax.bar([i+w/2 for i in x], [100*s['categories'][k]['evidence_checks'] for k in keys], w, label='Evidence checks', color='#234c6a')
    ax.set_xticks(x, labels); ax.set_ylabel('Decision accuracy (%)'); ax.set_ylim(0, 112)
    ax.spines[['top','right']].set_visible(False); ax.legend(loc='lower center', bbox_to_anchor=(.5,1.0), ncol=2, frameon=False)
    ax.set_yticks([0,25,50,75,100]); fig.tight_layout()
    chart = ROOT / 'report' / 'category_accuracy.png'; fig.savefig(chart, dpi=200); plt.close(fig)
    doc = Document(ROOT / 'docs' / 'official_template.docx')
    body = doc._element.body
    for child in list(body):
        if child.tag != qn('w:sectPr'): body.remove(child)
    normal = doc.styles['Normal']
    normal.font.name = 'Arial'; normal.font.size = Pt(10.5); normal.font.color.rgb = RGBColor(0,0,0); normal.font.italic = False
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.10
    for name in ['Title','Subtitle','Heading 1','Heading 2','Heading 3']:
        st=doc.styles[name]; st.font.name='Arial';st.font.color.rgb=RGBColor(0,0,0)
        st.paragraph_format.space_before=Pt(10);st.paragraph_format.space_after=Pt(5)
    doc.styles['Title'].font.size=Pt(21)
    doc.styles['Subtitle'].font.size=Pt(12)
    doc.styles['Heading 1'].font.size=Pt(14)
    doc.styles['Heading 2'].font.size=Pt(12)
    def p(text, style=None): return doc.add_paragraph(text,style)
    def h(text): return p(text,'Heading 1')
    def table(headers, rows):
        t=doc.add_table(rows=1, cols=len(headers));t.autofit=False
        for c,text in zip(t.rows[0].cells,headers):c.text=text
        for row in rows:
            for c,text in zip(t.add_row().cells,row):c.text=str(text)
        for ri,row in enumerate(t.rows):
            for ci,c in enumerate(row.cells):
                c.width=Inches(3.4 if ci==0 else 1.55)
                pr=c._tc.get_or_add_tcPr();border=OxmlElement('w:tcBorders')
                for side in ['top','left','bottom','right']:
                    node=OxmlElement('w:'+side);node.set(qn('w:val'),'single');node.set(qn('w:sz'),'4');node.set(qn('w:color'),'D9D9D9');border.append(node)
                pr.append(border)
                if ri==0:
                    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E7EDF2');pr.append(sh)
                for par in c.paragraphs:
                    par.paragraph_format.space_after=Pt(5);par.paragraph_format.space_before=Pt(5)
                    for run in par.runs:run.font.size=Pt(9);run.bold=(ri==0)
        p('')
        return t
    p('EvidenceShift','Title')
    p('Temporal and authority checks in document grounded decisions','Subtitle')
    p('Ibrahim Rabiu | DevClans Solution LTD\nAI x Epistemics Research Sprint | November 2026')
    p('Review draft. Empirical results are available; independent human annotation and author approval are pending.')
    h('Abstract')
    abstract=(f'Document-grounded assistants must distinguish genuine updates from newer drafts, future rules, archive uploads and unofficial claims. '
      f'This pilot compares a concise document-grounded baseline with an explicit evidence-checking instruction using {s["model"]}. '
      'The evaluation contains 40 fictional cases in ten domain families, with resolved discrepancies, unresolved conflicts, missing information and consistent controls. '
      'Both conditions receive identical documents and output requirements. Each case is evaluated in two document orders, producing 160 scheduled responses. '
      f'Decision accuracy was {pct(a["decision_correct"])} for the baseline and {pct(b["decision_correct"])} for evidence checks. '
      f'The paired family mean difference was {delta:.1f} percentage points, with an exploratory percentile bootstrap interval of [{lo:.1f}, {hi:.1f}]. '
      f'{outcome} on this constrained task. '
      'These results describe a small synthetic evaluation, not retrieval quality or real-world decision improvement. '
      'The packets state authority and timing explicitly, and related cases share templates. Exact quotation checks are mechanical proxies rather than semantic verification. '
      'Independent human review remains pending. The contribution is a reproducible evaluation package and a documented pilot outcome; stronger claims require harder, independently annotated evidence and additional models.')
    assert 150 <= len(abstract.split()) <= 250, len(abstract.split())
    p(abstract)
    h('1 Introduction')
    p('A recent publication date does not necessarily establish the applicable rule. An approved future change may not yet apply; a new upload may reproduce an obsolete notice. EvidenceShift asks whether explicitly checking these distinctions changes an assistant\'s answers. Its practical contribution is a transparent, modestly scoped pilot with frozen inputs, paired document orders, retained raw outputs and separate mechanical and human review measures.')
    h('2 Related work')
    p('Wang et al. [1] introduce RAMDocs and MADAM-RAG for ambiguity, misinformation and noisy evidence. Cattan et al. [2] introduce CONFLICTS and report benefits from prompting models to reason about conflicts. The general idea of conflict-aware prompting is therefore not new. EvidenceShift is a replication-oriented pilot on date and authority distinctions; it does not benchmark those published methods or claim comparable scores. CONFLICTS uses retrieved web evidence with expert conflict annotations; RAMDocs combines ambiguity, misinformation and noise. Those settings are materially harder and broader than these two-document synthetic packets.')
    doc.add_page_break()
    h('3 Methods')
    p('The test set comprises ten fictional domains, including schools, delivery, libraries, workshops and community services. Each family contains four related cases. Two separate development families supply eight additional cases. Development and test share construction patterns; this is domain separation, not an unseen-mechanism evaluation. All data were constructed with AI assistance and checked structurally; no independent human annotation has been completed.')
    table(['Case category','Test cases'],[['Resolved discrepancies','10'],['Unresolved equal-authority conflicts','10'],['Missing target information','10'],['Consistent controls','10']])
    p('Table 1. Test composition. The ten resolved cases include two each of immediate supersession, future effective dates, draft authority, archive republication and unofficial newer claims.')
    p('Each packet contains two documents, an as-of date and four shuffled answer options. Responses select an option and answer/conflict/insufficient status, provide a justification of at most 120 words, and cite one to four exact quotations. Private gold labels, category names and rationales are excluded from model requests. Both conditions use the same format requirements; the treatment adds explicit date, authority, scope and conflict checks.')
    cfg=manifest['specification']['config']
    p(f'The model was {cfg["model"]}, requested through Google\'s OpenAI-compatible endpoint, with temperature 0, reasoning effort low, a 4096-token output cap and JSON-object mode. Each call starts a fresh conversation. One call per condition per document order yields 160 test responses. Job order uses seed 20261114. Requests are serial, paced at no more than ten starts per minute; retries share the limiter. Transport failures remain in the record and count as unsuccessful decisions. The model returned its own version and usage metadata when available. Execution paused after 133 test responses because the local execution allowance was exhausted, then resumed with the same configuration without rerunning completed jobs. This time gap is visible in the raw timestamps.')
    p('The primary outcome requires a schema-valid response with the correct option and status. Scores are averaged over orders within cases, then within four-case families. The contrast is the mean of ten paired family differences. A 10,000-draw percentile family bootstrap uses seed 711. It is exploratory: the families are few and share templates, and order variants are not independent cases. The treatment also changes prompt length, so this design does not isolate individual instructions or reasoning mechanisms.')
    p('Secondary outcomes are schema compliance, exact-quote validity, annotated evidence-set coverage, a combined grounded-decision proxy and order consistency. Matching a substring from a named source does not prove that it supports the conclusion. Blinded human review files are provided, but no human semantic scores are claimed.')
    doc.add_page_break()
    h('4 Results')
    p(f'The completed test schedule contains {s["scheduled_responses"]} responses and {s["transport_errors"]} transport failures. {outcome}. All values below come from the saved run artifacts; no connectivity-check or mock-server output enters these statistics.')
    table(['Metric','Baseline','Evidence checks'],[
        ['Decision accuracy',pct(a['decision_correct']),pct(b['decision_correct'])],
        ['Schema compliance',pct(a['schema_valid']),pct(b['schema_valid'])],
        ['Exact quote validity',pct(a['quote_valid_fraction']),pct(b['quote_valid_fraction'])],
        ['Gold evidence-set coverage',pct(a['evidence_set_covered']),pct(b['evidence_set_covered'])],
        ['Grounded-decision proxy',pct(a['grounded_decision_proxy']),pct(b['grounded_decision_proxy'])],
        ['Valid decision order consistency',pct(s['order_invariance_valid_decisions']['baseline']),pct(s['order_invariance_valid_decisions']['evidence_checks'])],
        ['Reported total tokens',a['reported_total_tokens'],b['reported_total_tokens']],
        ['Mean request latency seconds',f'{a["mean_latency_seconds"]:.2f}',f'{b["mean_latency_seconds"]:.2f}']])
    p('Table 2. Primary and diagnostic results. Each condition has 80 responses across 40 cases. Quote and source-coverage measures are mechanical, not human semantic judgments. Latency includes transport retries and any limiter wait inside the measured request.')
    doc.add_picture(str(chart),width=Inches(6.3))
    p('Figure 1. Decision accuracy by case category, averaging the two document orders. Each category has ten cases; bars do not represent independent human decisions.')
    p(f'The estimated treatment difference was {delta:.1f} percentage points (exploratory bootstrap interval [{lo:.1f}, {hi:.1f}]). '+('Both conditions reached the decision-score ceiling. The degenerate interval reflects identical observed family scores; it does not establish population-level equivalence.' if ceiling else 'This interval reflects only the observed synthetic family sample. It does not establish population-level superiority or equivalence.'))
    doc.add_page_break()
    h('5 Discussion and limitations')
    p(('The most direct interpretation is a ceiling effect: the baseline already solves the constrained decisions in this small, explicitly labelled evaluation. Adding evidence checks cannot improve an observed decision score of 100%. This result is useful as a diagnostic of evaluation difficulty, not evidence that such checks are unnecessary in realistic systems.' if ceiling else 'The observed difference is limited to these packets and this model configuration. Format compliance, authority cues and answer-option wording may influence the score. It should not be interpreted as an effect on factual understanding or downstream human choices without additional evidence.'))
    p('Explicit words such as approved, draft and pending make the intended interpretation unusually clear. Four alternatives constrain generation and may cue abstention. The examples share short templates, contain no retrieval mistakes and do not test forged provenance or realistic multi-document noise. Ten domain clusters are not a representative sample of institutional evidence. A single model cannot establish broad model behaviour, and provider-side revisions may limit exact reproduction.')
    p('The grounded-decision proxy checks valid quote strings and annotated source-set coverage. An irrelevant substring from an appropriate source can still pass. Human-supported justification and unsupported-claim rates therefore remain unmeasured. The dataset labels are AI-assisted, with no independent annotation or inter-rater agreement. These limitations must remain visible in any submission.')
    p('A useful next study would use independently written, ambiguous evidence packets, distinguish publication and effective dates without overt labels, include a length-matched control, and compare additional models on a frozen external dataset. Such additions would be a new experiment, not post-hoc modifications to this test. The current outputs and protocol should remain unchanged.')
    h('6 Conclusion')
    p(f'{outcome} in this 40-case pilot. The package provides an auditable experiment and an honest boundary on its interpretation. It does not demonstrate real-world decision improvement, source authentication or end-to-end RAG performance. Independent human review and a stronger external-validity study remain necessary.')
    h('Code and data')
    p('The accompanying EvidenceShift package contains source code, 48 synthetic cases, frozen inputs, configuration without credentials, raw Gemini outputs, scores and a blinded review export. No public repository URL has been created. Test results are in runs/gemini-test; development results are separate in runs/gemini-dev. The report follows the official Apart sprint template section structure and retains its source document styles.')
    p('Author approval remains pending. The author named above should verify the evidence, confirm attribution and revise the manuscript before submission. No sprint submission has been made.')
    doc.add_page_break()
    h('References')
    p('[1] Wang, H., Prasad, A., Stengel-Eskin, E., and Bansal, M. (2025). Retrieval-Augmented Generation with Conflicting Evidence. arXiv:2504.13079. https://arxiv.org/abs/2504.13079')
    p('[2] Cattan, A., et al. (2025). DRAGged into Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented LLMs. arXiv:2506.08500. https://arxiv.org/abs/2506.08500')
    p('[3] Apart Research (2026). AI x Epistemics Research Sprint. Event guidelines and official report template, accessed 14 November 2026. https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15')
    p('[4] Google (2026). Gemini API OpenAI compatibility and rate limits. Accessed 14 November 2026. https://ai.google.dev/gemini-api/docs/openai ; https://ai.google.dev/gemini-api/docs/rate-limits')
    h('Appendix A Limitations and dual use considerations')
    p('All organisations and policies are fictional, with no personal data. Authority and effective-date labels are trusted stipulations, not verified provenance. The evaluation does not cover forged evidence, document prompt injection, long contexts, uncertain real-world outcomes, medical or legal advice, or autonomous action. Findings could help attackers craft misleading authoritative-looking text. Model outputs should not be presented as a truth oracle; real deployment requires source authentication and human oversight. The credentials used for API access are excluded from code, configuration, output logs and the distributed package.')
    h('Appendix B Reproducibility and AI use')
    p('Code, synthetic data, analysis and manuscript drafting were AI-assisted. Actual model calls were made to Gemini; raw responses and request hashes are retained. Software tests use clearly labelled mocks and are excluded from research statistics. Human review has not been substituted with an LLM judge. The delivery includes a pending-review checklist rather than invented reviewer scores. No claim of public preregistration is made; local hash freezing detects file changes but does not authenticate a public registration time.')
    p('An initial Gemini 2.5 Flash preflight returned an unavailable-model error. Google recommended Gemini 3.8 Flash, which was selected before the formal development and test schedules. Both conditions use that same model and parameters. Request pacing, retry policy, seeds and generation settings are recorded in the manifest. The delivery includes the original failed connectivity record for transparency.')
    p('Independent reviewers should inspect the labelled dataset and complete the blinded response review before stronger semantic claims are added. Any subsequent changes to data, prompts or scoring require a separately frozen experiment and explicit disclosure.')
    target=ROOT/'report'/'EvidenceShift_Research_Report.docx'
    doc.core_properties.title='EvidenceShift research report';doc.core_properties.author='Ibrahim Rabiu';doc.core_properties.last_modified_by=''
    doc.save(target)
    (ROOT/'report'/'abstract.txt').write_text(abstract+'\n')
    print(json.dumps({'docx':str(target),'abstract_words':len(abstract.split()),'primary_difference_pp':delta}))


if __name__=='__main__':build(sys.argv[1])
