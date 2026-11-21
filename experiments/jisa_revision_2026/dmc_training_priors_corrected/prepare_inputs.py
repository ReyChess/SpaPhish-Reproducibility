"""Restore exact native train/test inputs from archived memberships and features."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parents[1]


def rows(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def main():
    output = Path(sys.argv[1])
    binary = {r['instance_id']: r for r in rows(REPO/'data/spaphish_binary_folds.csv')}
    inventory = rows(ROOT/'automatic_35_baselines/indicator_inventory.csv')
    codes = [(r['item_name'], r['item_id']) for r in inventory if r['jisa_automatic']=='1']
    grouped = rows(ROOT/'grouped_35_validation/grouped_cv_train_test_manifest.csv')
    temporal = rows(ROOT/'temporal_35_validation/temporal_train_test_manifest.csv')
    provenance = json.loads((HERE/'provenance.json').read_text())
    for evidence in provenance['scenarios']:
        scenario = evidence['scenario']
        if scenario.startswith('grouped'):
            partition = [r for r in grouped if int(r['held_out_fold']) == int(scenario[-2:])]
        else:
            protocol = 'train_'+scenario.removeprefix('temporal_')
            partition = [r for r in temporal if r['protocol'] == protocol]
        folder = output/scenario
        folder.mkdir(parents=True, exist_ok=True)
        for role in ('train', 'test'):
            selected = [binary[r['instance_id']] for r in partition if r['role']==role]
            lines = [' '.join([*(code for name,code in codes if r[name]=='1'), r['class']])
                     for r in selected]
            data = ('\n'.join(lines)+'\n').encode()
            if hashlib.sha256(data).hexdigest() != evidence[f'{role}_sha256']:
                raise ValueError(f'Input hash mismatch for {scenario} {role}')
            (folder/f'{role}.dat').write_bytes(data)
            if role=='train':
                counts = Counter(r['class'] for r in selected)
                (folder/'Classes.dat').write_text(''.join(f'{c} {counts[c]}\n' for c in sorted(counts)))
            else:
                with (folder/'test_ids.csv').open('w', newline='') as stream:
                    writer = csv.writer(stream)
                    writer.writerow(['instance_id','class'])
                    writer.writerows((r['instance_id'],r['class']) for r in selected)
    print('Verified SHA-256 of all 24 native partition files')


if __name__ == '__main__':
    main()
