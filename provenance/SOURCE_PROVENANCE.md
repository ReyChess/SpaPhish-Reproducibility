# Historical source provenance

The three files in `src/` are preserved historical sources supplied by the authors for the SpaPhish experiments. File names were normalized for repository use; file contents were not modified.

- `mfi_ct_spaphish_historical.c` — direct maximal CAR miner used by the main SpaPhish experiment. When compiled and run at `sigma=0.04` on the ten archived training sets, it regenerates all ten archived `ReglasDataset*.dat` files byte-for-byte.
- `dmc_ac_spaphish_historical.cpp` — DMC-AC/M4d classifier. Its SHA-256 is identical to the `main.cpp` stored in the full feature-ablation and complexity experiment snapshots. Re-running it on the regenerated rules and archived folds reproduces the reported main 10-fold average accuracy of `88.2424%`.
- `divide_en_10_historical.c` — historical stratified 10-fold generator. It seeds its shuffle with `time(NULL)`, so it is retained for provenance and protocol inspection, but it must not be used to regenerate the canonical published folds. The exact archived folds are the reproducibility reference.

See `uploaded_source_sha256.txt` and `scripts/reproduce_main_10fold.py`.
