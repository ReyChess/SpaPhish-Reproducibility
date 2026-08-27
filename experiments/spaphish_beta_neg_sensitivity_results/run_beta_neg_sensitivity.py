from pathlib import Path
import re, subprocess, os, shutil, itertools
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from scipy.stats import binomtest

here=Path(__file__).resolve().parent
package_root=here.parent.parent
base=package_root/'spaphish_complexity_efficiency_results'/'complexity_efficiency'
out=here/'beta_neg_sensitivity'
out.mkdir(exist_ok=True)
source=(base/'main.cpp').read_text()
# remove macro blocks and replace tokens with globals
blocks={
'STABLE_TIE_EPS': r'#ifndef STABLE_TIE_EPS\n(?:.|\n)*?#endif',
'M4_NEG_VETO_MIN': r'#ifndef M4_NEG_VETO_MIN\n(?:.|\n)*?#endif',
'M4_NEG_VETO_DIFF': r'#ifndef M4_NEG_VETO_DIFF\n(?:.|\n)*?#endif',
'STABLE_BETA_NEG': r'#ifndef STABLE_BETA_NEG\n(?:.|\n)*?#endif',
}
for name,pat in blocks.items():
    source,n=re.subn(pat,'',source,count=1)
    if n!=1: raise RuntimeError(f'block {name} not found')
source=(source.replace('STABLE_TIE_EPS','g_tie_eps')
              .replace('M4_NEG_VETO_MIN','g_veto_min')
              .replace('M4_NEG_VETO_DIFF','g_veto_diff')
              .replace('STABLE_BETA_NEG','g_beta_neg'))
insert='''\nstatic double g_tie_eps = 0.03;\nstatic double g_veto_min = 0.05;\nstatic double g_veto_diff = 0.0;\nstatic double g_beta_neg = 15.0;\nstatic inline void load_veto_env(void) {\n  const char* s;\n  s=getenv("VETO_TIE_EPS"); if(s) g_tie_eps=atof(s);\n  s=getenv("VETO_MIN"); if(s) g_veto_min=atof(s);\n  s=getenv("VETO_DIFF"); if(s) g_veto_diff=atof(s);\n  s=getenv("BETA_NEG"); if(s) g_beta_neg=atof(s);\n}\n'''
marker='// ================== M4: M2 + negative rules only for tie-breaking =================='
source=source.replace(marker,insert+'\n'+marker,1)
source=source.replace('int main(int argc, char *argv[])\n{\n','int main(int argc, char *argv[])\n{\n  load_veto_env();\n',1)
(out/'main_runtime.cpp').write_text(source)
subprocess.run(['g++','-O2','-std=c++11',str(out/'main_runtime.cpp'),'-o',str(out/'classifier')],check=True)
for p in base.glob('*.dat'):
    if p.name.startswith(('1.','2.','3.','4.','5.','6.','7.','8.','9.','10.','Classes','ReglasDataset')):
        shutil.copy2(p,out/p.name)

baseline=package_root/'spaphish_scoring_ablation_results'/'spaphish_scoring_ablation'/'topk_shrink'/'m4d_veto_instance_log.csv'
bdf=pd.read_csv(baseline)
basepred={(int(r.fold),int(r.inst_idx)):int(r.pred_class) for r in bdf.itertuples()}

ties=[0.02,0.03]
mins=[0.025,0.05]
diffs=[0.0,0.01]
betas=[0,2,5,10,15,20]
rows=[]; predrows=[]
for idx,(tie,vmin,vdiff,beta) in enumerate(itertools.product(ties,mins,diffs,betas),1):
    for fn in ['m4d_veto_instance_log.csv','m4d_veto_fold_summary.csv','AnalisisInstancias.dat','tmp_results.txt']:
        try:(out/fn).unlink()
        except FileNotFoundError:pass
    env=os.environ.copy(); env.update({'VETO_TIE_EPS':str(tie),'VETO_MIN':str(vmin),'VETO_DIFF':str(vdiff),'BETA_NEG':str(beta)})
    cp=subprocess.run([str(out/'classifier'),'tmp_results.txt',str(idx)],cwd=out,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    if cp.returncode: raise RuntimeError(cp.stderr)
    df=pd.read_csv(out/'m4d_veto_instance_log.csv')
    y=df.true_class.astype(int).to_numpy(); pred=df.pred_class.astype(int).to_numpy()
    cm=confusion_matrix(y,pred,labels=[77,78]); tn,fp,fn,tp=cm.ravel()
    changed=wc=cw=0
    for r in df.itertuples():
        k=(int(r.fold),int(r.inst_idx)); bp=basepred[k]; pp=int(r.pred_class); yy=int(r.true_class)
        if bp!=pp:
            changed+=1
            if bp!=yy and pp==yy: wc+=1
            elif bp==yy and pp!=yy: cw+=1
    p=binomtest(min(wc,cw),wc+cw,0.5).pvalue if wc+cw else 1.0
    rows.append(dict(tie_eps=tie,veto_min=vmin,veto_diff=vdiff,beta_neg=beta,
                     accuracy=accuracy_score(y,pred),macro_f1=f1_score(y,pred,average='macro'),
                     TN=tn,FP=fp,FN=fn,TP=tp,near_ties=int(df.near_tie.sum()),negative_covered=int(df.neg_covered.sum()),
                     changed=changed,wrong_to_correct=wc,correct_to_wrong=cw,net_gain=wc-cw,mcnemar_exact_p=p))
    for r in df.itertuples():
        predrows.append((tie,vmin,vdiff,beta,int(r.fold),int(r.inst_idx),int(r.true_class),int(r.pred_class)))
res=pd.DataFrame(rows).sort_values(['net_gain','accuracy','changed'],ascending=[False,False,True])
res.to_csv(out/'beta_neg_sensitivity_all.csv',index=False)
pd.DataFrame(predrows,columns=['tie_eps','veto_min','veto_diff','beta_neg','fold','inst_idx','true_class','pred_class']).to_csv(out/'beta_neg_predictions.csv',index=False)
res.head(30).to_csv(out/'top30_configs.csv',index=False)
res.groupby('beta_neg').agg(mean_accuracy=('accuracy','mean'),max_accuracy=('accuracy','max'),mean_net_gain=('net_gain','mean'),max_net_gain=('net_gain','max'),mean_changed=('changed','mean')).reset_index().to_csv(out/'summary_by_beta_neg.csv',index=False)
# robustness count of top performance by beta and neighborhood
best_acc=res.accuracy.max(); best_gain=res.net_gain.max()
summary={
 'best_accuracy':best_acc,'best_net_gain':int(best_gain),
 'configs_at_best_accuracy':int((res.accuracy==best_acc).sum()),
 'configs_positive_gain':int((res.net_gain>0).sum()),
 'configs_zero_gain':int((res.net_gain==0).sum()),
 'configs_negative_gain':int((res.net_gain<0).sum())}
Path(out/'summary.txt').write_text(str(summary)+'\n\n'+res.head(20).to_string(index=False)+'\n')
print(res.head(20).to_string(index=False))
print(summary)
