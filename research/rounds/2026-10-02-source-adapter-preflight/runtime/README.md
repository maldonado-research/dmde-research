# Bounded GPL native-source adapter diagnostic

This separately authored GPL-3.0-only wrapper exercises the pinned official
Nudec solver at fixed states. It changes only the runtime source catalog,
registering the exact-muon-mass Michel callback with branch `[2*B_mumu]`.
Every native mass, mixing, collision, EOS and RHS implementation remains intact.
The grid is configured through native `setupGrid`; it is deliberately a coarse
N65 local fixture and is not certified for source moments or thermal transport.

The source-only control returns a zero callback with the same positive parent
count and native time gate. Parent density, Hubble and parent energy deposition
therefore remain present; turning the neutrino source off redirects its energy
to the electromagnetic sector. A separate native-gate-off control demonstrates
the different photon-temperature response.

The actual state time selects the native gate: `0 <= t < 18*tau`, implemented
with `stopPoint=nextafter(x,+inf)` or zero. Negative actual state times are
rejected before the native RHS. Boundary probes and different x/t pairs verify
the policy without presenting negative-time evolution as physical.

Run with the prepared exact package versions:

```sh
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B /workspace/shared/dmde-adapter-runtime/source_adapter_diagnostic.py declare --out /workspace/shared/dmde-adapter-runtime/predeclared-first
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B /workspace/shared/dmde-adapter-runtime/source_adapter_diagnostic.py run --out /workspace/shared/dmde-adapter-runtime/results-first
```

Output paths must be fresh. An atomic directory creation reserves the output
path, exclusive file creation prevents overwrites, and failures retain their
logs. The worker has a 60-second timeout. Optimized Python is refused; failed
adapter checks, native failures and timeouts exit nonzero. The expected failed
physics criterion is recorded separately from successful diagnostic execution.

The artifacts contain all 21 native tracked-file hashes and clean Git state
before/after, a complete executed wrapper snapshot/hash, package versions,
actual occupations, native vectors, callback captures and canonical six-charge
state/source arrays in JSON and CSV. Callback captures are actual pre-mixing
physical phi arrays. The wrapper converts those captures to canonical source
arrays; paired real RHS differences witness their consumed coefficient after
native mixing, using the measured native time derivative and an independent
mixing construction. The internal df_nudx accumulator is not instrumented.

The native full RHS mixes injected flavors and produces a tau source response,
so its source-only derivative disagrees with the frozen preoscillation phi.
This is an infinitesimal native unsplit RHS incompatibility; no finite-step
full-stepper h/h2 criterion is evaluated. It does not establish incompatibility
of a separately authored source substep or a split evolution scheme.
Independent audits additionally identified native QED P2 derivative and
rho3 identity inconsistencies. This work does not validate physics or integrate
a cosmological trajectory, weak rates, BBN, or a fitted production calculation.

The wrapper is GPL-3.0-only. `LICENSE.txt` carries the GPLv3 license text.

The completed fixed-state run is `results-serialization-fix/`. Its 12 adapter
and fixed-state checks passed in 5.05 seconds, and its independently
reconstructed native source coefficient differs by 4.46e-16 relative to the
peak source. Those checks establish the local adapter wiring and coefficient;
they do not validate a frozen bridge. The native unsplit derivative differs
from the declared preoscillation source by 0.580347 relative to its peak, above
the predeclared 0.005 comparison ceiling, with a positive tau response.
The native checkout remained clean and all 21 tracked hashes were unchanged.

The initial `results-first/` run failed final summary serialization on a NumPy
boolean and correctly exited nonzero; its raw evidence and error logs are
retained. The serialization repair and more precise scope wording did not
change scientific inputs. `predeclared-serialization-fix/` records the wrapper
identity immediately before the successful fresh run. `cli-checks/result.json`
records optimization rejection, existing-output preservation, concurrent
fresh-path reservation, and propagation of the actual first failure.

`bundle_manifest.json` identifies the current wrapper, selected successful
evidence, raw export route, limitations, and file hashes. Earlier failed
evidence is retained explicitly as execution history.
