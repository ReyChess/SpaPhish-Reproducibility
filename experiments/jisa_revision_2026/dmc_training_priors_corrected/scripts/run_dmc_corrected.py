#!/usr/bin/env python3
"""DMC-AC-P with training-only priors across grouped CV and two retrospective temporal holdouts.
Uses the ORIGINAL historical C/C++ sources (no reimplementation of predictor).
Historical classifier is hard-coded for 10 folds and one Classes.dat. We run
one process per scenario, replicating ONLY that scenario's test/rules ten times,
then KEEP only the first fold's native instance predictions. This avoids a
source-level semantic modification and gives each scenario training-only priors.
"""
import argparse,csv,hashlib,json,os,re,shutil,subprocess,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCENARIOS=[f'grouped_fold_{i:02d}' for i in range(1,11)]+['temporal_through_2023_test_2024','temporal_through_2024_test_2025']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def run(cmd,cwd=None,output=None):
    p=subprocess.run([str(x) for x in cmd],cwd=cwd,text=True,capture_output=True,check=False)
    if output:output.write_text(f'COMMAND {cmd}\nRETURN CODE {p.returncode}\nSTDOUT\n{p.stdout}\nSTDERR\n{p.stderr}',encoding='utf8')
    if p.returncode:raise RuntimeError(f'Failed: {cmd}; log={output}')
    return p

def metrics(items):
    cm=Counter((str(x['true_class']),str(x['predicted_class'])) for x in items)
    tn,fp,fn,tp=[cm[k] for k in [('77','77'),('77','78'),('78','77'),('78','78')]]
    n=tn+fp+fn+tp
    return {'n':n,'correct':tn+tp,'accuracy':(tn+tp)/n,'macro_f1':(2*tn/(2*tn+fp+fn)+2*tp/(2*tp+fp+fn))/2,'tn':tn,'fp':fp,'fn':fn,'tp':tp}

def write_csv(path,arr):
    if not arr:raise ValueError('Empty output')
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(arr[0]));w.writeheader();w.writerows(arr)

