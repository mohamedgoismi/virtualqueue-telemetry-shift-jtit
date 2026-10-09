# Reproducibility protocol

1. Python 3.10+ and dependencies in `requirements.txt`.
2. Reference generator is `code/virtual_queue_experiment.py`: `simulator()`.
3. Event-time features are computed by `causal_features()`; a report for packet
   *j* can be used at packet *i* only when its completion+report delay is not
   after *i*'s arrival time. Unreported packets expire after 120 ms.
4. Primary four-fold test partitions group complete scenario IDs, with 18
   configurations (5,400 packets) held out per fold; training and validation
   contain the other 54 configurations.
5. Repeated traces in `code/reviewer_round3_experiments.py --repeat 10` use ten
   generator seeds 20261100–20261109 and randomized scenario-group folds.
   This repeats **only** context LR, history LR and the pending-count rule.
6. Scientific artifacts in `results/` originate from the archived M5 project.
   Re-running scripts in place can overwrite them, so use a separate checkout
   or commit before experiments. Results depend on dependency versions.
7. Fast smoke and integrity checks: `python code/test_temporal_integrity.py`
   followed by `python -m unittest discover -s tests -v`.
8. Trace generation and comparison is CPU-based. Runtime of full repeated
   experiments can be substantial. No GPU is required.

## External data

`code/inspect_external_dataset.py` inspects local CSV files if independently
obtained by users; this is **not** a completed Zenodo dataset evaluation. The
repository does not ship or assume third-party packet measurements.

## Numerical reporting

Use the archived values in primary files, cite methods and fold definitions
explicitly, and do not interchange mean-of-fold AP with pooled out-of-fold AP.
Averaging PR-AUC/AP across different label prevalences is descriptive.
