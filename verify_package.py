from pathlib import Path
import json, sys

root = Path(__file__).resolve().parent
errors=[]

def need(rel):
    p=root/rel
    if not p.exists(): errors.append(f"Missing: {rel}")
    return p

need('data/full_45_indicator/spaphish_item_dictionary.csv')
need('data/full_45_indicator/spaphish_hybrid_aggregate.dat')
need('data/spaphish_binary_folds.csv')
need('statistical_validation/spaphish_joint_oof_predictions_complete.csv')

need('src/mfi_ct_spaphish_historical.c')
need('src/dmc_ac_spaphish_historical.cpp')
need('src/divide_en_10_historical.c')
need('scripts/reproduce_main_10fold.py')
need('provenance/SOURCE_PROVENANCE.md')

need('experiments/spaphish_complexity_efficiency_results/complexity_efficiency/complexity_efficiency_summary.json')

temporal = next((root/'experiments/spaphish_temporal_validation_results').rglob('temporal_validation_summary.json'), None)
if temporal is None:
    errors.append('Missing temporal_validation_summary.json')
else:
    d=json.loads(temporal.read_text(encoding='utf-8'))
    if abs(float(d.get('best_sigma', -1))-0.04)>1e-12: errors.append('Unexpected temporal best_sigma')
    p=d.get('test2025_positive',{})
    if abs(float(p.get('accuracy',-1))-0.7690802348336595)>1e-9: errors.append('Unexpected 2025 positive accuracy')
    if abs(float(p.get('phishing_recall',-1))-0.7612293144208038)>1e-9: errors.append('Unexpected 2025 phishing recall')

rule_summary = root/'experiments/spaphish_rule_evolution_20_analysis/summary.json'
if not rule_summary.exists():
    errors.append('Missing rule evolution summary.json')
else:
    d=json.loads(rule_summary.read_text(encoding='utf-8'))
    ph=d.get('78',{})
    expected={'baseline_positive_rules':103,'updated_positive_rules':151,'persistent':31,'added':120,'removed':72}
    for k,v in expected.items():
        if int(ph.get(k,-999))!=v: errors.append(f'Unexpected phishing rule evolution {k}: {ph.get(k)}')
    rec=d.get('recovered_fn',{})
    if int(rec.get('n',-1))!=42: errors.append('Unexpected recovered FN count')
    if int(rec.get('with_at_least_one_new_exact_phishing_rule',-1))!=27: errors.append('Unexpected recovered FN exact-new-rule count')

if errors:
    print('VERIFY: FAIL')
    for e in errors: print(' -',e)
    sys.exit(1)
print('VERIFY: OK')
print('Temporal best sigma: 0.04')
print('Held-out 2025 DMC-AC-P accuracy: 0.7690802348')
print('Held-out 2025 phishing recall: 0.7612293144')
print('Rule evolution (phishing): 31 persistent / 120 emerging / 72 disappearing')
print('Recovered false negatives: 27/42 exactly covered by new rules')
