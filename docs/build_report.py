"""Build the report from the frozen experiment files, never from estimated scores."""

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.graphics.shapes import Drawing, Rect, String
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'travel_constraint_report.pdf'
TEAL, INK, MUTED = '#245D51', '#182D29', '#596660'
BG, RULE = '#F4F5EF', '#DCE2DA'
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyProject', fontName='Helvetica', fontSize=10.5, leading=14.6, textColor=colors.HexColor(INK), spaceAfter=8))
styles.add(ParagraphStyle(name='TitleProject', fontName='Helvetica-Bold', fontSize=29, leading=33, textColor=colors.HexColor(INK), spaceAfter=13))
styles.add(ParagraphStyle(name='HeadProject', fontName='Helvetica-Bold', fontSize=19, leading=23, textColor=colors.HexColor(TEAL), spaceAfter=13))
styles.add(ParagraphStyle(name='SubProject', fontName='Helvetica-Bold', fontSize=11.5, leading=15, textColor=colors.HexColor(TEAL), spaceBefore=9, spaceAfter=6))
styles.add(ParagraphStyle(name='SmallProject', fontName='Helvetica', fontSize=8.4, leading=11.4, textColor=colors.HexColor(MUTED), spaceAfter=7))
styles.add(ParagraphStyle(name='CellProject', fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor(INK)))
styles.add(ParagraphStyle(name='CellHead', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.white))


def para(text, style='BodyProject'):
    return Paragraph(text, styles[style])


def table(rows, widths, header=True):
    cells = [[para(escape(str(x)), 'CellHead' if i == 0 and header else 'CellProject') for x in row] for i, row in enumerate(rows)]
    t = Table(cells, colWidths=widths, hAlign='LEFT', repeatRows=1 if header else 0)
    commands = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 9),
                ('RIGHTPADDING', (0, 0), (-1, -1), 9), ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('LINEBELOW', (0, 0), (-1, -1), .35, colors.HexColor(RULE))]
    if header:
        commands += [('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(TEAL)),
                     ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(BG)])]
    t.setStyle(TableStyle(commands))
    return t


def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor(RULE))
    canvas.line(47, 41, 548, 41)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(47, 28, 'Hyojin Lee  |  Recent Areas of AI  |  2026')
    canvas.drawRightString(548, 28, str(doc.page))


def f1_chart(metrics):
    d = Drawing(500, 139)
    names = [('small_baseline', '0.5B baseline'), ('small_lora', '0.5B + LoRA'), ('large_fewshot', '7B, two-shot')]
    for i, (key, label) in enumerate(names):
        y = 104 - i * 39
        value = metrics[key]['f1']
        d.add(String(0, y + 5, label, fontName='Helvetica', fontSize=10, fillColor=colors.HexColor(INK)))
        d.add(Rect(123, y, 310, 20, fillColor=colors.HexColor(BG), strokeColor=None))
        d.add(Rect(123, y, 310 * value, 20, fillColor=colors.HexColor(TEAL if key == 'small_lora' else '#8AA99A'), strokeColor=None))
        d.add(String(443, y + 5, f'{value:.3f}', fontName='Helvetica-Bold', fontSize=10, fillColor=colors.HexColor(INK)))
    d.add(String(123, 0, 'Constraint-content micro F1 (0 to 1)', fontName='Helvetica', fontSize=9, fillColor=colors.HexColor(MUTED)))
    return d


