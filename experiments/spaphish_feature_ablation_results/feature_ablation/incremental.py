from pathlib import Path
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score,f1_score
root=Path(__file__).resolve().parent
def load(v):
 x=pd.read_csv(root/v/'m4d_veto_instance_log.csv').drop_duplicates(['fold','inst_idx'],keep='last').sort_values(['fold','inst_idx'])
 return x[['fold','inst_idx','true_class','pred_class']]
pairs=[('technical','technical_lexical','add lexical to technical'),('technical','technical_persuasion','add persuasion to technical'),('lexical','lexical_persuasion','add persuasion to lexical'),('persuasion','technical_persuasion','add technical to persuasion'),('persuasion','lexical_persuasion','add lexical to persuasion'),('technical_lexical','full','add persuasion to technical+lexical'),('technical_persuasion','full','add lexical to technical+persuasion'),('lexical_persuasion','full','add technical to lexical+persuasion')]
rows=[]
for a,b,label in pairs:
 A=load(a).rename(columns={'pred_class':'pa'});B=load(b).rename(columns={'pred_class':'pb'})
 z=A.merge(B,on=['fold','inst_idx','true_class'])
 ca=z.pa.eq(z.true_class); cb=z.pb.eq(z.true_class)
 a_wrong_b_right=int((~ca&cb).sum());a_right_b_wrong=int((ca&~cb).sum());d=a_wrong_b_right+a_right_b_wrong
 rows.append(dict(comparison=label,from_variant=a,to_variant=b,accuracy_from=ca.mean(),accuracy_to=cb.mean(),net_correct_gain=a_wrong_b_right-a_right_b_wrong,wrong_to_correct=a_wrong_b_right,correct_to_wrong=a_right_b_wrong,mcnemar_p=binomtest(min(a_wrong_b_right,a_right_b_wrong),d,.5).pvalue if d else 1))
pd.DataFrame(rows).to_csv(root/'feature_incremental_comparisons.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
