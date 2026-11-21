"""Check archived predictions, partitions, priors, rule replay and agreement."""
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
GROUP = ROOT / 'grouped_35_validation'
DMC = ROOT / 'dmc_training_priors_corrected'
ABLATION = ROOT / 'prior_lambda_ablation'
ANNOTATION = ROOT / 'annotation_agreement'
AUTO = ROOT / 'automatic_35_baselines'
EXPLANATION = ROOT / 'rule_level_explanations'


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def near(actual, expected, tolerance=1e-10):
    assert math.isclose(actual, float(expected), abs_tol=tolerance), (actual, expected)


def metrics(predictions):
    c = Counter(predictions)
    tn, fp, fn, tp = [c[key] for key in [('77', '77'), ('77', '78'), ('78', '77'), ('78', '78')]]
    n = tn + fp + fn + tp
    assert n == len(predictions)
    return dict(n=n, accuracy=(tn + tp) / n, tn=tn, fp=fp, fn=fn, tp=tp,
                macro_f1=(2*tn/(2*tn+fp+fn)+2*tp/(2*tp+fp+fn))/2,
                balanced_accuracy=(tn/(tn+fp)+tp/(tp+fn))/2,
                phishing_recall=tp/(tp+fn), phishing_precision=tp/(tp+fp),
                legitimate_recall=tn/(tn+fp), phishing_f1=2*tp/(2*tp+fp+fn))


def check_metrics(pairs, expected):
    result = metrics(pairs)
    for key, value in result.items():
        reported = expected.get(key, expected.get(key.upper()))
        if reported is not None:
            near(value, reported)
    return result


def key(row):
    return row['scenario'], row['instance_id']


def protocol(scenario):
    return 'grouped_cv' if scenario.startswith('grouped') else scenario[-4:]


