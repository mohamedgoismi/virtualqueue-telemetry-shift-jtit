# Provenance of the scientific archive

**Source snapshot:** the user-provided `JTIT_VirtualQueue_M5_COMPLETE.zip` /
`VirtualQueue_JTIT_M5_REVISED` project, dated 9 October 2026. We have **copied**
its selected Python and results files, not regenerated or silently corrected
their numbers in this GitHub preparation step. `MANIFEST_SHA256.txt` records
SHA-256 hashes for each file included in the repository.

## Primary manuscript evidence

- `results/synthetic_trace.csv`: original synthetic FIFO trace (72 scenarios,
  two repetitions of 150 packets each; 21,600 observations).
- `results/major_revision_metrics.csv` and `results/major_revision_summary.csv`:
  four-fold scenario-held-out results for queue rules, LR and HGB.
- `results/round3_context_fourfold.csv`,
  `results/round3_intermediate_summary.csv`,
  `results/round3_oof_predictions.csv`: contextual and intermediate-load
  analyses (out-of-fold predictions from the original trace).
- `results/round3_independent_traces.csv`,
  `results/round3_trace_confidence.csv` and `results/round3_trace_paired.json`:
  10 independent RNG traces; repeated context-LR, history-LR and queue-count
  **only**, on the same scenario family.
- `results/round3_threshold_sensitivity.csv` and
  `results/round3_budgets_with_ceiling.csv`: sensitivity and retrospective alert
  budgets from the original trace.
- `results/fourfold_matched_frozen_mixed.csv`:
  original-trace comparisons for matched, frozen and mixed regimes; do not
  present these as reproduced over 10 independent generator traces.

## Exploratory/secondary results retained for transparency

Legacy three-split results such as `model_metrics.csv`, `summary.csv`,
`queue_reconstruction.csv`, `split_summary.csv`,
`delay_2ms_by_split.csv`, and `cross_regime_transfer.csv` arise from an earlier
protocol, and MUST NOT be pooled with the four-fold manuscript results.
`results/provenance_secondary.json` has related notes from the prior project.

## Scientific vs. archival claims

A code archive DOI establishes a **persistent software record**, not proof of
validity, peer review, real-world generalizability or dataset integrity.
External validation is outstanding.
