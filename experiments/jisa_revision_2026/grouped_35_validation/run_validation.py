import pandas as pd, numpy as np, json
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix, balanced_accuracy_score
import argparse
args = argparse.ArgumentParser()
args.add_argument('output', type=Path)
output = args.parse_args().output
output.mkdir(parents=True, exist_ok=True)
ROOT=Path(__file__).resolve().parent
A=pd.read_csv(ROOT/'split_manifest.csv').rename(columns={'group_id':'template_group_id_095','group_cv_fold':'group_cv_fold_10'})
B=pd.read_csv(ROOT.parents[2]/'data/spaphish_binary_folds.csv')
assert A.instance_id.equals(B.instance_id)
assert len(A)==len(B)==1395
exclude={'AUTHORITY_YES','SOCIAL_PROOF_YES','LIKING_SIMILARITY_DECEPTION_YES','COMMITMENT_INTEGRITY_RECIPROCATION_YES','DISTRACTION_YES','AUTHORITY_STRONG_3_ANNOTATORS','SOCIAL_PROOF_STRONG_3_ANNOTATORS','LIKING_SIMILARITY_DECEPTION_STRONG_3_ANNOTATORS','COMMITMENT_INTEGRITY_RECIPROCATION_STRONG_3_ANNOTATORS','DISTRACTION_STRONG_3_ANNOTATORS'}
features=[c for c in B.columns if c not in ('instance_id','class','fold') and c not in exclude]
assert len(features)==35 and len(exclude)==10
assert A['class'].equals(B['class'])
assert A.groupby('template_group_id_095').group_cv_fold_10.nunique().max()==1
X=B[features].to_numpy(dtype=np.float64); y=(B['class']==78).to_numpy(dtype=int)
year=A.year
models={'RF':lambda:RandomForestClassifier(n_estimators=500,random_state=42,n_jobs=-1), 'LR':lambda:LogisticRegression(max_iter=2000,random_state=42), 'DT':lambda:DecisionTreeClassifier(random_state=42)}
def metrics(y_true,y_pred):
 cm=confusion_matrix(y_true,y_pred,labels=[0,1]);return {'n':len(y_true),'accuracy':accuracy_score(y_true,y_pred),'balanced_accuracy':balanced_accuracy_score(y_true,y_pred),'macro_f1':f1_score(y_true,y_pred,average='macro',zero_division=0),'phishing_precision':precision_score(y_true,y_pred,zero_division=0),'phishing_recall':recall_score(y_true,y_pred,zero_division=0),'phishing_f1':f1_score(y_true,y_pred,zero_division=0),'TN':int(cm[0,0]),'FP':int(cm[0,1]),'FN':int(cm[1,0]),'TP':int(cm[1,1])}
summary=[];folds=[];preds=[]
for name, factory in models.items():
 outputs=np.full(len(A),-1,dtype=int)
 for f in sorted(A.group_cv_fold_10.unique()):
  test=np.flatnonzero(A.group_cv_fold_10.to_numpy()==f);train=np.flatnonzero(A.group_cv_fold_10.to_numpy()!=f)
  clf=factory();clf.fit(X[train],y[train]);out=clf.predict(X[test]);outputs[test]=out
  folds.append({'protocol':'grouped_cv','model':name,'fold':int(f),**metrics(y[test],out)})
  for idx,p in zip(test,out):preds.append({'protocol':'grouped_cv','model':name,'instance_id':int(B.instance_id.iloc[idx]),'fold':int(f),'true_class':int(B['class'].iloc[idx]),'predicted_class':77+int(p)})
 assert (outputs>=0).all()
 summary.append({'protocol':'grouped_cv','model':name,'train_n':'9 folds','test_n':len(A),**metrics(y,outputs)})
 for cutoff, test_year in [(2023,2024),(2024,2025)]:
  train=np.flatnonzero((year<=cutoff).to_numpy());test=np.flatnonzero((year==test_year).to_numpy())
  assert len(train) and len(test)
  clf=factory();clf.fit(X[train],y[train]);out=clf.predict(X[test]);protocol=f'temporal_train_through_{cutoff}_test_{test_year}'
  summary.append({'protocol':protocol,'model':name,'train_n':len(train),'test_n':len(test),**metrics(y[test],out)})
  for idx,p in zip(test,out):preds.append({'protocol':protocol,'model':name,'instance_id':int(B.instance_id.iloc[idx]),'fold':'','true_class':int(B['class'].iloc[idx]),'predicted_class':77+int(p)})
pd.DataFrame(summary).to_csv(output/'metrics_summary.csv',index=False)
pd.DataFrame(folds).to_csv(output/'grouped_cv_fold_metrics.csv',index=False)
pd.DataFrame(preds).to_csv(output/'oof_and_temporal_predictions.csv',index=False)
(output/'features_35.json').write_text(json.dumps(features,indent=2))
print(pd.DataFrame(summary).to_string(index=False,float_format=lambda a:f'{a:.5f}'))
print('year counts',year.value_counts(dropna=False).to_dict())
