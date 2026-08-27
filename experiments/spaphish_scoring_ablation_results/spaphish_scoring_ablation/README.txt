SpaPhish scoring ablation

All variants use:
- the same ten predefined outer folds;
- the same RegLasDataset1.dat--ReglasDataset10.dat files mined at global support sigma=0.04;
- exact-first positive coverage with one-missing-item partial fallback;
- negative veto disabled;
- class-prior term unchanged (STABLE_LAMBDA_PRIOR=0.15).

Variants:
1. best_single: STABLE_K_MAX=1, STABLE_BETA=0.0.
2. topk_no_shrink: STABLE_K_MAX=12, STABLE_BETA=0.0.
3. topk_shrink: STABLE_K_MAX=12, STABLE_BETA=2.0.

Files:
- scoring_ablation_summary.csv: pooled metrics and confusion matrices.
- scoring_ablation_folds.csv: fold-level accuracy.
- scoring_transitions.csv: paired prediction transitions and exact McNemar tests.
- scoring_instance_comparison.csv: aligned instance-level predictions.
- variant folders: source, executable, logs, and results for each run.
