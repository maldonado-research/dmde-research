# Copied-location QED helper CLI replay

The copied public helper ran successfully from working directory `/tmp`, with an explicit `--source /workspace/shared/dmde-upstream/nudec`, using Python 3.12.14, NumPy 2.3.5, and SciPy 1.16.3. The nine declared observations exactly match the original public component run; the complete JSON receipt differs only in its timestamp. This is a CLI portability and component-replay check, not a full EOS, RHS, trajectory, BBN, or observable validation. No parameters, helper files, or native source were patched.

The independent `portability_receipt.json` records the command, copied/original input SHA-256 hashes, complete before/after native tracked-file hashes, full original-public-tree hashes, output/log hashes, runtime comparisons, and pass/fail checks. The native source remained clean at `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`. The original public tree and all copied inputs were byte-identical before/after execution. `cli_import_trace.stderr.txt` records that Python loaded the two utility modules from the copied location and the three native modules from the explicitly supplied source.

## Minimum files and external dependencies

The runtime copy needs these four sibling files:

- `qed_component_reference.py`
- `conservation_review.py`
- `qed_identity_review.py`
- `qed_identity_review.json`

Keep `COPYING` with distributions. The helper imports sibling utility modules (`qed_component_reference.py:29–30`) and loads the prior negative JSON relative to its own file (`:109`). It requires Python, NumPy, SciPy, Git, and a clean complete Git checkout of the declared NuDec commit. The source snapshot hashes all tracked files, although the numerical component calculation imports only `Constants.py`, `Momentum_Grid.py`, and `Thermodynamics/Thermal_QED_corrections.py`. This isolated execution does not require upstream collision/solver dependencies such as Numba.

The helper does not need `local_conservation_review.json`, the saved RHS fixture, `PRIMARY_REFERENCE.json`, the original README/hash manifest, or a raw PDF or extracted PDF text. No raw primary-reference PDF was copied. The old JSON supplies reference metadata; this replay does not independently reopen or verify the cited paper.

The replay command was:

```sh
PYTHONPATH='' PYTHONDONTWRITEBYTECODE=1 \
  /workspace/shared/dmde-upstream/nudec-venv/bin/python -B -v \
  /workspace/shared/dmde-adapter-component-peer/portability/copied_public_helper/qed_component_reference.py \
  --source /workspace/shared/dmde-upstream/nudec \
  --output /workspace/shared/dmde-adapter-component-peer/portability/qed_component_reference_copied_replay.json
```

The recorded command ran with working directory `/tmp`; stdout and stderr were captured separately. Use a fresh output filename to repeat it, because the helper deliberately uses exclusive creation.

## Receipt limits identified independently

The ordinary fresh CLI resolves `--source`, validates a pinned-clean source snapshot, and prepends that source before native imports (`qed_component_reference.py:60–65`; `conservation_review.py:37–48`). The observed import trace confirms the selected files for this replay. Calling `run(args)` inside an existing Python process would require additional checks against cached `sys.modules` and namespace/package shadowing; the helper does not record loaded module paths itself.

The component hashes its own script and the prior JSON, but does not hash its two imported utility scripts in its output receipt (`qed_component_reference.py:117–119`). It also does not compare the old JSON's source snapshot, declaration, or recorded utility-script hashes with current inputs. This peer receipt independently binds all copied files and verifies that the old JSON's source and utility hashes match the actual pinned source and copies.

The output field `native_symbols_modified=False` (`:112`) is narrower than literal global immutability: native callables are unchanged, but the run sets grid globals and performs the declared QED 81/161/321 refinements (`:66–70`). It then restores the hardcoded QED default of 81 (`:104–105`), rather than an embedded caller's prior configuration, and lacks `try/finally` restoration on failure. This short-lived standalone process exited successfully.

The helper checks its final source snapshot before creating the output (`:106–126`). A path inside the source checkout could therefore dirty the checkout after that check. This replay placed all output outside the source and independently checked native cleanliness/hashes after CLI exit. Git tracked hashes and porcelain do not certify ignored-file cleanliness; this replay disabled bytecode writing with `-B` and `PYTHONDONTWRITEBYTECODE=1`.
