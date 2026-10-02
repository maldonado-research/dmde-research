# Frozen-source callback and native collision-domain design

This public-source diagnostic identifies a viable **source-only** callback and canonical mapping, but does not establish a full frozen-history native transport adapter. The limiting issue is the combination of a fixed wide uniform comoving grid, an endpoint that moves through that grid, and the nonzero stopped-muon muon-flavor endpoint. A short-domain source moment scan passes at 4,001 and 8,001 native nodes; the full reference-domain ladder fails at all tested resolutions. No collision JIT, production stepper, trajectory, weak-rate calculation or nuclear network was executed here.

Research program: Ricardo Maldonado. This authored design and independent diagnostic were prepared with AI assistance from public official source, published audit and public provider documentation/source cards. No private raw input was read or published. Official upstream commit `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62` remains clean and byte-identical before/after. The diagnostic is GPL-3.0-only; the native dependency is the official GPLv3 Nudec solver.

## Explicit mass and callback policy

The selected minimal design keeps the native transport/EOS/collision masses unchanged and introduces exactly one source-specific callback. This is a deliberate separate prescription:

| Quantity | Value | Consumers and treatment |
|---|---:|---|
| Native coordinate electron mass | `0.5109989` MeV | `p=q*me/x`, `a=x/me`, Hubble conversion, parent count/density, temperature conversion and occupation normalization retain this value |
| Native muon mass | `105.7` MeV | Native constant copies and unused pion-derived endpoint remain unchanged; native muon source is retained only as a negative diagnostic |
| Frozen source muon mass | `105.6583755` MeV | Authored `frozen_michel` callback alone uses this exact value for shape/support |
| Frozen weak-kernel electron mass | `0.51099895` MeV | Explicitly recorded; no weak kernel is executed and this value is not substituted into the transport coordinate |

The requested exact electron mass must be consumed explicitly by a future weak-rate adapter. Its existence does not by itself require replacing the native coordinate scale. If a future design chooses a global exact-electron-mass transport variant, it must declare that distinct variant and propagate the value to every consumer before compilation. Relabeling native coordinates as though they used `0.51099895` would be incorrect.

The static all-consumer map is in `results-first-declared/consumer_override_map.json`. `from Constants import *` creates copied names in `Distributions`, `Core`, `System_Nudecoupling`, `Thermodynamics.Thermodynamics_ideal_gas`, `Thermodynamics.Thermal_QED_corrections`, `Collision_term.Collision_term_diagonal` and `SingleShot`; `Constants` owns the original values. Some copies are unused by individual modules. `Distributions.__pion_neutrino_energy` is computed once at import. The diagnostic imports the safe library modules, verifies every imported mass copy remains native, records the derived pion endpoint and never imports execution entrypoints `SingleShot` or `BatchLauncher`. A late edit to `Constants.me/mmu` alone would miss existing copies and derived values.

Register `Distributions.getDistribution=[frozen_michel]` and use `branching_fractions=[2*B_mumu]`. The branch list is the intended future native-production mapping; this source-only diagnostic directly uses the algebraically equivalent B factor and does not construct or consume production branches. The callback implements native physical-momentum density `K=dN/dp` with exact endpoint `p_star=52.82918775 MeV`, returns shape `(3,Nq)`, tau source zero and no renormalization. Its decay probability is one for the prompt stopped-muon prescription. All pion and direct-neutrino channels are absent. It does not invoke `initDistributions` afterward, because that would replace the source catalog. This differs from modifying `Distributions.muonDistribution` or global mass constants. Catalog registration is a Python-memory assignment and upstream files remain untouched.

## Canonical state and actual-source export

For native transport `c=me/x`, `p_i=c*q_i`, choose and state a positive comoving reference entropy

```text
s0 = (2*pi^2/45)*10.75*(1.00003*me/x0)^3
s_ref(x) = s0*(x0/x)^3
n_start = Y0*s0
native llp_count = n_start*(x0/me)^3
alpha(q_i,x) = c*p_i^2/(2*pi^2*s_ref(x))
state_dYdq_a = alpha*f_a
```

At fixed comoving q, `alpha=q^2*me^3/(2*pi^2*s0*x0^3)` is independent of x. Thus the canonical source conversion has no extra normalization time derivative. The native accumulator is

