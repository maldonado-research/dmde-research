# Spectral-to-BBN bridge contract v0.9.20

Return one coarse and one fine bridge pair per blind card. Each pair consists of an NPZ history and a metadata JSON.

The NPZ must contain:

- the full frozen source identity and native multiplicities;
- time, scale factor, photon temperature, momentum nodes/weights, and the physical-momentum scale;
- separate neutrino and antineutrino distributions for all three flavors;
- six momentum-resolved canonical source-RHS arrays in `dY/(dt dq)` per second, exported from the actual production injection callable before collisions and oscillations;
- six canonical `state_dYdq_*` histories and the declared positive
  normalization density mapping them to the occupation arrays;
- eight selected initial states and paired source-on/off production-stepper
  outputs at `h` and `h/2` for all six species;
- the implemented frozen decay, electromagnetic, neutrino, and zero charged-pion source histories;
- direct total and process-resolved neutron-to-proton and proton-to-neutron rates, Hubble history, neutron lifetime, and final $Y_p$, $10^5\mathrm{D/H}$, and $N_{\rm eff}$. Corrected physical process columns must sum to each total.

The metadata must identify the backend, immutable version/commit, environment,
run role, coordinate/quadrature, source, state, production stepper and toggle,
collision/oscillation treatment, exact five-process weak-rate mapping and
callable, BBN canary command, nuclear rates, interpolation/extrapolation, and
production classification.

Both bridges must independently pass source identity; endpoint; all-node source
weighted-L1/CDF/support/cutoff; scalar and actual source time integrals;
thermal and initial-FD shape; Michel moments; occupation-to-state mapping;
paired stepper response and halving; canonical process sums; capture proxy;
Hubble/scale-factor; coordinate; physical-history; and provenance gates.

The validator derives all convergence deltas directly from the two files. In
addition to histories, moments, and final outputs, the fine grid must strictly
increase both `Nt` and `Nq` and reduce by at least `10%` the largest source-
window `dt/tau`, weak-window `|d ln T|`, stopped-muon-domain physical momentum
cell, antineutrino-threshold bracket, and beta-endpoint bracket. Irrelevant
tail nodes cannot qualify.
