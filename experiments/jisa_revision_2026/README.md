# SpaPhish JISA 2026 experimental evidence

This directory records the retrospective 35-indicator evaluation. It uses 24 technical or structural indicators and 11 aggregated lexical indicators. Five majority-vote and five unanimous-vote persuasion indicators were excluded. The 1,395 messages comprise 664 legitimate (77) and 731 phishing (78).

| Protocol | n | DMC-AC-P | CBA | RF | LR | DT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original stratified folds | 1,395 | 85.09% | 84.37% | — | — | — |
| Template-group-disjoint CV | 1,395 | 84.37% | 84.66% | 89.82% | 87.38% | 85.38% |
| Train through 2023, test 2024 | 295 | 77.97% | 65.76% | 69.83% | 81.36% | 71.86% |
| Train through 2024, test 2025 | 511 | 63.21% | 71.04% | 76.91% | 79.45% | 70.65% |

The original stratified 35-indicator archive supplied aligned predictions for DMC-AC-P and CBA. RF, LR and DT were described in the manuscript with different configurations from the grouped and temporal runs. Their original stratified prediction files were unavailable for this integration. The archived historical 45-indicator 10-fold result remains 88.24%. The archived historical 2025 DMC-AC-P temporal result is about 76.91%, under a different protocol.

For the 12 revised grouped and temporal scenarios, DMC-AC-P uses support 0.04, Kmax 12, beta 2, prior weight 0.15 and training-only class counts. Negative evidence was disabled. DMC-AC-PN is the historical optional negative-evidence extension. Its evidence is documented in the [repository README](../../README.md).

## Verify and rerun

From the repository root:

```sh
python experiments/jisa_revision_2026/verify_evidence.py
sha256sum -c SHA256SUMS.txt
```

The verifier checks prediction-level metrics, class and fold alignment, priors, hashes, the two 2025 explanations and five annotation agreement estimates. The [evidence manifest](EVIDENCE_MANIFEST.md) identifies the source files and the remaining gaps.

To rerun the grouped and temporal RF, LR and DT fits with scikit-learn 1.8.0, NumPy and pandas, write outputs to a scratch directory:

```sh
python experiments/jisa_revision_2026/grouped_35_validation/run_validation.py /tmp/spaphish-sklearn
```

To rerun DMC-AC-P with GCC/G++ and SSE4.2, generate the exact training and test files in scratch. The input preparation script requires all 24 files to match the archived hashes. Each native process uses one training partition and repeats its held-out inputs in ten positions for compatibility with the historical executable. Its first-position predictions are retained once.

```sh
replica=$(mktemp -d)
campaign=experiments/jisa_revision_2026/dmc_training_priors_corrected
mkdir -p "$replica/scripts"
cp "$campaign/scripts/run_dmc_corrected.py" "$replica/scripts/"
python "$campaign/prepare_inputs.py" "$replica/prepared"
python "$replica/scripts/run_dmc_corrected.py" --repo "$PWD"
```

To replay the 14 prior weights from the archived rules and scenario counts, use pandas and NumPy:

```sh
python experiments/jisa_revision_2026/prior_lambda_ablation/replay_ablation.py /tmp/spaphish-ablation
```

The replay uses fixed rule bases and is retrospective. The 2025 outcomes did not select a new prior weight. At weight zero versus 0.15, accuracy is 83.66% versus 84.37% for grouped CV, 72.20% versus 77.97% in 2024, and 77.89% versus 63.21% in 2025. The 2025 replay corrects 90 predictions, introduces 15 errors and reduces phishing false negatives from 176 to 86.
