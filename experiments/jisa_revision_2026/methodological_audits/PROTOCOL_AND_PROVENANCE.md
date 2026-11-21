# Protocol and provenance

The historical enriched comparison used 45 indicators and archived stratified folds. The 35-indicator work reuses those outer folds for one comparison, holds out entire template groups for a second comparison, and uses retrospective calendar-year holdouts for the third and fourth comparisons. The 24 messages with unparseable dates are outside both chronological analyses. CBA's inner folds were class-stratified, including when its outer folds were template-grouped. The fixed-configuration RF, LR and DT comparisons are descriptive alongside the internally tuned CBA.

The first grouped DMC-AC-P setup used dataset-wide class counts (664 and 731) as priors. The corrected run derives the counts from each scenario's training membership and supplies a separate `Classes.dat` to each native process. For example, grouped fold 1 uses 597 legitimate and 658 phishing training examples. The training count also defines the majority fallback.

The chronological protocol separates model fitting from its later test messages. The historical Spanish wordlists, regular expressions, case and accent normalization, and feature-definition freeze date could not be authenticated. Whether 2025 messages influenced feature design remains unresolved. The supplied 35-column data reproduce model inputs, but do not establish end-to-end regeneration of the lexical indicators from raw emails. The numeric-field cross-check covers ten indicators. Contributor/channel provenance is incomplete, and template grouping does not settle label/source confounding in the convenience sample. The 2025 ablation is a retrospective diagnostic and does not validate a post-hoc parameter change.

## CMAR exclusion

The manuscript audit reported identical inner macro-F1 and rule counts across requested support settings within each outer-fold and confidence combination. It counted 6,663 of 11,189 exported rules below the selected 0.04 support threshold. In the separate first-fold diagnostic, the inspected Java build reported zero effective support records during frequent-set generation and returned identical rules and predictions at four requested supports. The historical binary could not be authenticated against that diagnostic build. These reported observations concern the tested implementation and the archived exports. The JISA comparison and associated significance tests omit CMAR. The original diagnostic logs and exports were unavailable in the supplied integration evidence for independent verification.

The recovered [fold 1 support analysis](cmar_reports/INFORME_CMAR.md) and
[JAR diagnostic report](cmar_reports/CMAR_VERIFICATION_README.md) document
the exclusion. The JAR report includes excerpts from the later diagnostic
and the fingerprint reported for that diagnostic build. Local paths in the
report were redacted. The original JAR, complete diagnostic logs, rule
exports, bytecode and session files are unavailable in this archive. The
historical JAR's identity remains unresolved.

Independently enumerating the 63 nonempty subsets of the six fold-1 indicators
that occur in at least half of the 1,254 training messages confirmed one class
association rule at joint support 0.50. Its antecedent is `DISTRACTION_YES` and
its consequent is class 78 (638 joint matches out of 1,254 messages). Its
confidence is 638/941, below 0.80. This calculation checks the support argument
with the archived data. The JAR behaviour is documented by the supplied report.
