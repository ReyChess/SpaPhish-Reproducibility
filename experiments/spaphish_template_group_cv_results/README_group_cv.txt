SpaPhish template-grouped cross-validation experiment
=====================================================

Dataset: 1395 messages.
Text used for grouping: normalized subject + body.
Normalization: lowercase; URLs, e-mail addresses, dates, and numbers replaced by placeholders; whitespace collapsed.
Similarity representation: TF-IDF character n-grams (3-5).
Primary template threshold: cosine similarity >= 0.95.
Grouping: connected components of the similarity graph.
Cross-validation: StratifiedGroupKFold, 10 folds, shuffle=True, random_state=42.
Important property: no template group occurs in more than one fold.

Grouping results
----------------
73 multi-message template groups.
271 messages belong to a multi-message group.
Largest connected template group: 44 messages.
No group at threshold 0.95 mixes the two labels.

DMC-AC settings
---------------
sigma = 0.04
exact-first positive coverage, one-missing-item fallback
Kmax = 12
positive beta = 2
lambda_prior = 0.15
negative Kmax = 2
negative beta = 15
tie epsilon = 0.03
veto minimum = 0.05
veto difference = 0
Negative partial coverage disabled.

Template-grouped results
------------------------
DMC-AC-P:
accuracy = 0.884588
macro-F1 = 0.884519
phishing precision = 0.908309
phishing recall = 0.867305
phishing F1 = 0.887334
balanced accuracy = 0.885460
MCC = 0.770030
TN=600, FP=64, FN=97, TP=634

DMC-AC-PN with the previously tuned veto:
identical predictions and metrics; veto changes = 0.

Interpretation
--------------
The positive classifier did not deteriorate under template-grouped CV relative to the previously reported random stratified CV.
This provides evidence that its reported performance is not explained by strong near-duplicate templates at the selected 0.95 threshold.
The negative veto benefit did not reproduce under the grouped partition, indicating that the negative stage is more sensitive to fold composition.
Because the original and grouped protocols use different folds, differences between their aggregate metrics are descriptive rather than paired significance tests.