```text
dfdx_source = [N_mu*n_X*hbar/(2*H*x*tau)]*K(p)*2*pi^2/p^2
dt_dx = hbar/(H*x)
S_dYdt_dq = alpha*dfdx_source/dt_dx
           = B_mumu*[Y0*exp(-t/tau)/tau]*c*K(c*q)
```

This map contains the required `dp/dq=c` Jacobian. An evolving plasma entropy density cannot replace `s_ref` without revisiting the derivative. Native charge symmetry means export `nuebar=nue`, `numubar=numu`, `nutaubar=nutau`; these are six declared symmetry-related arrays from three evolved occupations, not six independently evolved histories. Tau occupation can be nonzero even though the pre-mixing tau source is zero.

The emitter diagnostic exports six source arrays and six fixed-state canonical arrays in `diagnostic_symmetric_arrays.npz`, with eight independent synthetic snapshots at `t/tau=0,.001,.1,1,5,17.999,18,18.001`, all at `x=.1`. The latter are deliberately not a cosmological history. Source arrays invoke the registered callback, not a production RHS accumulator, and must not be presented as production-consumption evidence.

A future production witness can capture the actual native accumulator without changing upstream: install a read-only Python trace callback scoped to `System_Nudec.__code__`, pinned file hash and the line just before mixing (`System_Nudecoupling.py:123`). Copy `df_nudx`, `momentumVals`, `trueHubble`, x and the input state from frame locals; convert with the formula above; remove the trace in a `finally` block. The native RHS is ordinary Python, whereas Numba collision internals need no trace. This is an observation hook, not an independently reconstructed Michel sidecar. A trace at return is too late because mixing and collision have already modified the accumulator. Production runs must identify the callback, selected frame/line, executed wrapper and source hash, retain source toggles and bind accepted-state exports to source-captured RHS calls.

For the exact half-open cutoff, a wrapper may pass native `stopPoint=+infinity` when `0<=sys_values[-1]<18*tau` and `stopPoint=-infinity` otherwise, so both native `x<stopPoint` source and parent-deposition branches follow the actual t state. Split integration at the actual-time event and validate the source-off row at the event; a reference `x(t)` table is not a proof. Native residual parent density still decays after this cutoff and requires separate continuity treatment. These production techniques are designs, not exercised capabilities here.

Native source mixing immediately populates tau. The full mixed production-stepper response therefore does not satisfy a literal pre-mixing six-species source response requirement without a separately defined pre-mixing/source substep and corresponding provenance. Current source-only success does not close that gap.

## Native grid and collision assumptions

`Momentum_Grid.setupGrid` constructs a positive affine grid with odd N and its native weights:

```text
q_i = q_min + i*Deltaq
Deltaq = (q_max-q_min)/(N-1)
mathematical native weights = Deltaq/3*(1,4,2,...,4,1)
p_i(x) = me*q_i/x
dp_i quadrature weights = (me/x)*weights_dq_i
```

Require `N>=3`, odd N, `0<q_min<q_max`, finite increasing nodes, positive finite native weights and coherent `(ni,i=gridVals[ni])` inputs. The upstream implementation computes each three-point Lagrange polynomial in absolute coordinates and sums overlapping windows; preserve its returned bytes instead of silently replacing them with analytic Simpson weights.

The native collision kernel integrates over every j,k pair for each i, forms `l_pre=q_i+q_j-q_k`, rejects it outside the inclusive grid bounds and snaps it to the closest grid node. On a uniform offset grid

```text
l_pre = q_min + (i_index+j_index-k_index)*Deltaq
```

is another node in exact arithmetic. Nonuniform-grid snapping changes momentum conservation. For a 21-node independent geometry diagnostic, the uniform maximum defect was `8.88e-16`; a nonuniform grid gave defect `0.143888` with 4,951 of 5,796 in-range triples differing above `1e-12`. This independently coded geometry diagnostic did not execute collision integrals. Floating-point bounds tests can also reject mathematically boundary-valued triples, and this was not repaired here.