def verify_inputs():
    names=[]
    for scenario in SCENARIOS:
        d=ROOT/'prepared'/scenario
        train=d/'train.dat';test=d/'test.dat';cls=d/'Classes.dat';ids=d/'test_ids.csv'
        for p in [train,test,cls,ids]:
            if not p.is_file():raise FileNotFoundError(p)
        tr=[int(line.split()[-1]) for line in train.read_text().splitlines()]
        te=[int(line.split()[-1]) for line in test.read_text().splitlines()]
        counts=Counter(tr)
        expected={int(a):int(b) for a,b in [line.split() for line in cls.read_text().splitlines()]}
        assert set(counts)=={77,78} and counts==expected,(scenario,counts,expected)
        assert len(te)==len(rows(ids)),scenario
        assert [int(r['class']) for r in rows(ids)]==te,scenario
        assert len(tr)>len(te)>0
        names.append({'scenario':scenario,'train_n':len(tr),'test_n':len(te),'train_77':counts[77],'train_78':counts[78],'test_77':te.count(77),'test_78':te.count(78)})
    return names

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,help='Local checkout containing src/mfi_ct_spaphish_historical.c and src/dmc_ac_spaphish_historical.cpp')
    ap.add_argument('--sigma',default='0.04')
    ap.add_argument('--verify-only',action='store_true')
    ap.add_argument('--scenario',choices=SCENARIOS,action='append')
    args=ap.parse_args()
    preflight=verify_inputs();print('PREPARED SCENARIOS VERIFIED:',len(preflight))
    if args.verify_only:return 0
    if not args.repo:ap.error('--repo is required for real execution')
    src=args.repo.resolve()/'src'
    miner_src=src/'mfi_ct_spaphish_historical.c'; cls_src=src/'dmc_ac_spaphish_historical.cpp'
    for p in [miner_src,cls_src]:
        if not p.is_file():raise FileNotFoundError(p)
    root=ROOT/'outputs';root.mkdir(exist_ok=True)
    build=root/'build';build.mkdir(exist_ok=True)
    exe='.exe' if os.name=='nt' else ''
    miner=build/('miner'+exe);classifier=build/('classifier_pos_only'+exe)
    run([os.getenv('CC','gcc'),'-O3','-msse4.2',miner_src,'-lm','-o',miner],output=build/'compile_miner.log')
    run([os.getenv('CXX','g++'),'-O3','-DM4_USE_NEGATIVES_FOR_TIEBREAK=0',cls_src,'-lm','-o',classifier],output=build/'compile_classifier.log')
    chosen=args.scenario or SCENARIOS
    all_preds=[];summary=[];manifest=[]
    for scenario in chosen:
        d=ROOT/'prepared'/scenario;work=root/scenario;work.mkdir(exist_ok=True)
        counts=(d/'Classes.dat').read_text().strip();tr=(d/'train.dat');te=(d/'test.dat')
        (work/'Classes.dat').write_text(counts+'\n')
        # Actual source miner: regenerate rules only from this scenario's TRAIN data.
        run([miner,tr,args.sigma,work/'ReglasDataset1.dat'],output=work/'miner.log')
        rule=work/'ReglasDataset1.dat'
        if not rule.exists() or not rule.stat().st_size:raise RuntimeError(f'No rules: {scenario}')
        for k in range(1,11):
            shutil.copy2(te,work/f'{k}.dat')
            if k!=1:shutil.copy2(rule,work/f'ReglasDataset{k}.dat')
        # The historical executable requires 10 folds; this run repeats ONE
        # untouched test fold 10x, then we retain ONLY fold 1 (no pseudoreplication).
        run([classifier,'native_result.txt'],cwd=work,output=work/'classifier.log')
        log=work/'m4d_veto_instance_log.csv'
        if not log.exists():raise RuntimeError(f'Native per-instance log missing {scenario}')
        trace=rows(log)
        assert len(trace)==10*len(rows(d/'test_ids.csv')),(scenario,len(trace))
        first=[x for x in trace if int(x['fold'])==1]
        assert len(first)==len(rows(d/'test_ids.csv'))
        first.sort(key=lambda x:int(x['inst_idx']))
        ids=rows(d/'test_ids.csv')
        actual=[]
        for idx,(r,t) in enumerate(zip(first,ids),start=1):
            assert int(r['inst_idx'])==idx,(scenario,idx,r['inst_idx'])
            assert str(r['true_class'])==str(t['class']),(scenario,idx,'test-order mismatch')
            assert str(r['neg_evaluated']) in ('0','0.0'),('NEGATIVE EVIDENCE WAS USED',scenario,idx)
            pred={'scenario':scenario,'instance_id':t['instance_id'],'true_class':t['class'],'predicted_class':r['pred_class'],'correct':int(t['class']==r['pred_class'])}
            actual.append(pred)
        vals=metrics(actual)
        assert vals['n']==len(ids)
        write_csv(work/'predictions.csv',actual)
        all_preds.extend(actual);summary.append({'scenario':scenario,**vals})
        # Training-only counts are stored and validated for each scenario.
        manifest.append({'scenario':scenario,'train_counts':counts,'test_n':len(ids),'train_sha256':sha(tr),'test_sha256':sha(te),'rules_sha256':sha(rule),'native_log_sha256':sha(log),'prediction_sha256':sha(work/'predictions.csv')})
        print(scenario, f"n={vals['n']}",f"accuracy={vals['accuracy']:.6f}",f"macro_F1={vals['macro_f1']:.6f}")
    write_csv(root/'all_dmc_predictions.csv',all_preds)
    write_csv(root/'scenario_metrics.csv',summary)
    (root/'provenance.json').write_text(json.dumps({'protocol':'12 scenarios, original positive-only classifier, one isolated native run per scenario','sigma':args.sigma,'negative_tiebreak_enabled':False,'source_sha256':{p.name:sha(p) for p in [miner_src,cls_src]},'scenarios':manifest},indent=2))
    if all(x in chosen for x in SCENARIOS[:10]):
        g=[x for x in all_preds if x['scenario'].startswith('grouped')]
        assert len(g)==1395 and len({x['instance_id'] for x in g})==1395
        print('GROUPED POOLED:',metrics(g))
    print('SUCCESS: genuine native results written to',root)
    return 0
if __name__=='__main__':sys.exit(main())
