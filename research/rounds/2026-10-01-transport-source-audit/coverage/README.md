# Continuous source and weak-quadrature coverage diagnostic

This independent calculation integrates only the public prescribed Michel
source shapes. It neither evolves a neutrino state nor calculates occupied-state
weak rates, a time-integrated injection yield, or BBN abundances. The final
injection-domain fractions below are local `x -> x_stop^-` limits, because native
Nudec injection is enabled only while `x < stopPoint`. A final-domain deficit
must not be described as the fraction of the whole injection history lost.

`source_coverage.py` imports neither the provider validator nor an upstream
physics module. Its optional source paths record public-file hashes and Git
commits. The numerical receipt uses Python 3.12.14, NumPy 2.3.5, and SciPy 1.17.0.
No private inputs are used. Provider source cards and acceptance rules are
unchanged.

## Exact continuum reference

Let `L = m_mu/2`, `z = E/L`, and `c = clip(E_cut/L, 0, 1)`. The idealized frozen
source prescription is the massless charged-lepton Michel shape,

```
w_e(z)  = 12 z^2 (1-z)
w_mu(z) = 2 z^2 (3-2z)
dN/dE   = w(E/L)/L, 0 <= E <= L.
```

The complete normalized dimensionless moments and retained fractions are

```
M_e,k  = 12 / [(k+3)(k+4)]
M_mu,k = 2(k+6) / [(k+3)(k+4)]
R_e,k(c)  = (k+4)c^(k+3) - (k+3)c^(k+4)
R_mu,k(c) = [3(k+4)c^(k+3) - 2(k+3)c^(k+4)] / (k+6).
```

Physical complete moments are `L^k M_a,k`; retained moments multiply by
`R_a,k(c)`. The omitted upper-tail fraction is `1-R_a,k(c)`. The receipt records
all six frozen moment orders, `k=0,...,5`.

These exact continuum integrals are targets for quadrature. Frozen source-RHS
identity uses point values at the returned momentum nodes; it does not permit a
cell-average prescription or a renormalized clipped shape to replace those
values. A moment approximation and a pointwise source identity are separate
checks. The upstream source callable and its native grid quadrature require
separate execution evidence.

## Native endpoint arithmetic

At Nudec commit `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`, the source constants are
`me=0.5109989 MeV`, `mmu=105.7 MeV`; these differ from the frozen mass conventions
`me=0.51099895 MeV`, `m_mu=105.6583755 MeV`. `Core.py` selects
`q_max=x_stop*mmu/2` when that term exceeds the floor and direct-neutrino columns
are omitted. `System_Nudecoupling.py` evaluates `p=q*me/x`, so its final injection
limit is `p_max=27.006291865 MeV`, versus the native source endpoint `52.85 MeV`.
The retained native endpoint fraction is therefore `c=0.5109989`.

At the reference `x_stop=16.993868549367075`, native `q_max` is
`898.1259528340499`. Native endpoint completeness requires
`q_max=1757.5888183595891`. With both frozen masses, the corresponding complete
reference endpoint is `1756.8965106353612`. These are arithmetic evaluations at
the public reference stop value, not new transport results.

| Prescribed shape at native final domain | Retained number | Retained energy | Conditional mean / full mean |
|---|---:|---:|---:|
| Native electron flavor | 0.3291771086 | 0.2015509907 | 0.6122873840 |
| Native muon flavor | 0.1986803491 | 0.1062885613 | 0.5349726925 |
| Frozen electron flavor | 0.3294856246 | 0.2018137947 | 0.6125116837 |
| Frozen muon flavor | 0.1988883612 | 0.1064404397 | 0.5351768152 |

The native callable returns unrenormalized samples. A deliberately renormalized
negative control restores number to one but leaves only about 61.2% and 53.5% of
the full mean energy; it changes the source prescription and cannot repair
missing endpoint support. Fixed-endpoint bin refinement converges to the clipped
moments. For any fixed `q_max`, `p_max(x)=q_max*me/x`; native clipping begins only
at `x/x_stop > 0.5109989`. The receipt includes local snapshots showing that
earlier source support can be complete. Calculating an integrated source loss
requires the actual `x(t)` history and source weights, which are absent here.

## Finite-electron-mass capture proxies and PRIMAT coverage

The static, zero-blocking Born capture weights used here are

```
K_nu(E)     = (E+Delta) sqrt[(E+Delta)^2-me^2]
K_antinu(E) = (E-Delta) sqrt[(E-Delta)^2-me^2], E >= Delta+me;
              0 otherwise.
```

