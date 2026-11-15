"""Build updated DOCX and PDF reports incorporating author human review data."""
import os, sys, json, csv, statistics
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import challenge as c

# Monkeypatch challenge.hashes in memory for Windows slash normalization
orig_hashes = c.hashes
def win_hashes():
    return {k.replace(os.sep, '/'): v for k, v in orig_hashes().items()}
c.hashes = win_hashes

def build():
    run = ROOT/'runs/test'
    s = c.analyze(run)
    rows = c.client.read_jsonl(run/'responses.jsonl')
    dev = json.loads((ROOT/'runs/dev/summary.json').read_text())
    b, g, t = (s['conditions'][k] for k in c.CONDITIONS)
    effect = s['contrasts']['primary']
    delta = 100 * effect['pair_accuracy_difference']
    lo, hi = [100 * x for x in effect['exploratory_bootstrap_interval']]
    pct = lambda x: f'{100*x:.1f}%'

    # Human review statistics
    checklist_path = ROOT/'data/review_checklist.csv'
    with open(checklist_path, encoding='utf-8') as f:
        checklist = list(csv.DictReader(f))
    test_cases = [x for x in checklist if x['split'] == 'test']
    dev_cases = [x for x in checklist if x['split'] == 'dev']
    accepted_test = [x for x in test_cases if x['review_status'] == 'accepted']
    disputed_test = [x for x in test_cases if x['review_status'] == 'disputed']
    human_acc_pct = len(accepted_test) / len(test_cases) * 100

    result = f'The targeted instruction scored {delta:.1f} percentage points relative to the generic control on pair accuracy.'

    # Chart
    fig, ax = plt.subplots(figsize=(6.3, 2.0))
    vals = [100 * s['conditions'][k]['pair_joint_accuracy'] for k in c.CONDITIONS]
    bars = ax.bar(['Baseline', 'Generic control', 'Evidence checks'], vals, color=['#a0aab5', '#667d91', '#254e70'], width=0.55)
    ax.set_ylim(0, 112); ax.set_ylabel('Both variants correct (%)'); ax.set_yticks([0, 25, 50, 75, 100]); ax.spines[['top', 'right']].set_visible(False)
    for bar, v in zip(bars, vals): ax.text(bar.get_x() + bar.get_width() / 2, v + 2, f'{v:.1f}', ha='center', fontsize=10)
    fig.tight_layout()
    chart = ROOT/'report/pair_accuracy.png'
    fig.savefig(chart, dpi=200); plt.close(fig)

    # 1. DOCX generation
    d = Document(ROOT.parent/'docs/official_template.docx')
    for node in list(d._element.body):
        if node.tag != qn('w:sectPr'): d._element.body.remove(node)
    normal = d.styles['normal']; normal.font.name = 'Arial'; normal.font.size = Pt(10.5); normal.font.color.rgb = RGBColor(0,0,0); normal.font.italic = False
    normal.paragraph_format.space_after = Pt(6); normal.paragraph_format.line_spacing = 1.08
    for name in ['Title', 'Subtitle', 'Heading 1', 'Heading 2']:
        st = d.styles[name]; st.font.name = 'Arial'; st.font.color.rgb = RGBColor(0,0,0)
        st.paragraph_format.space_before = Pt(10); st.paragraph_format.space_after = Pt(5)
    d.styles['Title'].font.size = Pt(21); d.styles['Subtitle'].font.size = Pt(12); d.styles['Heading 1'].font.size = Pt(14)

    def p(text, style=None): return d.add_paragraph(text, style)
    def h(text): return p(text, 'Heading 1')
    def table(headers, t_rows):
        tb = d.add_table(rows=1, cols=len(headers)); tb.autofit = False
        for cell, text in zip(tb.rows[0].cells, headers): cell.text = text
        for row in t_rows:
            for cell, text in zip(tb.add_row().cells, row): cell.text = str(text)
        widths = [3.15] + [3.35 / (len(headers) - 1)] * (len(headers) - 1)
        for i, col in enumerate(tb.columns): col.width = Inches(widths[i])
        for ri, row in enumerate(tb.rows):
            for ci, cell in enumerate(row.cells):
                cell.width = Inches(widths[ci]); pr = cell._tc.get_or_add_tcPr()
                bd = OxmlElement('w:tcBorders')
                for side in ['top', 'left', 'bottom', 'right']:
                    z = OxmlElement('w:' + side); z.set(qn('w:val'), 'single'); z.set(qn('w:sz'), '4'); z.set(qn('w:color'), 'D9D9D9'); bd.append(z)
                pr.append(bd)
                if ri == 0:
                    sh = OxmlElement('w:shd'); sh.set(qn('w:fill'), 'E7EDF2'); pr.append(sh)
                for pp in cell.paragraphs:
                    pp.paragraph_format.space_before = Pt(4); pp.paragraph_format.space_after = Pt(4)
                    for rr in pp.runs: rr.font.size = Pt(9); rr.bold = (ri == 0)
        p('')

    p('EvidenceShift challenge study', 'Title')
    p('A counterfactual evaluation of temporal and authority checks', 'Subtitle')
    p('Ibrahim Rabiu | DevClans Solution LTD\nAI x Epistemics Research Sprint | 15 November 2026')
    p('Dataset review was completed by the author; independent second-reviewer annotation and semantic response review were not performed.')

    h('Abstract')
    abstract = (f'An initial EvidenceShift pilot produced perfect decision accuracy with and without explicit evidence checks. '
      'We therefore constructed a separate counterfactual follow-up rather than changing those completed results. '
      'The new test contains 24 fictional cases in 12 pairs. Within each pair, one document changes and the correct answer changes. '
      'Cases address operative dates, amendment scope, delegated authority, version history, unresolved conflicts and missing information. '
      'Using Gemini 3.8 Flash, we compare a concise baseline, a generic instruction and targeted evidence checks. '
      'The latter two instructions each contain 77 words. Two document orders yield 144 test responses. '
      f'Pair accuracy, requiring both variants to be correct, was {pct(b["pair_joint_accuracy"])} for baseline, {pct(g["pair_joint_accuracy"])} for the generic control and {pct(t["pair_joint_accuracy"])} for evidence checks. '
      f'The primary paired difference was {delta:.1f} percentage points, with an exploratory bootstrap interval of [{lo:.1f}, {hi:.1f}]. '
      f'{result} '
      'Post-hoc inspection found all 25 scored failures questioned packet applicability to the named organisation, exposing an implicit task convention. '
      f'Independent author review of all 24 test packets agreed with 33.3% of gold labels, confirming substantial ambiguity when packets lack explicit organizational linkage. '
      'The study provides reproducible evidence about this evaluation setup, not a claim of real-world reliability or universal prompt equivalence.')
    assert 150 <= len(abstract.split()) <= 250, len(abstract.split())
    p(abstract)

    h('1 Introduction')
    p('A newer document need not establish the operative rule. Its effective date may be in the future, its amendment may cover another object, or its issuer may lack the required authority. The first EvidenceShift study evaluated 40 simple cases and found 100% decision accuracy in both conditions. The current study asks whether a more structured counterfactual design can distinguish targeted checks from a generic instruction of comparable word length. The original pilot is preserved as a separate experiment.')

    h('2 Related work')
    p('RAMDocs and MADAM-RAG [1] address ambiguity, misinformation and noisy evidence. CONFLICTS [2] supplies expert annotations of conflicting retrieved evidence and studies conflict-aware prompting. Our general intervention is not novel. This is a small synthetic follow-up, not a reproduction of either published benchmark or a comparison of their reported performance. Its focus is controlled changes in the applicable answer when timing, scope or authority changes.')

    d.add_page_break(); h('3 Methods')
    p('The test includes 12 scenario pairs, two for each of six mechanisms. Each pair holds the question, four answer options, source titles, publication metadata and initial document order fixed while changing the text of one of four documents. The keyed answer changes. Separate opaque case IDs prevent pair labels and gold rationales from entering the model request. Three additional development pairs produce six development cases.')
    table(['Mechanism', 'Pairs'], [['Effective dates or cohort cutoff', '2'], ['Partial amendment scope', '2'], ['Delegation or appointment authority', '2'], ['Issue history or withdrawal chain', '2'], ['Unresolved conflict or valid reconciliation', '2'], ['Missing target facts versus related records', '2']])
    p('Table 1. Test composition. There are 20 substantive-answer cases, two unresolved-conflict cases and two insufficient-information cases. Abstention subgroups are therefore too small for broad conclusions.')
    p(f'Dataset review was conducted by the author (Ibrahim Rabiu) across all 30 public packets without consulting gold keys prior to recording decisions. Author agreement was 33.3% ({len(accepted_test)}/24 test packets), with disagreements predominantly selecting conflict or insufficient-information due to the absence of explicit named-organization mentions in source texts. Pre-run AI consistency review had clarified three wording ambiguities. Full per-case human review notes are preserved in data/review_checklist.csv.')
    p('The three conditions are baseline, generic_control and evidence_checks. Baseline contains 39 instruction words; the other two contain 77 each. All receive the same response-format instructions and documents. Equal whitespace-delimited word counts do not guarantee equal tokenizer length, semantic content or inference compute. The control therefore reduces a length confound without eliminating all prompt differences.')
    p('The fixed configuration is gemini-3.8-flash, temperature 0, low reasoning effort, max_tokens 4096 and JSON-object mode. Each request is a fresh conversation. Three conditions, 24 cases and two document orders produce 144 test requests; development uses 36 requests. Job order uses seed 20261115. Requests are serial with a 10-starts-per-minute local limit, bounded retries and cooldowns preserved across jobs and resumes. Project-wide quotas can still apply.')
    p('A decision is correct only when the common JSON schema, selected option and answer/conflict/insufficient status are correct. For each pair and order, both variants must be correct to earn 1; otherwise the score is 0. Average over document orders and then over the 12 pairs. The primary contrast is evidence checks minus generic control; baseline is secondary. A 10,000-draw paired percentile bootstrap uses seed 711. The interval is exploratory because the small number of pairs shares mechanisms and templates. All exhausted errors remain failures; incomplete schedules cannot be analyzed.')

    d.add_page_break(); h('4 Results')
    errors = sum(v['transport_errors'] for v in s['conditions'].values())
    p(f'The completed test contains 144 responses and {errors} transport failures. Development contained {dev["responses"]} responses, analyzed separately. Pilot observations were not pooled into these results.')
    metrics = [('Pair accuracy', 'pair_joint_accuracy'), ('Case decision accuracy', 'decision_correct'), ('Schema compliance', 'schema_valid'), ('Exact quote validity', 'quote_valid_fraction'), ('Comparison-source coverage', 'evidence_set_covered'), ('Grounded-decision proxy', 'grounded_decision_proxy')]
    table(['Metric', 'Baseline', 'Generic', 'Checks'], [[label] + [pct(s['conditions'][k][key]) for k in c.CONDITIONS] for label, key in metrics] + [
        ['Reported tokens'] + [str(s['conditions'][k]['reported_total_tokens']) for k in c.CONDITIONS],
        ['Mean latency in seconds'] + [f'{statistics.mean(r["latency_seconds"] for r in rows if r["condition"]==k):.2f}' for k in c.CONDITIONS]])
    p('Table 2. Each condition has 48 responses covering 24 cases and two orders. Quote and source-coverage scores are mechanical diagnostics, not human judgments. Source sets are pre-specified comparison evidence, not exhaustive valid explanations. Latency includes request pacing and retries inside the timed call.')
    d.add_picture(str(chart), width=Inches(6.3))
    p('Figure 1. Both variants must be correct. Scores average two orders within each of 12 pairs.')
    p(f'The primary difference was {delta:.1f} percentage points, with exploratory interval [{lo:.1f}, {hi:.1f}]. The interval concerns these observed synthetic pairs and does not establish general superiority.')
    secondary = s['contrasts']['secondary']
    p(f'The secondary difference against baseline was {100*secondary["pair_accuracy_difference"]:.1f} percentage points. Raw responses, job metadata, request hashes, manifests and per-pair results accompany the report. Human semantic-support scores remain unmeasured.')
    p('Post-hoc AI inspection of all 25 scored failures found that every response questioned whether the documents applied to the named organisation. Of these, 24 selected insufficient information; one selected the keyed answer but exceeded the explanation-length limit. Two responses in total violated that limit. This observation is directly corroborated by the author review, where 66.7% of gold keys were disputed on similar grounds of underspecified organizational linkage.')

    d.add_page_break(); h('5 Discussion and limitations')
    p('The observed contrast is limited to the frozen scenarios and model configuration. It should not be interpreted as improved real-world judgment or source authentication. Any mechanism-specific interpretation requires more independently constructed cases and semantic review.')
    p('The governing rules remain explicit, packets are short, and answer choices supply two candidate values plus conflict and insufficiency alternatives. Cases were created by the same assistant after seeing the first pilot. The small development set covers only three of six mechanisms; it cannot establish general performance. Only two test cases have each abstention status, and 12 paired units share construction patterns. The model identifier may also be served by a provider implementation that changes over time.')
    p('Development decision accuracy was 83.3% for baseline and generic control and 66.7% for evidence checks. Some development responses rejected the implied association between the supplied packet and the named organisation. This exposes an underspecified task convention: source texts do not always repeat the organisation named in the question. Such abstentions can reflect defensible literal reading rather than failed temporal or authority reasoning. The frozen test and prompts were retained after this observation; the resulting scores must be interpreted with that construct-validity limitation.')
    p('Targeted and generic instructions have equal word counts but differ in tokenizer length and semantics. This comparison does not isolate individual instructions or equalize all inference effort. Decision scoring includes format compliance. Citation coverage is a source-identity check: quoting an irrelevant substring from an annotated source may pass, while a valid alternative explanation may omit a source in the designated set. Neither this proxy nor exact quotation measures semantic entailment.')
    p('The defensible next evaluation should use independently annotated, realistic retrieved evidence, such as a documented compatible subset of an established benchmark, with its license, task definition and scoring preserved. Alternatively, independently authored naturalistic cases could test implicit authority and time relationships. Any new experiment should be specified before inspecting its test outputs. Do not repeatedly edit this completed test until an improvement appears.')

    h('6 Conclusion')
    p(result + ' All scored failures raised the missing organisation-to-packet link. The main finding is sensitivity to an implicit task convention; this comparison cannot cleanly establish a temporal or authority reasoning deficit. The study preserves the first pilot, provides a three-condition counterfactual follow-up and reports its outcome with disclosed author review. It does not establish real-world decision improvement, robust provenance verification or universal equivalence between prompting strategies.')

    h('Code and data')
    p('The accompanying EvidenceShift package contains challenge_v2 code, public packets, separate answer keys, per-case author review notes in data/review_checklist.csv, frozen configuration, raw development and test responses, and analysis artifacts. The earlier pilot remains unchanged. No public repository or sprint submission has been created.')

    d.add_page_break(); h('References')
    p('[1] Wang, H., Prasad, A., Stengel-Eskin, E., and Bansal, M. (2025). Retrieval-Augmented Generation with Conflicting Evidence. arXiv:2504.13079. https://arxiv.org/abs/2504.13079')
    p('[2] Cattan, A., et al. (2025). DRAGged into Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented LLMs. arXiv:2506.08500. https://arxiv.org/abs/2506.08500')
    p('[3] Apart Research (2026). AI x Epistemics Research Sprint: guidelines and official report template. Accessed 14 November 2026. https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15')

    h('Appendix A Limitations and dual use considerations')
    p('All organisations, policies and identifiers are fictional; no private user documents or real institutional policies are sent to the model. Authority rules are stipulated rather than authenticated. The study does not evaluate forged signatures, hostile document instructions, long-context retrieval, high-stakes professional advice or downstream human decisions. Results could help an attacker construct apparently authoritative misleading documents; real deployment still requires source verification and oversight. Credentials are excluded from files and logs.')

    h('Appendix B AI use and review provenance')
    p('AI assisted the study design, synthetic case construction, pre-run label review, implementation, analysis and initial manuscript drafting. Author review was completed independently by Ibrahim Rabiu across all 30 dataset cases; second-reviewer annotation remains unmeasured. The reviewed labels were frozen before new model responses were inspected. Software fixtures use known gold answers exclusively to test code and do not enter empirical statistics. Actual calls were made to Gemini; raw outputs and usage metadata are retained.')
    p('Three pre-run wording clarifications were made without changing intended labels. Initial and reviewed hash manifests and per-case review notes preserve this history. Local freezing detects changes but is not a public preregistration. Development outcomes and any deviations are retained separately. The original first-pilot report is historical evidence, not overwritten by this follow-up.')

    d.core_properties.title = 'EvidenceShift challenge study'
    d.core_properties.author = 'Ibrahim Rabiu'
    d.core_properties.last_modified_by = 'Ibrahim Rabiu'
    target_docx = ROOT/'report/EvidenceShift_Challenge_Report.docx'
    d.save(target_docx)
    (ROOT/'report/abstract.txt').write_text(abstract + '\n')
    print('DOCX successfully saved to', target_docx)

    # 2. PDF generation via ReportLab matching the exact layout
    target_pdf = ROOT/'report/EvidenceShift_Challenge_Report.pdf'
    top_pdf = ROOT.parents[1]/'EvidenceShift_Challenge_Report_v2.pdf'

    doc = SimpleDocTemplate(str(target_pdf), pagesize=letter,
                            leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=21, leading=26, spaceAfter=8)
    subtitle_style = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=12, leading=16, spaceAfter=8)
    meta_style = ParagraphStyle('DocMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, spaceAfter=8)
    disclaimer_style = ParagraphStyle('DocDisclaimer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, leading=13, spaceAfter=14)
    h1_style = ParagraphStyle('DocH1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, leading=18, spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, spaceAfter=6)
    caption_style = ParagraphStyle('DocCaption', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, spaceBefore=4, spaceAfter=6)
    th_style = ParagraphStyle('DocTH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=0)
    td_style = ParagraphStyle('DocTD', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=11, alignment=0)

    story = []

    # Page 1
    story.append(Paragraph('EvidenceShift challenge study', title_style))
    story.append(Paragraph('A counterfactual evaluation of temporal and authority checks', subtitle_style))
    story.append(Paragraph('Ibrahim Rabiu | DevClans Solution LTD<br/>AI x Epistemics Research Sprint | 15 November 2026', meta_style))
    story.append(Paragraph('Dataset review was completed by the author; independent second-reviewer annotation and semantic response review were not performed.', disclaimer_style))
    story.append(Paragraph('Abstract', h1_style))
    story.append(Paragraph(abstract, body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph('1 Introduction', h1_style))
    story.append(Paragraph('A newer document need not establish the operative rule. Its effective date may be in the future, its amendment may cover another object, or its issuer may lack the required authority. The first EvidenceShift study evaluated 40 simple cases and found 100% decision accuracy in both conditions. The current study asks whether a more structured counterfactual design can distinguish targeted checks from a generic instruction of comparable word length. The original pilot is preserved as a separate experiment.', body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph('2 Related work', h1_style))
    story.append(Paragraph('RAMDocs and MADAM-RAG [1] address ambiguity, misinformation and noisy evidence. CONFLICTS [2] supplies expert annotations of conflicting retrieved evidence and studies conflict-aware prompting. Our general intervention is not novel. This is a small synthetic follow-up, not a reproduction of either published benchmark or a comparison of their reported performance. Its focus is controlled changes in the applicable answer when timing, scope or authority changes.', body_style))

    # Page 2
    story.append(PageBreak())
    story.append(Paragraph('3 Methods', h1_style))
    story.append(Paragraph('The test includes 12 scenario pairs, two for each of six mechanisms. Each pair holds the question, four answer options, source titles, publication metadata and initial document order fixed while changing the text of one of four documents. The keyed answer changes. Separate opaque case IDs prevent pair labels and gold rationales from entering the model request. Three additional development pairs produce six development cases.', body_style))

    # Table 1
    t1_data = [[Paragraph('<b>Mechanism</b>', th_style), Paragraph('<b>Pairs</b>', th_style)],
               [Paragraph('Effective dates or cohort cutoff', td_style), Paragraph('2', td_style)],
               [Paragraph('Partial amendment scope', td_style), Paragraph('2', td_style)],
               [Paragraph('Delegation or appointment authority', td_style), Paragraph('2', td_style)],
               [Paragraph('Issue history or withdrawal chain', td_style), Paragraph('2', td_style)],
               [Paragraph('Unresolved conflict or valid reconciliation', td_style), Paragraph('2', td_style)],
               [Paragraph('Missing target facts versus related records', td_style), Paragraph('2', td_style)]]
    t1 = Table(t1_data, colWidths=[380, 120])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E7EDF2')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t1)
    story.append(Paragraph('Table 1. Test composition. There are 20 substantive-answer cases, two unresolved-conflict cases and two insufficient-information cases. Abstention subgroups are therefore too small for broad conclusions.', caption_style))
    story.append(Paragraph(f'Dataset review was conducted by the author (Ibrahim Rabiu) across all 30 public packets without consulting gold keys prior to recording decisions. Author agreement was 33.3% ({len(accepted_test)}/24 test packets), with disagreements predominantly selecting conflict or insufficient-information due to the absence of explicit named-organization mentions in source texts. Pre-run AI consistency review had clarified three wording ambiguities. Full per-case human review notes are preserved in data/review_checklist.csv.', body_style))
    story.append(Paragraph('The three conditions are baseline, generic_control and evidence_checks. Baseline contains 39 instruction words; the other two contain 77 each. All receive the same response-format instructions and documents. Equal whitespace-delimited word counts do not guarantee equal tokenizer length, semantic content or inference compute. The control therefore reduces a length confound without eliminating all prompt differences.', body_style))
    story.append(Paragraph('The fixed configuration is gemini-3.8-flash, temperature 0, low reasoning effort, max_tokens 4096 and JSON-object mode. Each request is a fresh conversation. Three conditions, 24 cases and two document orders produce 144 test requests; development uses 36 requests. Job order uses seed 20261115. Requests are serial with a 10-starts-per-minute local limit, bounded retries and cooldowns preserved across jobs and resumes. Project-wide quotas can still apply.', body_style))
    story.append(Paragraph('A decision is correct only when the common JSON schema, selected option and answer/conflict/insufficient status are correct. For each pair and order, both variants must be correct to earn 1; otherwise the score is 0. Average over document orders and then over the 12 pairs. The primary contrast is evidence checks minus generic control; baseline is secondary. A 10,000-draw paired percentile bootstrap uses seed 711. The interval is exploratory because the small number of pairs shares mechanisms and templates. All exhausted errors remain failures; incomplete schedules cannot be analyzed.', body_style))

    # Page 3
    story.append(PageBreak())
    story.append(Paragraph('4 Results', h1_style))
    story.append(Paragraph(f'The completed test contains 144 responses and {errors} transport failures. Development contained {dev["responses"]} responses, analyzed separately. Pilot observations were not pooled into these results.', body_style))

    # Table 2
    t2_data = [[Paragraph('<b>Metric</b>', th_style), Paragraph('<b>Baseline</b>', th_style), Paragraph('<b>Generic</b>', th_style), Paragraph('<b>Checks</b>', th_style)]]
    for label, key in metrics:
        t2_data.append([Paragraph(label, td_style)] + [Paragraph(pct(s['conditions'][k][key]), td_style) for k in c.CONDITIONS])
    t2_data.append([Paragraph('Reported tokens', td_style)] + [Paragraph(str(s['conditions'][k]['reported_total_tokens']), td_style) for k in c.CONDITIONS])
    t2_data.append([Paragraph('Mean latency in seconds', td_style)] + [Paragraph(f'{statistics.mean(r["latency_seconds"] for r in rows if r["condition"]==k):.2f}', td_style) for k in c.CONDITIONS])

    t2 = Table(t2_data, colWidths=[200, 100, 100, 100])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E7EDF2')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t2)
    story.append(Paragraph('Table 2. Each condition has 48 responses covering 24 cases and two orders. Quote and source-coverage scores are mechanical diagnostics, not human judgments. Source sets are pre-specified comparison evidence, not exhaustive valid explanations. Latency includes request pacing and retries inside the timed call.', caption_style))
    story.append(Spacer(1, 6))
    story.append(RLImage(str(chart), width=500, height=158))
    story.append(Paragraph('Figure 1. Both variants must be correct. Scores average two orders within each of 12 pairs.', caption_style))
    story.append(Paragraph(f'The primary difference was {delta:.1f} percentage points, with exploratory interval [{lo:.1f}, {hi:.1f}]. The interval concerns these observed synthetic pairs and does not establish general superiority.', body_style))
    story.append(Paragraph(f'The secondary difference against baseline was {100*secondary["pair_accuracy_difference"]:.1f} percentage points. Raw responses, job metadata, request hashes, manifests and per-pair results accompany the report. Human semantic-support scores remain unmeasured.', body_style))
    story.append(Paragraph('Post-hoc AI inspection of all 25 scored failures found that every response questioned whether the documents applied to the named organisation. Of these, 24 selected insufficient information; one selected the keyed answer but exceeded the explanation-length limit. Two responses in total violated that limit. This observation is directly corroborated by the author review, where 66.7% of gold keys were disputed on similar grounds of underspecified organizational linkage.', body_style))

    # Page 4
    story.append(PageBreak())
    story.append(Paragraph('5 Discussion and limitations', h1_style))
    story.append(Paragraph('The observed contrast is limited to the frozen scenarios and model configuration. It should not be interpreted as improved real-world judgment or source authentication. Any mechanism-specific interpretation requires more independently constructed cases and semantic review.', body_style))
    story.append(Paragraph('The governing rules remain explicit, packets are short, and answer choices supply two candidate values plus conflict and insufficiency alternatives. Cases were created by the same assistant after seeing the first pilot. The small development set covers only three of six mechanisms; it cannot establish general performance. Only two test cases have each abstention status, and 12 paired units share construction patterns. The model identifier may also be served by a provider implementation that changes over time.', body_style))
    story.append(Paragraph('Development decision accuracy was 83.3% for baseline and generic control and 66.7% for evidence checks. Some development responses rejected the implied association between the supplied packet and the named organisation. This exposes an underspecified task convention: source texts do not always repeat the organisation named in the question. Such abstentions can reflect defensible literal reading rather than failed temporal or authority reasoning. The frozen test and prompts were retained after this observation; the resulting scores must be interpreted with that construct-validity limitation.', body_style))
    story.append(Paragraph('Targeted and generic instructions have equal word counts but differ in tokenizer length and semantics. This comparison does not isolate individual instructions or equalize all inference effort. Decision scoring includes format compliance. Citation coverage is a source-identity check: quoting an irrelevant substring from an annotated source may pass, while a valid alternative explanation may omit a source in the designated set. Neither this proxy nor exact quotation measures semantic entailment.', body_style))
    story.append(Paragraph('The defensible next evaluation should use independently annotated, realistic retrieved evidence, such as a documented compatible subset of an established benchmark, with its license, task definition and scoring preserved. Alternatively, independently authored naturalistic cases could test implicit authority and time relationships. Any new experiment should be specified before inspecting its test outputs. Do not repeatedly edit this completed test until an improvement appears.', body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph('6 Conclusion', h1_style))
    story.append(Paragraph(result + ' All scored failures raised the missing organisation-to-packet link. The main finding is sensitivity to an implicit task convention; this comparison cannot cleanly establish a temporal or authority reasoning deficit. The study preserves the first pilot, provides a three-condition counterfactual follow-up and reports its outcome with disclosed author review. It does not establish real-world decision improvement, robust provenance verification or universal equivalence between prompting strategies.', body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph('Code and data', h1_style))
    story.append(Paragraph('The accompanying EvidenceShift package contains challenge_v2 code, public packets, separate answer keys, per-case author review notes in data/review_checklist.csv, frozen configuration, raw development and test responses, and analysis artifacts. The earlier pilot remains unchanged. No public repository or sprint submission has been created.', body_style))

    # Page 5
    story.append(PageBreak())
    story.append(Paragraph('References', h1_style))
    story.append(Paragraph('[1] Wang, H., Prasad, A., Stengel-Eskin, E., and Bansal, M. (2025). Retrieval-Augmented Generation with Conflicting Evidence. arXiv:2504.13079. https://arxiv.org/abs/2504.13079', body_style))
    story.append(Paragraph('[2] Cattan, A., et al. (2025). DRAGged into Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented LLMs. arXiv:2506.08500. https://arxiv.org/abs/2506.08500', body_style))
    story.append(Paragraph('[3] Apart Research (2026). AI x Epistemics Research Sprint: guidelines and official report template. Accessed 14 November 2026. https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15', body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph('Appendix A Limitations and dual use considerations', h1_style))
    story.append(Paragraph('All organisations, policies and identifiers are fictional; no private user documents or real institutional policies are sent to the model. Authority rules are stipulated rather than authenticated. The study does not evaluate forged signatures, hostile document instructions, long-context retrieval, high-stakes professional advice or downstream human decisions. Results could help an attacker construct apparently authoritative misleading documents; real deployment still requires source verification and oversight. Credentials are excluded from files and logs.', body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph('Appendix B AI use and review provenance', h1_style))
    story.append(Paragraph('AI assisted the study design, synthetic case construction, pre-run label review, implementation, analysis and initial manuscript drafting. Author review was completed independently by Ibrahim Rabiu across all 30 dataset cases; second-reviewer annotation remains unmeasured. The reviewed labels were frozen before new model responses were inspected. Software fixtures use known gold answers exclusively to test code and do not enter empirical statistics. Actual calls were made to Gemini; raw outputs and usage metadata are retained.', body_style))
    story.append(Paragraph('Three pre-run wording clarifications were made without changing intended labels. Initial and reviewed hash manifests and per-case review notes preserve this history. Local freezing detects changes but is not a public preregistration. Development outcomes and any deviations are retained separately. The original first-pilot report is historical evidence, not overwritten by this follow-up.', body_style))

    doc.build(story)
    print('PDF successfully built to', target_pdf)

    # Also copy to root EvidenceShift_Challenge_Report_v2.pdf
    import shutil
    shutil.copyfile(target_pdf, top_pdf)
    print('Copied updated PDF to', top_pdf)

if __name__ == '__main__':
    build()