def main():
    split = {r['instance_id']: r for r in rows(GROUP/'split_manifest.csv')}
    binary = {r['instance_id']: r for r in rows(REPO/'data/spaphish_binary_folds.csv')}
    inventory = rows(AUTO/'indicator_inventory.csv')
    codes = {r['item_name']: int(r['item_id']) for r in inventory if r['jisa_automatic']=='1'}
    assert len(inventory)==45 and len(codes)==35
    assert len(split)==1395 and Counter(r['class'] for r in split.values())=={'77':664,'78':731}
    assert sum(not r['year'] for r in split.values())==24
    folds = defaultdict(set)
    for i, r in split.items():
        folds[r['group_id']].add(r['group_cv_fold'])
        assert (r['class'],r['original_stratified_fold'])==(binary[i]['class'],binary[i]['fold'])
    assert len(folds)==1197 and all(len(f)==1 for f in folds.values())

    membership = defaultdict(dict)
    for r in rows(GROUP/'grouped_cv_train_test_manifest.csv'):
        s = f"grouped_fold_{int(r['held_out_fold']):02d}"
        i = r['instance_id']
        assert i not in membership[s]
        assert r['role']==('test' if split[i]['group_cv_fold']==r['held_out_fold'] else 'train')
        membership[s][i] = r['role']
    for r in rows(ROOT/'temporal_35_validation/temporal_train_test_manifest.csv'):
        s = 'temporal_'+r['protocol'].removeprefix('train_')
        i = r['instance_id']
        assert i not in membership[s]
        year = split[i]['year']
        expected = 'excluded' if not year or year>s[-4:] else ('test' if year==s[-4:] else 'train')
        assert r['role']==expected
        membership[s][i] = r['role']

    all_dmc = {key(r):r for r in rows(DMC/'all_dmc_predictions.csv')}
    all_cba = {key(r):r for r in rows(DMC/'reference_CBA/all_predictions.csv')}
    provenance = json.loads((DMC/'provenance.json').read_text())
    for name, digest in provenance['source_sha256'].items():
        source=(REPO/'src'/name).read_bytes().replace(b'\r\n',b'\n')
        assert digest in {hashlib.sha256(source).hexdigest(),
                          hashlib.sha256(source.replace(b'\n',b'\r\n')).hexdigest()}
    assert len(all_dmc)==len(all_cba)==2201
    for entry in provenance['scenarios']:
        scenario=entry['scenario']
        folder = DMC/'scenarios'/scenario
        partition = membership[scenario]
        assert partition.keys()==split.keys()
        train = Counter(split[i]['class'] for i in partition if partition[i]=='train')
        counts = dict(line.split() for line in (folder/'Classes.dat').read_text().splitlines())
        assert train=={k:int(v) for k,v in counts.items()}
        for filename, field in [('ReglasDataset1.dat','rules_sha256'),
                                ('m4d_veto_instance_log.csv','native_log_sha256'),
                                ('predictions.csv','prediction_sha256')]:
            assert hashlib.sha256((folder/filename).read_bytes()).hexdigest()==entry[field]
        predictions = rows(folder/'predictions.csv')
        assert len(predictions)==entry['test_n']
        assert {r['instance_id'] for r in predictions}=={i for i in partition if partition[i]=='test'}
        native=rows(folder/'m4d_veto_instance_log.csv')
        assert len(native)==10*len(predictions)
        for r in native:
            p=predictions[int(r['inst_idx'])-1]
            assert (p['true_class'],p['predicted_class'])==(r['true_class'],r['pred_class'])
            assert r['neg_evaluated']=='0'
        for p in predictions:
            assert p==all_dmc[key(p)] and p['true_class']==all_cba[key(p)]['true_class']==split[p['instance_id']]['class']

    pool = defaultdict(list)
    for model, source in [('DMC-AC-P',all_dmc),('CBA',all_cba)]:
        for (scenario,i), r in source.items():
            pool[protocol(scenario),model].append((r['true_class'],r['predicted_class']))
    sklearn = defaultdict(list)
    ids = defaultdict(set)
    for r in rows(GROUP/'oof_and_temporal_predictions.csv'):
        p = protocol(r['protocol'])
        i = r['instance_id']
        scenario = f"grouped_fold_{int(r['fold']):02d}" if p=='grouped_cv' else r['protocol'].replace('train_','')
        assert membership[scenario][i]=='test' and r['true_class']==split[i]['class']
        assert i not in ids[p,r['model']]
        ids[p,r['model']].add(i)
        pair=(r['true_class'],r['predicted_class'])
        sklearn[r['protocol'],r['model']].append(pair)
        pool[p,r['model']].append(pair)
    for r in rows(GROUP/'metrics_summary.csv'):
        check_metrics(sklearn[r['protocol'],r['model']],r)
    verified = rows(ROOT/'verified_robustness_metrics.csv')
    assert len(verified)==len(pool)==15
    for r in verified:
        p,m = protocol(r['protocol']),r['model']
        assert len(pool[p,m])=={'grouped_cv':1395,'2024':295,'2025':511}[p]
        print(p,m,f"{check_metrics(pool[p,m],r)['accuracy']:.2%}")

    oof = rows(AUTO/'aligned_dmc_cba_oof.csv')
    assert len(oof)==len({r['instance_id'] for r in oof})==1395
    for r in oof:
        s=split[r['instance_id']]
        assert (r['fold'],r['class'],r['neg_evaluated'])==(s['original_stratified_fold'],s['class'],'0')
    for model, expected in [('dmc',1187),('cba',1177)]:
        result=metrics([(r['class'],r[f'{model}_prediction']) for r in oof])
        assert result['tp']+result['tn']==expected
        print('stratified',model,f"{result['accuracy']:.2%}")

    counterfactual = rows(ABLATION/'counterfactual_instance_predictions.csv')
    assert len(counterfactual)==len({key(r) for r in counterfactual})==2201
    for r in counterfactual:
        assert r['native_pred']==r['pred_lambda_0p15']==all_dmc[key(r)]['predicted_class']
        assert r['true_class']==all_dmc[key(r)]['true_class']
    tables=rows(ABLATION/'lambda_sensitivity_metrics.csv')
    assert len(tables)==42
    for r in tables:
        p='grouped_cv' if r['scenario']=='grouped_10fold' else r['scenario'][-4:]
        col='pred_lambda_'+format(float(r['lambda_prior']),'g').replace('.','p')
        selected=[q for q in counterfactual if protocol(q['scenario'])==p]
        check_metrics([(q['true_class'],q[col]) for q in selected],r)
        flips=Counter((q['pred_lambda_0p15']==q['true_class'],q[col]==q['true_class']) for q in selected)
        assert (flips[False,True],flips[True,False])==(int(r['changed_wrong_to_right']),int(r['changed_right_to_wrong']))
    year_2025=[r for r in counterfactual if protocol(r['scenario'])=='2025']
    assert sum(r['true_class']==r['pred_lambda_0']!=r['native_pred'] for r in year_2025)==90
    assert sum(r['true_class']==r['native_pred']!=r['pred_lambda_0'] for r in year_2025)==15

    votes=rows(ANNOTATION/'affirmative_vote_counts.csv')
    assert len(votes)==len({r['instance_id'] for r in votes})==1395
    for r in rows(ANNOTATION/'annotator_agreement_verified.csv'):
        category=r['category']
        counts=[int(v[category]) for v in votes]
        for v,c in zip(votes,counts,strict=True):
            b=binary[v['instance_id']]
            assert c in range(4)
            assert int(b[category.upper()+'_YES'])==(c>=2)
            assert int(b[category.upper()+'_STRONG_3_ANNOTATORS'])==(c==3)
        p=sum(counts)/(3*len(counts))
        agreement=sum((c*(c-1)+(3-c)*(2-c))/6 for c in counts)/len(counts)
        chance=p*p+(1-p)**2
        near((agreement-chance)/(1-chance),r['fleiss_kappa_binary'])

    folder=DMC/'scenarios/temporal_through_2024_test_2025'
    rules=[]
    for pos,line in enumerate((folder/'ReglasDataset1.dat').read_text().splitlines(),1):
        values=line.split()
        n=int(values[0])
        rules.append((pos,set(map(int,values[1:n])),int(values[n]),float(values[-1])))
    trace=rows(EXPLANATION/'real_2025_rule_by_rule_traces.csv')
    predictions=rows(folder/'predictions.csv')
    native=rows(folder/'m4d_veto_instance_log.csv')
    for r in rows(EXPLANATION/'real_2025_TP_FN_reconstructed_scores.csv'):
        i=r['instance_id']
        position=int(r['test_position'])-1
        assert predictions[position]['instance_id']==i
        items={code for name,code in codes.items() if binary[i][name]=='1'}
        exact=[x for x in rules if x[2]>0 and x[1]<=items]
        eligible=exact or [x for x in rules if x[2]>0 and len(x[1]-items)==1]
        assert len(eligible)==int(r['eligible_rule_count'])
        mu=sum(x[3] for x in eligible)/len(eligible)
        near(mu,native[position]['mu0_pos'],1e-9)
        adjusted={}
        for c in (77,78):
            found=[x for x in eligible if x[2]==c]
            stored=[x for x in trace if x['instance_id']==i and int(x['class'])==c]
            assert len(found)==len(stored)
            for j,(rule,t) in enumerate(zip(found,stored,strict=True),1):
                assert rule[0]==int(t['rule_line']) and j==int(t['rank_in_class'])
                near(rule[3],t['netconf_file'])
                near(1/j if j<=12 else 0,t['weight'])
            top=found[:12]
            q=sum(x[3]/j for j,x in enumerate(top,1))/sum(1/j for j in range(1,len(top)+1))
            score=(len(top)*q+2*mu)/(len(top)+2)
            near(score,r[f'score_{c}'])
            adjusted[c]=score+0.15*math.log(float(r[f'prior_{c}']))
            near(adjusted[c],r[f'adjusted_score_{c}'])
        assert str(max(adjusted,key=adjusted.get))==r['predicted_class']==native[position]['pred_class']
    print('JISA evidence checks passed')


if __name__=='__main__':
    main()
