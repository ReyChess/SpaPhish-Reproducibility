import json, math, csv
from pathlib import Path
import pandas as pd
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
OUT = parser.parse_args().output
OUT.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
RUN = root/'dmc_training_priors_corrected/scenarios'
binary = pd.read_csv(root.parents[1]/'data/spaphish_binary_folds.csv').set_index('instance_id')
inventory = pd.read_csv(root/'automatic_35_baselines/indicator_inventory.csv')
dictionary = dict(zip(inventory.loc[inventory.jisa_automatic==1, 'item_name'],
                      inventory.loc[inventory.jisa_automatic==1, 'item_id']))
pred = []
diagnostics = []
for scenario in sorted(p.name for p in RUN.iterdir() if p.is_dir()):
    folder=RUN/scenario
    assert folder.is_dir(), folder
    orig=pd.read_csv(folder/'predictions.csv'); log=pd.read_csv(folder/'m4d_veto_instance_log.csv'); log=log[log.fold==1];assert len(orig)==len(log)
    counts={int(x.split()[0]):int(x.split()[1]) for x in (folder/'Classes.dat').read_text().splitlines() if x.strip()}; N=sum(counts.values());priors={k:v/N for k,v in counts.items()}
    rules=[]
    for line in (folder/'ReglasDataset1.dat').read_text().splitlines():
        v=line.split(); n=int(v[0]); assert len(v)==n+5; cls=int(v[n]);
        if cls>0: rules.append((set(map(int,v[1:n])),cls,float(v[-1])))
    for j,o in enumerate(orig.itertuples(index=False)):
        items={code for name,code in dictionary.items() if binary.loc[o.instance_id,name]==1}
        matching=[(cls,nc) for ant,cls,nc in rules if ant.issubset(items)]
        partial=not matching
        if partial: matching=[(cls,nc) for ant,cls,nc in rules if len(ant-items)==1]
        mu=sum(nc for _,nc in matching)/len(matching) if matching else 0
        bycls={c:[nc for rc,nc in matching if rc==c] for c in (77,78)}
        score={}
        for c in (77,78):
            vals=bycls[c][:12];k=len(vals)
            if k:
                w=[1/(i+1) for i in range(k)];q=sum(a*b for a,b in zip(vals,w))/sum(w)
                score[c]=(q*k+2*mu)/(k+2)
        lrow=log.iloc[j]
        def choose(lam):
            if not score:return max(priors,key=priors.get)
            best=max(score.values());tied=[c for c in score if best-score[c]<=.005]
            cand=tied if len(tied)>1 else list(score)
            return max(cand, key=lambda c:(score[c]+lam*math.log(priors[c]),-c))
        predicted=choose(.15)
        err=(predicted!=o.predicted_class)
        if abs(mu-lrow.mu0_pos)>1e-5 or abs(max(score.values())-lrow.best_pos)>1e-5 if score else False:
            diagnostics.append((scenario,o.instance_id,'score-mismatch',mu,lrow.mu0_pos,max(score.values()),lrow.best_pos))
        if err: diagnostics.append((scenario,o.instance_id,'prediction-mismatch',predicted,o.predicted_class,score,priors))
        row=dict(scenario=scenario,instance_id=int(o.instance_id),true_class=int(o.true_class),native_pred=int(o.predicted_class),coverage=('partial' if partial else 'exact') if score else 'default',n_pos_rules=len(matching),score_77=score.get(77,float('nan')),score_78=score.get(78,float('nan')),prior_77=priors[77],prior_78=priors[78],raw_pos_winner=max(score,key=lambda c:(score[c],-c)) if score else None)
        for lam in (0,.01,.02,.03,.04,.05,.06,.08,.10,.12,.15,.20,.25,.30):row['pred_lambda_'+str(lam).replace('.','p')]=choose(lam)
        pred.append(row)
print('rows',len(pred),'diagnostics',len(diagnostics));print('diagnostics examples', diagnostics[:8]);pd.DataFrame(pred).to_csv(OUT/'counterfactual_instance_predictions.csv',index=False);(OUT/'diagnostics.json').write_text(json.dumps(diagnostics[:200],indent=2,default=str))

def confusion_matrix(y, yp, labels):
    import numpy as np
    return np.array([[int(((y == a) & (yp == b)).sum()) for b in labels] for a in labels])
def accuracy_score(y, yp):
    return (y == yp).mean()
def precision_score(y, yp, pos_label, zero_division=0):
    denom = (yp == pos_label).sum()
    return ((y == pos_label) & (yp == pos_label)).sum() / denom if denom else zero_division
def recall_score(y, yp, pos_label):
    return ((y == pos_label) & (yp == pos_label)).sum() / (y == pos_label).sum()
def f1_score(y, yp, average):
    assert average == "macro"
    return sum(2 * ((y == c) & (yp == c)).sum() / ((y == c).sum() + (yp == c).sum()) for c in (77, 78)) / 2

D=pd.DataFrame(pred); summary=[]; flips=[]
for scenario,df in [('grouped_10fold',D[D.scenario.str.startswith('grouped')]),('test_2024',D[D.scenario.str.contains('2024$')]),('test_2025',D[D.scenario.str.contains('2025$')])]:
    y=df.true_class
    ref=df.native_pred
    for lam in (0,.01,.02,.03,.04,.05,.06,.08,.10,.12,.15,.20,.25,.30):
        col='pred_lambda_'+str(lam).replace('.','p'); yp=df[col]; tn,fp,fn,tp=confusion_matrix(y,yp,labels=[77,78]).ravel()
        summary.append(dict(scenario=scenario,lambda_prior=lam,n=len(df),accuracy=accuracy_score(y,yp),macro_f1=f1_score(y,yp,average='macro'),phishing_recall=recall_score(y,yp,pos_label=78),phishing_precision=precision_score(y,yp,pos_label=78,zero_division=0),legitimate_recall=recall_score(y,yp,pos_label=77),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp),changes_vs_015=int((yp!=ref).sum()),changed_wrong_to_right=int(((yp!=ref)&(yp==y)).sum()),changed_right_to_wrong=int(((yp!=ref)&(yp!=y)).sum())))
    for ix,row in df.iterrows():
        y=int(row.true_class);old=int(row.native_pred); no=int(row['pred_lambda_0']);
        if old!=no: flips.append(dict(scenario=row.scenario,instance_id=row.instance_id,true_class=y,pred_015=old,pred_0=no,prior_helped=int(old==y),prior_hurt=int(no==y),raw_pos_winner=row.raw_pos_winner,score_77=row.score_77,score_78=row.score_78,prior_77=row.prior_77,prior_78=row.prior_78,coverage=row.coverage))
S=pd.DataFrame(summary);S.to_csv(OUT/'lambda_sensitivity_metrics.csv',index=False);pd.DataFrame(flips).to_csv(OUT/'flipped_instances_lambda_015_vs_0.csv',index=False)
print(S[S.lambda_prior.isin([0,.05,.1,.15])].to_string(index=False)); print('flips',len(flips));print('change categories',pd.DataFrame(flips).groupby('scenario')[['prior_helped','prior_hurt']].sum().to_string())