The collision prefactors multiply `weights_dq[j]*weights_dq[k]`. Replacing full-domain native weights with support-truncated/custom Simpson weights changes the discrete collision operator and its energy exchange. Nonuniform grids are callable but do not preserve the native momentum relation; custom weights do not preserve its quadrature. Improving source moments by either change is therefore a new discretization, requiring separate physical tests.

Numba specializes collision functions with grid module globals treated as constants. Set the grid exactly once before first JIT specialization, and use a fresh process for each new grid. Reassigning `Momentum_Grid.gridVals/gridWeights/n` after compilation can leave native collision snapshots inconsistent with the live Python RHS. The present source-only ladder changes grids safely because it never specializes a collision function; the empty dispatcher signatures are recorded.

Physical nodes may evolve via `p=c(x)q` while q stays fixed. Rebuilding `q=x*p/me` to keep physical nodes fixed changes the native state basis and requires a regridding/advection term. A time-varying native q grid cannot be substituted into the existing ODE. Fresh workers can evaluate instantaneous collision operators on different valid static grids, but that is a different construction from fixed-q native evolution.

## Endpoint strategy, observed failures and budget

Choose a predeclared hard coordinate cap x_cap and retain fixed `q_max>=x_cap*p_star/me`, preferably with explicit slack. At every actual source-on RHS call assert `q_max*me/x>=p_star`; terminate with a preserved failure if the cap is exceeded. The public reference table gives `x_cap=16.993868549367075`, but an injected background may differ. This cap is an illustrative reference value, not an achieved actual-time domain proof.

With native me, the reference endpoint-complete `q_max=1756.8966825434131`; at initial x=.1 the endpoint is only `q_star=10.338415160971971`. The default N301 grid spacing is about 5.8563 and only two nodes lie in source support. Full-domain native-weight errors below are maxima over both source flavors and moment orders 0 through 5 at x `.1,.25,1,4,10,x_cap`:

| N | Maximum relative moment error | Result |
|---:|---:|---|
| 301 | 82.5367% | fail |
| 1,001 | 26.9356% | fail |
| 3,001 | 3.15852% | fail |
| 10,001 | 5.01297% | fail |

At identical nodes the exact-source callback and independent dimensionless frozen formula agree with peak-scaled errors below `7.34e-16`; this nodal identity does not imply quadrature accuracy. At x=.1, N10001 still gives 5.01297% moment error. Refinement is nonmonotonic because the moving interior endpoint changes phase relative to global Simpson weights. The original clipped q_max formula gives 99.2044% worst moment error at x_cap; it is retained without rescaling. Native rounded-muon source differs from the frozen nodal shape by peak-scaled `0.00231866` at the tested x=1.

For an interior muon endpoint, `F_mu(1)=2` is nonzero. If it falls after node m at fractional cell phase theta, the global Simpson cumulative constant weights terminate at `(m+1/3)h` for even m or `(m+2/3)h` for odd m. Their discrepancy from the exact endpoint can approach `2h/3`. The leading high-order endpoint term therefore estimates

```text
relative muon-k5 endpoint error ~= (48/11)*Deltaq/q_star
```

because `M_mu,5=11/36`. To keep that leading estimate below .005 at initial x=.1 requires `Deltaq~<=.0118461`, giving odd N about 148,311 for the full reference domain. This is an asymptotic phase estimate, **not a rigorous error bound or an executed convergence result**. Native collision work scales roughly as N cubed per RHS, so that estimate is about `1.196e8` times the N301 loop count. No wall-time projection or full dense collision feasibility claim is made.

The native polynomial weight construction also becomes numerically ill-conditioned as bins narrow while absolute q grows: full-cap N10001 weights differ from analytic Simpson by up to `2.6481e-4` relative per weight. It is not safe to extrapolate this builder to N148311 or substitute custom weights silently. Thus a full-history native collision adapter has an unresolved numerical and computational blocker under the current grid prescription.

The smallest supported next source-only refinement is the short native grid `q=[.01,40]` with N4001 and N8001, x in `[.1,.2]`. The independently predeclared scan tested 1,001 equally spaced x coordinates:

| N | Worst k0..5 relative error | Worst x | Pass sampled .005 ceiling |
|---:|---:|---:|---|
| 3,001 | .00539153 | .1026 | no |
| 4,001 | .00398695 | .1027 | yes |
| 8,001 | .00202978 | .1012 | yes |

