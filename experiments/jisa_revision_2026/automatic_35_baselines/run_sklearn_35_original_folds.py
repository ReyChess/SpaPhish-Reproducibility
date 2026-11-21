#!/usr/bin/env python3
"""Fixed-parameter sklearn checks, SpaPhish original outer folds (not nested)."""
from pathlib import Path
import argparse, hashlib, json, platform
import numpy as np, pandas as pd, sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, f1_score, precision_score, recall_score
MANUAL={
'AUTHORITY_YES','AUTHORITY_STRONG_3_ANNOTATORS','LIKING_SIMILARITY_DECEPTION_YES',
'LIKING_SIMILARITY_DECEPTION_STRONG_3_ANNOTATORS','DISTRACTION_YES','DISTRACTION_STRONG_3_ANNOTATORS',
'COMMITMENT_INTEGRITY_RECIPROCATION_YES','COMMITMENT_INTEGRITY_RECIPROCATION_STRONG_3_ANNOTATORS',
'SOCIAL_PROOF_YES','SOCIAL_PROOF_STRONG_3_ANNOTATORS'}

def models():
 return {'LogisticRegression': lambda: LogisticRegression(C=1.0,max_iter=2000,solver='liblinear',random_state=42),
         'DecisionTree':lambda:DecisionTreeClassifier(random_state=42),
         'RandomForest':lambda:RandomForestClassifier(n_estimators=300,random_state=42,n_jobs=1)}

def calc(yt,yp):
 tn,fp,fn,tp=confusion_matrix(yt,yp,labels=[77,78]).ravel().astype(int)
 return dict(n=len(yt),correct=int(sum(yt==yp)),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp),accuracy=accuracy_score(yt,yp),macro_f1=f1_score(yt,yp,average='macro',labels=[77,78]),phishing_f1=f1_score(yt,yp,pos_label=78),phishing_precision=precision_score(yt,yp,pos_label=78),phishing_recall=recall_score(yt,yp,pos_label=78))

def main():
 a=argparse.ArgumentParser();a.add_argument('--input',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args()
 df=pd.read_csv(args.input);args.out.mkdir(exist_ok=True,parents=True)
 assert df.shape==(1395,48),df.shape
 assert df.instance_id.is_unique and set(df['class'])=={77,78} and set(df.fold)==set(range(1,11))
 features=[x for x in df if x not in {'instance_id','class','fold'}]; assert len(features)==45 and MANUAL.issubset(features)
 features=[x for x in features if x not in MANUAL];assert len(features)==35
 assert np.isin(df[features].to_numpy(),[0,1]).all()
 X=df[features].to_numpy(); y=df['class'].to_numpy();fold=df.fold.to_numpy()
 preds=[];summ=[]
 for model,factory in models().items():
  all_pred=np.zeros(len(y),dtype=int)
  for f in range(1,11):
   tr=fold!=f;te=fold==f;obj=factory();obj.fit(X[tr],y[tr]); p=obj.predict(X[te]);all_pred[te]=p
   summ.append(dict(model=model,fold=f,**calc(y[te],p)))
   preds.extend(dict(instance_id=int(row.instance_id),fold=int(f),true_class=int(row['class']),predicted_class=int(pp),model=model) for (_,row),pp in zip(df.loc[te].iterrows(),p))
  assert np.isin(all_pred,[77,78]).all()
  summ.append(dict(model=model,fold='pooled',**calc(y,all_pred)))
 pd.DataFrame(preds).to_csv(args.out/'sklearn_35_oof_predictions.csv',index=False)
 pd.DataFrame(summ).to_csv(args.out/'sklearn_35_fold_metrics.csv',index=False)
 manifest=dict(source_input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),n_instances=1395,
  feature_count=35,features=features,excluded_manual=sorted(MANUAL),folds='Original SpaPhish 10 stratified folds, not template-grouped',
  classifier_settings={'LogisticRegression':{'C':1,'solver':'liblinear','max_iter':2000,'random_state':42},'DecisionTree':{'random_state':42},'RandomForest':{'n_estimators':300,'random_state':42,'n_jobs':1}},
  tuning='None, fixed hyperparameters, exploratory external validation; do not equate with tuned 45-feature benchmark',
  provenance='Original 11 lexical feature design freeze date not established',
  python_version=platform.python_version(),sklearn_version=sklearn.__version__,pandas_version=pd.__version__,numpy_version=np.__version__)
 (args.out/'sklearn_35_manifest.json').write_text(json.dumps(manifest,indent=2))
 print(pd.DataFrame(summ).query('fold=="pooled"').to_string(index=False))
if __name__=='__main__':main()
