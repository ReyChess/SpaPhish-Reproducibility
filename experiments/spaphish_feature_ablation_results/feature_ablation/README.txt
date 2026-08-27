Feature-group ablation for SpaPhish DMC-AC-P.
All variants use the same predefined 10 folds, global support sigma=0.04, exact-first one-missing-item positive fallback, Kmax=12, beta=2, and negative veto disabled.
Feature groups:
- Technical/structural: 24 items
- Lexical: 11 items
- Persuasion/annotation: 10 items
Rules were re-mined independently for every reduced representation and outer training fold using the supplied original miner.
The full representation reproduced 88.2437% pooled accuracy and macro-F1 0.8822.
