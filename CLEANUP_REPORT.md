# GitHub cleanup report

- Removed duplicate `source_archives/` ZIPs after confirming their extracted contents are already represented in the repository.
- Removed precompiled ELF/PE/Mach-O binaries; source and stored outputs were retained.
- Removed transient `.log` and build/cache files.
- Flattened the accidental `experiments/spaphish_complexity_efficiency_results/mnt/data/complexity_efficiency/` path.
- Replaced obvious container-specific Python paths with repository-relative paths where inputs are available.
- Removed duplicate/legacy article snapshots and the submission cover letter from the reproducibility tree.
- Added `.gitignore`, `requirements.txt`, `CITATION.cff`, a reviewer-oriented README, and regenerated SHA-256 checksums.
- The original MFI-CT miner source was not present in the supplied artifact bundle; full miner re-execution therefore requires an external compatible build.

Removed transient/binary files: **224**.

## Final source integration

The final repository adds the exact historical SpaPhish miner, DMC-AC/M4d classifier, and DivideEn10 sources under `src/`. The main reproduction script recompiles them and verifies 10/10 archived rule files by SHA-256 before reproducing the 88.2424% mean 10-fold accuracy. `DivideEn10` is retained for provenance but canonical folds remain archived because its historical shuffle is seeded with `time(NULL)`.
