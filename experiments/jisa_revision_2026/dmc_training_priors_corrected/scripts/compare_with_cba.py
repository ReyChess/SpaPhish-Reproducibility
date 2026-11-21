#!/usr/bin/env python3
"""Pair corrected genuine native DMC predictions with frozen audited CBA output."""
import csv,math,sys
from collections import Counter,defaultdict
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def read(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def save(p,records):
    with p.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
def mcnemar_exact(b,c):
    n=b+c
    if n==0:return 1.0
    k=min(b,c)
    # P(X <= k) for Binomial(n, .5), with exact integer binomial coefficients.
    return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/2**n)
def main():
    d=read(P/'outputs/all_dmc_predictions.csv'); c=read(P/'reference_CBA/all_predictions.csv')
    ref={(x['scenario'],x['instance_id']):x for x in c}
    if len(ref)!=len(c):raise AssertionError('Duplicate CBA keys')
    if len({(x['scenario'],x['instance_id']) for x in d})!=len(d):raise AssertionError('Duplicate DMC keys')
    paired=[]
    for r in d:
        key=r['scenario'],r['instance_id']
        if key not in ref:raise AssertionError(f'Missing CBA key {key}')
        cc=ref[key]
        if str(r['true_class'])!=str(cc['true_class']):raise AssertionError(f'Class mismatch {key}')
        paired.append({'scenario':r['scenario'],'instance_id':r['instance_id'],'true_class':r['true_class'],'dmc_predicted':r['predicted_class'],'cba_predicted':cc['predicted_class'],'dmc_correct':int(r['true_class']==r['predicted_class']),'cba_correct':int(cc['true_class']==cc['predicted_class'])})
    save(P/'outputs/aligned_dmc_cba_predictions.csv',paired)
    scenarios=['GROUPED_ALL']+sorted(set(x['scenario'] for x in paired))
    out=[]
    for sc in scenarios:
        subset=[x for x in paired if (x['scenario'].startswith('grouped_') if sc=='GROUPED_ALL' else x['scenario']==sc)]
        if not subset:continue
        n=len(subset); dacc=sum(x['dmc_correct'] for x in subset);cacc=sum(x['cba_correct'] for x in subset)
        only_d=sum(x['dmc_correct']==1 and x['cba_correct']==0 for x in subset)
        only_c=sum(x['dmc_correct']==0 and x['cba_correct']==1 for x in subset)
        out.append({'scenario':sc,'n':n,'dmc_correct':dacc,'cba_correct':cacc,'dmc_accuracy':dacc/n,'cba_accuracy':cacc/n,'difference':(dacc-cacc)/n,'discordant_dmc_only':only_d,'discordant_cba_only':only_c,'mcnemar_exact_p':mcnemar_exact(only_d,only_c)})
    save(P/'outputs/paired_comparisons.csv',out)
    for row in out:print(row)
if __name__=='__main__':main()