They are averaged against the frozen electron-flavor `dN/dE`. This yields
source-shape proxies with units `MeV^2`, not absolute rate coefficients. The
static antineutrino threshold is `1.80433131 MeV`. Blocking, recoil, radiative,
finite-nucleon-mass and plasma corrections are absent.

At the unmodified native final domain, the frozen-source proxy retained
fractions are `0.1260750185` for neutrino capture and `0.1140858925` for
antineutrino capture. They cannot be interpreted as changes in cosmological
weak rates or abundances.

At public PRIMAT commit `4bf97d5082eee54b9df50d88f43182bb651fea80`,
`primat/weak_rates/corrections.py` uses dimensionless **electron momentum**
`p_max=max(7,30*T_gamma/me)`, with electron energy `me*sqrt(1+p^2)`. Its Python
API supplies `T_arr` in kelvin; here `T_gamma` means physical photon-temperature
energy `k_B*T_arr`, expressed in MeV. The quoted floor of seven belongs to the
public Python and C weak-rate paths; the bundled Mathematica source uses a
floor of twelve, so the quoted ceilings do not apply to that path. At
`T_gamma=0.1 MeV`, the floor gives the following static channel ceilings and
frozen-source proxy coverages, using the public default masses:

| Channel | Incoming neutrino energy ceiling (MeV) | Retained source proxy fraction |
|---|---:|---:|
| `nu_e + n -> p + e-` | 2.3199758672 | 2.5251277534e-6 |
| `anti-nu_e + p -> n + e+` | 4.9066405872 | 1.8399555660e-5 |

The earlier producer shorthand `7*me=3.58 MeV` is the electron-momentum ceiling.
Its electron-energy ceiling is `3.6133082272 MeV`; the incoming-neutrino ceilings
are this value minus/plus `Delta=1.29333236 MeV`. The current frozen producer
documents are preserved. This refinement records the precise public-source
coordinate mapping; the endpoint incompleteness conclusion is unchanged.
Gauss nodes lie strictly inside these integration intervals. The calculation
reports coverage up to the mathematical ceilings and does not measure native
PRIMAT quadrature errors or execute a nonthermal PRIMAT adapter.

## Executed controls and reproduction

The analytic moments agree with separate SciPy adaptive integration to
`3.71e-16` of the full target. Threshold-smoothed Gauss-Legendre 64/128-node
capture integrals agree with adaptive physical-energy integration to
`3.42e-14` relative error. Zero/full/clamped endpoints, monotonicity, zero
antineutrino proxy at/below threshold, and the `me=Delta=0` second-moment limit
pass. Negative controls demonstrate persistent fixed-domain deficits, false
number completeness after renormalization, and the unphysical negative
antineutrino branch admitted by a squared-only threshold condition.

The recording interface explicitly refuses `python -O`, `python -OO`, or
nonzero `PYTHONOPTIMIZE` before computing a receipt, because its scientific
controls require enabled assertions. This interface update changes no numerical
algorithms or results. Earlier unpublished receipts are preserved outside this
dossier in `/workspace/shared/dmde-source-coverage-pre-optguard/`;
`verification.json` records comparison with the prior numerical result and
refusal checks. `verify_coverage.py` independently checks the command interface
and prints its verification receipt without changing this dossier. It compares
all saved scientific JSON fields exactly, including numerical results and
public-source/code hashes, while allowing differences only inside the top-level
`runtime` object. Verification records both the baseline and executed runtime
and each allowed version difference. Fresh output files and their stdout must
match the current execution byte for byte. The prior optimization-interface
receipt comparison still permits only the executed script hash to differ from
the saved baseline, so that historical comparison retains equal runtimes.

The verifier passed in both the original SciPy 1.17.0 runtime
(`verification.json`) and the prepared native-control SciPy 1.16.3 runtime
(`verification_native_runtime.json`), with NumPy 2.3.5 and Python 3.12.14 in
both. In the latter check, SciPy's version string is the sole allowed receipt
difference; every numerical value, public-source hash and scientific code hash
matches the baseline exactly. The scientific script and its saved result are
unchanged by this verifier portability correction. The earlier verifier and
verification receipt are retained outside the dossier in
`/workspace/shared/dmde-source-coverage-pre-portability/`.

Default execution prints JSON and leaves the directory unchanged:

```bash
python source_coverage.py
```

To capture a new provenance-bearing receipt, point at clean public checkouts;
existing output paths are rejected:

```bash
python source_coverage.py \
  --nudec-dir /workspace/shared/dmde-upstream/nudec \
  --primat-dir /workspace/shared/dmde-upstream/primat \
  --output /tmp/dmde-source-coverage-replay.json
```
