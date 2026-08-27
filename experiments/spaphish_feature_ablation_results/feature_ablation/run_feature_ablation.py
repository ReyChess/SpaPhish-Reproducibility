from pathlib import Path
import subprocess, shutil, csv, time, json, os

here=Path(__file__).resolve().parent
base=here/'full'
out=here
miner=here/'miner'
classifier_src=base/'main.cpp'
if not miner.exists():
    raise SystemExit('MFI-CT miner executable is not bundled. Build/provide it as feature_ablation/miner before re-running this legacy orchestration script.')

pers={2,3,4,5,8,9,22,23,34,37}
lex={6,7,10,11,12,13,17,18,24,25,29}
allitems=set(range(1,46))
tech=allitems-pers-lex
variants={
 'technical':tech,
 'lexical':lex,
 'persuasion':pers,
 'technical_lexical':tech|lex,
 'technical_persuasion':tech|pers,
 'lexical_persuasion':lex|pers,
 'full':allitems,
}

def project(src,dst,keep):
    with open(src) as fi, open(dst,'w',newline='\n') as fo:
        for line in fi:
            vals=[int(x) for x in line.split()]
            if not vals: continue
            cls=vals[-1]
            feats=[x for x in vals[:-1] if x in keep]
            fo.write(' '.join(map(str,feats+[cls]))+'\n')

def run(cmd,cwd,log=None):
    p=subprocess.run(cmd,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=True)
    if log: Path(log).write_text(p.stdout)
    return p.stdout

# compile classifier DMC-AC-P (partial on, negative off)
for name,keep in variants.items():
    d=out/name
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)
    shutil.copy(classifier_src,d/'main.cpp')
    shutil.copy(base/'Classes.dat',d/'Classes.dat')
    # projected train/test files
    for i in range(1,11):
        project(base/f'Dataset{i}.dat',d/f'Dataset{i}.dat',keep)
        project(base/f'{i}.dat',d/f'{i}.dat',keep)
    # mine
    mine_rows=[]
    for i in range(1,11):
        t=time.time()
        txt=run([str(miner),f'Dataset{i}.dat','0.04',f'ReglasDataset{i}.dat'],d,d/f'miner_fold{i}.log')
        elapsed=time.time()-t
        lines=sum(1 for _ in open(d/f'ReglasDataset{i}.dat'))
        # parse maximal count
        maxc=None
        for ln in txt.splitlines():
            if ln.startswith('Total de Maximales '): maxc=int(ln.split()[-1])
        mine_rows.append({'variant':name,'fold':i,'rule_entries':lines,'maximals':maxc,'wall_seconds':elapsed})
    with open(d/'mining_summary.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=mine_rows[0].keys());w.writeheader();w.writerows(mine_rows)
    # compile and classify
    run(['g++','-O2','-std=gnu++17','-DM4_USE_NEGATIVES_FOR_TIEBREAK=0','main.cpp','-lm','-o','classifier'],d,d/'compile.log')
    for p in ['m4d_veto_instance_log.csv','m4d_veto_fold_summary.csv','AnalisisInstancias.dat','results.txt']:
        q=d/p
        if q.exists(): q.unlink()
    run(['./classifier','results.txt'],d,d/'classifier_stdout.log')

(out/'groups.json').write_text(json.dumps({k:sorted(v) for k,v in variants.items()},indent=2))