def main():
    summary = json.loads((ROOT / 'experiments/results/comparison.json').read_text())
    m = summary['metrics']
    errors = json.loads((ROOT / 'experiments/results/error_analysis.json').read_text())
    protocol = json.loads((ROOT / 'experiments/protocol.json').read_text())
    train = json.loads((ROOT / 'experiments/training_run.json').read_text())
    lora, baseline, large = (m[k] for k in ('small_lora', 'small_baseline', 'large_fewshot'))
    content = []
    add = content.append
    def p(text, style='BodyProject'): add(para(text, style))
    def heading(text): p(text, 'HeadProject')
    def sub(text): p(text, 'SubProject')
    def page(): add(PageBreak())

    p('Travel Constraint<br/>Extraction', 'TitleProject')
    p('Small-model fine-tuning for changes to a London itinerary', 'HeadProject')
    p('Hyojin Lee · Recent Areas of AI · Semester project · 29 October 2026', 'SmallProject')
    sub('1. Task and research question')
    p('A traveler can express several changes in one sentence: keep a museum visit, return earlier, reduce walking, and choose an indoor alternative if it rains. Before an application can act, it must separate the requested conditions and preserve their meaning. This project treats that step as structured information extraction with a Transformer language model.')
    p('The input is an English change request together with a short reference itinerary. The output is a JSON list of constraints. The research question is whether supervised LoRA adaptation improves a 0.5-billion-parameter instruction model on this task, compared with the same model without adaptation and a larger model using two examples in its prompt. Routing stays deliberately simple so that the NLP component remains the main implementation and experiment.')
    sub('An illustrative input and target')
    p('<b>Reference:</b> National Gallery, lunch, a South Bank walk, hotel return at 20:00.<br/><b>Request:</b> “Keep the gallery. I must be back by 19:00. I would prefer less walking.”')
    add(table([['Extracted condition', 'Representation'], ['Keep National Gallery', 'place / include / hard'], ['Hotel return by 19:00', 'time / hotel_return / <= 19:00 / hard'], ['Reduce walking', 'walking_amount / minimize / soft']], [220, 281]))
    p('This table explains the task; it is not a claimed model prediction. The executable schema also represents conditional weather actions, numeric walking limits, and unresolved values.', 'SmallProject')
    sub('What the experiment establishes')
    p(f'The adapted model obtained content F1 {lora["f1"]:.3f} and exact output on {round(lora["exact_record_accuracy"]*80)}/80 held-out inputs. The baseline obtained F1 {baseline["f1"]:.3f}, and the larger model obtained {large["f1"]:.3f}. These are results on a controlled, AI-reviewed synthetic dataset. They are not estimates of performance on real travelers or evidence of itinerary feasibility.')

    page(); heading('2. Dataset and annotation contract')
    p('The dataset contains 400 synthetic records: 100 reference scenarios, each paired with four request paraphrases. A record stores the reference itinerary, request, structured target, scenario identifier, split, and review provenance. Scenario groups remain intact in the 280/40/80 train/validation/test split. The test set contains 20 groups, two per task family.')
    add(table([['Family', 'What the model must extract'], ['Place inclusion / exclusion', 'Requested place and include/exclude operator'], ['Hotel return time', 'Clock time and by / exactly / not-before relation'], ['Walking limit / minimization', 'Numeric cap and scope, or qualitative preference'], ['Ambiguous time / walking scope', 'Unresolved value or scope; clarification needed'], ['Nearby lunch', 'Named or context-resolved anchor place'], ['Weather alternative', 'Both rain and dry branches with their conditions'], ['Combined request', 'Six conditions in one request']], [180, 321]))
    sub('Review, duplication, and leakage controls')
    p('Version 1 contained identical request sentences across splits and an association between gallery identity and requirement strength. Before v2 model experiments, the data review removed 37 cross-split duplicate-request groups, introduced separate wording pools per split, and included both hard and soft requests for each gallery. V2 has 400 distinct full inputs and 252 distinct request texts. Intent families, semantic frames, and some wording within each split still repeat.')
    p('<b>Review status:</b> AI-assisted semantic review of authored patterns and instantiated values, plus automated checks on all 400 records. Zero records are marked human-reviewed. The reference labels therefore remain fallible. This is a transparent limitation of the submitted experiment, rather than an independent human annotation study.')
    sub('Labeling rules')
    p('Direct instructions are hard requirements; “prefer” and “if possible” indicate soft preferences. “Less walking” is a soft minimization preference, not an invented numeric limit. Missing walking scope is null and requires clarification. Relative references such as “the gallery” and “the original return time” resolve against the supplied itinerary. Rain and dry alternatives are both extracted; later weather selection activates the relevant branch.')
    p('Frozen dataset SHA-256: ' + protocol['dataset_sha256'], 'SmallProject')

    page(); heading('3. Models and training')
    p('Qwen2.5 instruction models provide the Transformer backbone [1]. All approaches use the same schema and system instructions. The two small-model runs use the original bfloat16 0.5B checkpoint; the larger comparison uses an MLX 4-bit conversion of Qwen2.5-7B-Instruct. Model revisions are pinned in the experiment protocol.')
    add(table([['Approach', 'Adaptation and prompt'], ['0.5B baseline', 'Qwen2.5-0.5B-Instruct; zero-shot; no task training'], ['0.5B + LoRA', 'Same base; task-specific supervised LoRA; zero-shot'], ['7B two-shot', 'Qwen2.5-7B-Instruct, 4-bit; two training demonstrations; no task training']], [150, 351]))
    sub('LoRA configuration')
    p('LoRA keeps pretrained weights fixed and learns low-rank updates [2]. This run updates 733,184 parameters in the last four Transformer layers. Prompt tokens are masked in the loss; supervised learning targets the annotated JSON continuation.')
    add(table([['Setting', 'Value', 'Setting', 'Value'], ['Training / validation', '280 / 40', 'Optimizer', 'Adam'], ['Steps / epochs', '840 / 3', 'Learning rate', '0.0001'], ['Batch size / seed', '1 / 42', 'LoRA rank / scale', '8 / 20'], ['Sequence cap', '1,024 tokens', 'LoRA dropout', '0.0'], ['Max observed length', '966 tokens', 'Trainable parameters', '733,184']], [133, 117, 133, 118]))
    sub('Execution and checkpoint verification')
    p(f'A GPU training attempt stopped after 224 steps with a Metal “Impacting Interactivity” error. The final run restarted from the original base on CPU; the failed GPU weights were not reused. It completed all 840 steps with compilation disabled. The trainer reported {train["elapsed_seconds_reported_by_trainer"]:.3f} seconds. All 56 saved adapter tensors were reloaded and checked for exact equality before held-out evaluation.')
    p('The validation pool contains 40 records; each loss check sampled two batches rather than the full pool. No test records were used in training, the two few-shot demonstrations, or hyperparameter selection. One final training seed was completed, so variability across training runs is not measured. The adapter includes the base model’s Apache 2.0 license and modification notice; base weights are downloaded separately.')

    page(); heading('4. Evaluation and results')
    p('The protocol was frozen before the final test: 80 inputs per approach, deterministic decoding (temperature 0, seed 42), maximum 768 generated tokens, identical output schema, and no response repair. The longest reference output is 303 tokenizer tokens. Strict JSON parsing rejects prose and code fences; schema-invalid responses count as empty extractions.')
    p('Content matching is one-to-one and order-independent. Type, target, operator, value, unit, scope, and weather condition must match after documented case/spacing/Unicode normalization. Micro precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 = 2TP/(2TP+FP+FN). Hard/soft priority is scored separately on matched content. Exact-record accuracy additionally requires the full set, priorities, and clarification flags to be correct.')
    add(f1_chart(m))
    add(Spacer(1, 9))
    rows = [['Approach', 'P / R / F1', 'Exact', 'Valid JSON', 'Mean sec.']]
    for key, name in [('small_baseline','0.5B baseline'),('small_lora','0.5B + LoRA'),('large_fewshot','7B two-shot')]:
        x=m[key]
        rows.append([name,f'{x["precision"]:.3f} / {x["recall"]:.3f} / {x["f1"]:.3f}',f'{round(x["exact_record_accuracy"]*80)}/80',f'{x["schema_validity_rate"]:.1%}',f'{x["mean_inference_seconds_including_first_request"]:.2f}'])
    add(table(rows, [112, 166, 59, 86, 78]))
    sub('Uncertainty and measurement limits')
    cis=[]
    for key,name in [('small_baseline','baseline'),('small_lora','LoRA'),('large_fewshot','7B')]:
        low,high=m[key]['f1_cluster_bootstrap_95_interval'];cis.append(f'{name}: {low:.3f}-{high:.3f}')
    p('Approximate 95% percentile bootstrap intervals for F1 are ' + '; '.join(cis) + '. The 2,000 resamples draw reference scenarios, keeping all four paraphrases together. Only 20 independent reference groups are available; these intervals describe this synthetic sample, not real-world language variation.')
    p('Inference ran on the Apple M2 GPU with 16 GB unified memory. Wall time includes prompt processing and the first generation; loading is recorded separately. The 7B prompt is longer and its weights are quantized. Capacity, precision, prompting, and output length differ. Low schema validity can dominate F1: the strict baseline measures format compliance and content extraction together, not language understanding alone.')

    page(); heading('5. Error analysis')
    p('Family-level scores show which capabilities remain weak. Each family has eight test inputs, formed from just two reference scenarios; differences should be read as diagnostic evidence, not stable rankings. All raw responses, including failures, are retained in the repository.')
    rows=[['Family','Baseline F1','LoRA F1','7B F1']]
    for family in lora['by_family']:
        rows.append([family.replace('_',' ')] + [f'{m[k]["by_family"][family]["f1"]:.3f}' for k in ('small_baseline','small_lora','large_fewshot')])
    add(table(rows, [225, 92, 92, 92]))
    sub('Two observed LoRA failures')
    for family in ('ambiguous_walking_scope','hotel_time'):
        err=next(e for e in errors['small_lora'] if e['family']==family)
        request=err['input']['request'] if 'request' in err['input'] else err['input'].get('change_request', str(err['input']))
        gold=err['expected']['constraints'][0]
        pred=err['prediction']['constraints'][0] if err['prediction'] and err['prediction']['constraints'] else None
        p(f'<b>{escape(err["id"])}</b>: {escape(request)}')
        p('Reference: ' + escape(json.dumps(gold,ensure_ascii=False)) + '<br/>Prediction: ' + escape(json.dumps(pred,ensure_ascii=False)), 'SmallProject')
    p(f'The adapted model matched {lora["counts"]["tp"]} constraint contents, produced {lora["counts"]["fp"]} false positives, and missed {lora["counts"]["fn"]}. Priority accuracy was {lora["priority_accuracy_on_matched"]:.1%} on the matched constraints only. That conditional percentage must be read together with recall: it excludes missed conditions. No post-test repair, target relabeling, or extra tuning was used to improve the reported scores.')

    page(); heading('6. London demonstration')
    p('The browser demo shows extracted conditions and simple plan edits. Live mode runs the 0.5B LoRA model; offline mode clearly replays actual validation predictions. Editing the request selects live mode. Schema errors are shown without repair.')
    image=ImageReader(str(ROOT/'docs/images/conditions.png')); iw,ih=image.getSize()
    add(Image(str(ROOT/'docs/images/conditions.png'), width=501, height=501*ih/iw))
    p('Figure 1. Actual application output from a saved validation prediction. This demonstration example is separate from the held-out test set.', 'SmallProject')
    sub('Forecasts and conditional actions')
    p('Open-Meteo / ECMWF IFS 0.25-degree forecasts [3] select rain/dry alternatives. Rain and showers describe the preceding hour: a 14:00-15:00 walk uses the bucket ending at 15:00. The application threshold is 0.1 mm/hour. Partial hours are handled conservatively; missing coverage leaves both branches pending. Forecast timestamps and simulated weather are visible.')
    sub('Place data and interface verification')
    p('Six OpenStreetMap locations [4] provide reference coordinates. Nearby means straight-line distance; hours and availability are unverified. Book cafe is a category placeholder. Routes and walking caps are not verified. All 25 automated tests passed; browser checks confirmed rain/dry switching, six conditions, and a mobile layout without horizontal overflow or browser errors.')

    page(); heading('7. Discussion and reproducibility')
    delta=(lora['f1']-baseline['f1'])*100
    p(f'On the frozen synthetic test, LoRA changed the small model’s content F1 by {delta:+.1f} percentage points relative to its untuned baseline. The exact-record score of {lora["exact_record_accuracy"]:.2%} shows that structured extraction still fails on a substantial fraction of requests. Missing-scope and time-operator errors matter because an incorrect interpretation can change the resulting plan. A production system would require broader, independently annotated requests, additional training seeds, and explicit user confirmation of unresolved conditions.')
    p('This project demonstrates the complete experimental path: an extraction contract, a documented 400-record corpus, supervised Transformer adaptation, two prompting comparisons, strict held-out scoring, error inspection, and a working conditional demonstration. The weather and place components make the outputs inspectable; they do not substitute for the NLP evaluation.')
    sub('Reproduce and inspect')
    p('The public repository contains source code, the frozen dataset and split IDs, pinned model revisions, the LoRA artifact, raw predictions, metric summaries, and error analysis. The README gives installation and demo commands. Saved examples run without model downloads; live inference uses MLX on Apple Silicon. Base weights and a Python environment are excluded from the submission ZIP. A separate reproduction entry point writes new comparison outputs, preserving the submitted measurements.')
    p('<link href="https://github.com/hjarchivenote/travel-constraint-extraction" color="#245D51">github.com/hjarchivenote/travel-constraint-extraction</link>')
    sub('AI assistance and review status')
    p('Codex assisted with topic refinement, implementation, synthetic example and target generation, consistency checks, experiment execution, error analysis, interface construction, and report/presentation drafting. The reported experiments executed the stated models; raw outputs were not manually corrected. Dataset annotations are AI-reviewed, with zero human-verified records. This disclosure does not claim independent human validation or sole unaided implementation. The author should verify the interpretation and comply with the course’s AI-assistance policy before submission.')
    sub('References and source terms')
    refs=[
        '[1] Qwen et al. Qwen2.5 Technical Report (2024). <link href="https://arxiv.org/abs/2412.15115">arxiv.org/abs/2412.15115</link>. Model revisions and licenses are recorded in experiments/protocol.json and artifacts/qwen05_lora/.',
        '[2] Hu et al. LoRA: Low-Rank Adaptation of Large Language Models (2021). <link href="https://arxiv.org/abs/2106.09685">arxiv.org/abs/2106.09685</link>.',
        '[3] Open-Meteo, ECMWF API documentation and pricing/terms, accessed 29 Oct 2026. <link href="https://open-meteo.com/en/docs/ecmwf-api">open-meteo.com/en/docs/ecmwf-api</link>; <link href="https://open-meteo.com/en/pricing">open-meteo.com/en/pricing</link>. Forecast data: CC BY 4.0; Open-Meteo / ECMWF attribution retained. Free API used for non-commercial education.',
        '[4] OpenStreetMap contributors. OpenStreetMap data and copyright. <link href="https://www.openstreetmap.org/copyright">openstreetmap.org/copyright</link>. ODbL attribution and source metadata are retained in data/reference/london_places.json.',
        'Project rights and third-party terms: LICENSE_SCOPE.md and THIRD_PARTY_NOTICES.md. No additional blanket reuse license is asserted for the original project materials.'
    ]
    for ref in refs: p(ref,'SmallProject')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(OUT),pagesize=(595.276,841.89),rightMargin=47,leftMargin=47,topMargin=47,bottomMargin=55,title='Travel Constraint Extraction',author='Hyojin Lee').build(content,onFirstPage=footer,onLaterPages=footer)
    pages=len(PdfReader(str(OUT)).pages)
    assert pages==7, f'Expected 7 pages, got {pages}; inspect overflow before delivery.'
    print(json.dumps({'report':str(OUT),'pages':pages}))


if __name__=='__main__':
    main()
