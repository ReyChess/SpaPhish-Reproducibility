import csv, re, statistics, os, json
from pathlib import Path
base=Path(__file__).resolve().parent
rows=[]
all_lens=[]
for f in range(1,11):
    path=base/f'ReglasDataset{f}.dat'
    pos=neg=0; ants=set(); pos_l=[]; neg_l=[]; bytes_=path.stat().st_size
    with path.open() as fh:
        for line in fh:
            p=line.split()
            if not p: continue
            n=int(p[0]); items=list(map(int,p[1:1+n])); consequent=items[-1]; ant=tuple(items[:-1]); L=len(ant)
            ants.add(ant)
            if consequent<0: neg+=1; neg_l.append(L)
            else: pos+=1; pos_l.append(L)
            all_lens.append(L)
    rows.append({'fold':f,'positive_rules':pos,'negative_rules':neg,'rule_entries':pos+neg,'unique_antecedents':len(ants),
                 'mean_antecedent_length':statistics.mean(pos_l+neg_l),'median_antecedent_length':statistics.median(pos_l+neg_l),
                 'min_antecedent_length':min(pos_l+neg_l),'max_antecedent_length':max(pos_l+neg_l),'rule_file_bytes':bytes_})
with (base/'rule_complexity_by_fold.csv').open('w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
# local parse AnalisisInstancias.dat from final classifier run
text=(base/'AnalisisInstancias.dat').read_text(errors='ignore').splitlines()
local=[]; exact_partial=None; counts=[]
cur=[]
for line in text:
    if line.startswith('M4d partial POS coverage used'):
        if cur: counts=cur
        cur=[]
        partial='YES' in line.split('|')[0]
        exact_partial=partial
    elif line.strip().startswith('[+] POS:'):
        if 'NINGUNA' in line: cur.append(0)
        else: cur.append(line.count('[netconf='))
    elif line.startswith('Clase ='):
        if exact_partial is not None:
            retained=sum(min(x,12) for x in cur)
            local.append({'partial_used':int(exact_partial),'covering_positive_rules':sum(cur),'retained_positive_rules':retained,'classes_with_coverage':sum(x>0 for x in cur)})
        cur=[]; exact_partial=None
with (base/'local_explanation_complexity.csv').open('w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=local[0].keys()); w.writeheader(); w.writerows(local)

def stats(vals):
    return {'mean':statistics.mean(vals),'median':statistics.median(vals),'min':min(vals),'max':max(vals)}
summary={
 'rules': {k:stats([r[k] for r in rows]) for k in ['positive_rules','negative_rules','rule_entries','unique_antecedents','mean_antecedent_length','rule_file_bytes']},
 'local': {k:stats([r[k] for r in local]) for k in ['covering_positive_rules','retained_positive_rules','classes_with_coverage']},
 'local_exact': {k:stats([r[k] for r in local if not r['partial_used']]) for k in ['covering_positive_rules','retained_positive_rules']},
 'local_partial': {k:stats([r[k] for r in local if r['partial_used']]) for k in ['covering_positive_rules','retained_positive_rules']},
 'n_instances':len(local),'n_partial':sum(r['partial_used'] for r in local)
}
# benchmark summaries
for name,file in [('classification','classifier_benchmark.csv'),('mining','mining_benchmark.csv')]:
    with (base/file).open() as fh: rr=list(csv.DictReader(fh))
    for x in rr:
        for k in ['wall_seconds','user_seconds','sys_seconds','max_rss_kb']:
            x[k]=float(x[k])
    summary[name]={k:stats([x[k] for x in rr]) for k in ['wall_seconds','user_seconds','sys_seconds','max_rss_kb']}
    if name=='mining':
        summary[name]['per_fold_wall']={str(f):stats([x['wall_seconds'] for x in rr if int(x['fold'])==f]) for f in range(1,11)}
(base/'complexity_efficiency_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