The first three-point short-window test at N3001 appeared to pass, but the phase sweep falsified that conclusion. Both records remain. These finite samples do not establish all possible x phases or an actual short transport trajectory. The short grid covers the source endpoint throughout the declared x interval and supports meaningful source moments, but running native collisions at N4001/8001 would still cost roughly 2,349/18,782 times N301 loop count and was not attempted.

Use this short source-only ladder to exercise exact callback arrays, charge symmetry, zero tau, node identity, the comoving-state map, moments and actual-time cutoff semantics. Keep native collision/temperature/production-stepper checks on separately bounded affordable grids explicitly marked moment-inadequate; passing them does not promote that grid to a frozen-history source adapter. A full-history gate requires either a justified alternative conservative collision discretization or demonstrated adequate dense native quadrature/runtime, plus the independent background/source-stepper issues. Nonuniform grids, moment-repaired source weights and moving q grids cannot be described as preserving the existing native operator.

## Receipts and reproduction

`predeclaration.json` preceded the first execution. `refinement_predeclaration.json` preceded the phase scan. Both identify the public unblinded synthetic source test card `Y0=1e-6`, `B_mumu=.4`, `tau=40 s`; there is no private-label inference. Executed wrapper hashes, constant-copy map, source before/after inventories, raw arrays, native quadrature results and geometry controls are retained. The first refinement attempt failed after computation while serializing a NumPy `int64`; `results-phase-refinement/failure_receipt.json` retains that failure, and the corrected scan wrote a fresh directory. The failed wrapper was subsequently reconstructed by undoing its sole int-conversion fix; its exact bytes match the contemporaneously recorded execution hash, with reconstruction timing explicitly disclosed.

Independent review added a clean pinned-source precondition to the phase script and then root review added explicit refusal of assertion-disabling Python optimization. Current scripts refuse `-O`, `-OO` and assertion-disabling `PYTHONOPTIMIZE`, and check Git status with `--untracked-files=all`. Fresh `results-hardened-declared-replay/` and `results-hardened-phase-replay/` receipts identify their new wrapper hashes and exactly reproduce the earlier numerical rows and raw NPZ bytes. Historical executed-wrapper snapshots remain immutable; old receipts are not attributed to new wrapper bytes. `HARDENING_REPLAY_RECEIPT.json` records the controls and exact replay results.

```bash
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B source_grid_diagnostic.py \
  --upstream /workspace/shared/dmde-upstream/nudec \
  --predeclaration predeclaration.json --output /tmp/dmde-source-grid-replay
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B source_grid_refinement.py \
  --upstream /workspace/shared/dmde-upstream/nudec \
  --predeclaration refinement_predeclaration.json --output /tmp/dmde-source-phase-replay
```

Run from this directory; output paths must be fresh. Runtime used Python3.12.14, NumPy2.3.5, SciPy1.16.3, Numba0.63.1 and llvmlite0.46.0 in the existing native dependency environment. The callback/module wrapper is independently authored; it invokes upstream grid construction and retains the unmodified native emitter as a negative control. No external solver implementation was copied or relicensed.

Public basis: published `2026-10-01-transport-source-audit/README.md` and `source-audit/SOURCE_CAPABILITY_AUDIT.md`; public provider native mapping, source operator gate, endpoint-domain gate, spectral bridge contract, moment-lock/native-mapping tables and public source cards; pinned official `Momentum_Grid.py:8–45,72–98`, `Collision_term_diagonal.py:13–56,114–115,154–155`, `Distributions.py:40–58,61–84`, `System_Nudecoupling.py:72–168`, `Core.py:66–97,136–155,187–194`, `Thermodynamics_ideal_gas.py:7–20,76–105`. The independent collision-grid reviewer confirmed grid closure, native quadrature, JIT snapshots and fixed-comoving coordinate assumptions.

This diagnostic does not close energy/EOS continuity, source-consumption/stepper, actual background evolution, weak/BBN handoff or late-time DMDE physical/observational gates. It establishes callback identity and exposes domain/refinement constraints while preserving failures.
