from pathlib import Path
import pandas as pd, numpy as np, json, math
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, f1_score
root=Path(__file__).resolve().parent
variants=['technical','lexical','persuasion','technical_lexical','technical_persuasion','lexical_persuasion','full']
rows=[]; folds=[]; preds={}
for v in variants:
    d=root/v
    x=pd.read_csv(d/'m4d_veto_instance_log.csv')
    # unique current run
    x=x.drop_duplicates(['fold','inst_idx'],keep='last').sort_values(['fold','inst_idx'])
    preds[v]=x
    y=x.true_class; p=x.pred_class
    cm=confusion_matrix(y,p,labels=[77,78])
    pr,rc,f1,sup=precision_recall_fscore_support(y,p,labels=[77,78],zero_division=0)
    mine=pd.read_csv(d/'mining_summary.csv')
    rows.append(dict(variant=v,n=len(x),correct=int((y==p).sum()),accuracy=accuracy_score(y,p),macro_f1=f1_score(y,p,average='macro'),legit_precision=pr[0],legit_recall=rc[0],legit_f1=f1[0],phish_precision=pr[1],phish_recall=rc[1],phish_f1=f1[1],TN=int(cm[0,0]),FP=int(cm[0,1]),FN=int(cm[1,0]),TP=int(cm[1,1]),defaults=int(x.default_used.sum()),partial_uses=int(x.partial_used.sum()),avg_rule_entries=mine.rule_entries.mean(),avg_maximals=mine.maximals.mean(),total_mining_wall_sec=mine.wall_seconds.sum()))
    for fold,g in x.groupby('fold'):
        folds.append(dict(variant=v,fold=fold,n=len(g),correct=int((g.true_class==g.pred_class).sum()),accuracy=(g.true_class==g.pred_class).mean(),macro_f1=f1_score(g.true_class,g.pred_class,average='macro')))

summary=pd.DataFrame(rows).sort_values('accuracy',ascending=False)
summary.to_csv(root/'feature_ablation_summary.csv',index=False)
pd.DataFrame(folds).to_csv(root/'feature_ablation_folds.csv',index=False)
# Pairwise vs full
full=preds['full'][['fold','inst_idx','true_class','pred_class']].rename(columns={'pred_class':'pred_full'})
trans=[]
for v in variants[:-1]:
    a=preds[v][['fold','inst_idx','true_class','pred_class']].rename(columns={'pred_class':'pred_variant'})
    z=full.merge(a,on=['fold','inst_idx','true_class'])
    cf=z.pred_full.eq(z.true_class); cv=z.pred_variant.eq(z.true_class)
    full_wrong_var_right=int((~cf & cv).sum())
    full_right_var_wrong=int((cf & ~cv).sum())
    disc=full_wrong_var_right+full_right_var_wrong
    p=binomtest(min(full_wrong_var_right,full_right_var_wrong),disc,0.5).pvalue if disc else 1
    trans.append(dict(variant=v,full_wrong_variant_right=full_wrong_var_right,full_right_variant_wrong=full_right_var_wrong,discordant=disc,net_full_advantage=full_right_var_wrong-full_wrong_var_right,mcnemar_exact_p=p,predictions_different=int((z.pred_full!=z.pred_variant).sum())))
pd.DataFrame(trans).to_csv(root/'feature_ablation_vs_full.csv',index=False)
# all predictions
wide=full.copy()
for v in variants[:-1]:
    a=preds[v][['fold','inst_idx','pred_class']].rename(columns={'pred_class':f'pred_{v}'})
    wide=wide.merge(a,on=['fold','inst_idx'])
wide.to_csv(root/'feature_ablation_instance_predictions.csv',index=False)
print(summary.to_string(index=False))
print('\nVS FULL')
print(pd.DataFrame(trans).to_string(index=False))
