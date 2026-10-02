# Nudec source-capability audit — 1 October 2026

**Result:** The official pinned Python source contains the intended prompt stopped-muon emitter and a momentum-resolved three-flavor Boltzmann evolution. It is a plausible adapter target, but its shipped interface does not satisfy the DMDE spectral bridge. This inspection identifies concrete domain, time-cutoff, normalization and evidence-export work. It does not execute neutrino transport, calculate weak rates or abundances, validate this backend, or support a DMDE mechanism.

Research program: Ricardo Maldonado. This authored source inspection and algebra were prepared with AI assistance; they are not external peer review. No private archive, scoring material or blinded payload was used. The frozen provider and upstream checkout were not modified.

## Source state and runtime

Official repository: [baugid/Nudec_LLP_Solver](https://github.com/baugid/Nudec_LLP_Solver). Inspected commit: **`0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`**, committed **21 August 2025**, message “Fixed typo in the collision integral.” The fetched `origin/master` and `origin/HEAD` point to that same commit. This establishes the fetched default-branch state, not the absence of other branches or unpublished work. The worktree was clean after checkout.

The source is Python. Its [requirements](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/requirements.txt#L1-L3) name NumPy, SciPy and Numba without versions. [Core.py lines 7–14](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Core.py#L7-L14) imports the Python transport modules and SciPy `solve_ivp`; the collision modules use Numba JIT. The repository carries [GPL v3](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/LICENSE.txt#L1-L17). A redistributed modified adapter must preserve the applicable upstream license and attribution. Source inspection does not establish that dependencies install, JIT compilation succeeds, or a transport solve completes in this environment.

`Simulator.simulate` constructs a `3*Nq+2` state of three occupations, photon-temperature variable `z`, and time in seconds, then calls RK45 with `atol=rtol=1e-9` and `t_eval=None`. It does not itself check the returned `solution.success`, and supplies no `max_step`: [Core.py lines 136–155](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Core.py#L136-L155). A later execution must verify termination and measure the actual history resolution; those tolerances are not an achieved physical precision claim.

## Source mapping: what can be established from code

The native `llp_muonBranching` is the **average number of primary muons per LLP decay**, not a pair probability: [LLP_parameters.py lines 5–9](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/LLP_parameters.py#L5-L9). Thus the public DMDE pair branch maps to `N_mu=2*B_mumu`. `density` is a physical start number density in MeV³, converted to a comoving count by `n0*(x0/me)^3`: [Core.py lines 39–47](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Core.py#L39-L47), [lines 149–151](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Core.py#L149-L151).

The batch parser distinguishes absent direct-neutrino columns from three explicitly supplied zero columns. The latter activates `directNeutrinos=True` and changes domain selection: [BatchLauncher.py lines 34–44](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/BatchLauncher.py#L34-L44). With `decayFile=None`, the batch entry point leaves the default muon and pion decay probabilities equal to one: [lines 57–64](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/BatchLauncher.py#L57-L64), [Core.py lines 57–58](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Core.py#L57-L58). The intended diagnostic should use zero pion multiplicity and omit direct-neutrino input columns.

The actual emitter [Distributions.py lines 40–58](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Distributions.py#L40-L58) implements the normalized physical-momentum densities

```text
K_e(p)  = 96 p² (1 - 2p/m_mu) / m_mu³
K_mu(p) = 48 p² (1 - 4p/(3m_mu)) / m_mu³
```

It zeros nodes above `m_mu/2` using `searchsorted(..., side='right')` on the sorted grid. The exact endpoint is included; the electron source vanishes there, while the muon-flavor source need not. Pre-mixing tau injection is zero. Native constants are **`m_mu=105.7` MeV** and **`m_e=0.5109989` MeV**, whereas the frozen source specifies `m_mu=105.6583755` MeV: [Constants.py lines 8–10](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Constants.py#L8-L10). The two endpoints are 52.85 and 52.82918775 MeV. A matching adapter must record an explicit constant override and all consumers; relabeling the unmodified output would not establish exact frozen-source identity.

Writing `c=m_e/x`, `p=c*q`, the inspected source before mixing is

```text
n_X(t) = n0 (x0/x)^3 exp(-t/tau)
(df_a/dx)_source = [N_mu n_X hbar/(2 H x tau)] K_a(p) [2 pi²/p²]
dt/dx = hbar/(H x).
```

These follow from [System_Nudecoupling.py lines 99–120](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L99-L120) and [lines 162–164](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L162-L164). Choosing and declaring a **comoving reference** `s_ref(t)=s0*(x0/x)^3` and `n0=Y0*s0` gives, for each neutrino or antineutrino species,

```text
state_dYdq_a = c p² f_a /(2 pi² s_ref)
S_a(t,q) = (N_mu/2) [Y0 exp(-t/tau)/tau] c K_a(cq).
```

This is an algebraic mapping to the public source form before cutoff, with matched constants. The backend does not implement or declare that canonical reference-entropy map. An evolving plasma entropy density cannot be silently substituted for `s_ref`; plasma heating and QED conventions need their own records.

Only three occupations evolve. The RHS makes antineutrino occupations equal by copying them, and the source factor `1/2` accounts for shared neutrino/antineutrino production: [System_Nudecoupling.py lines 76–84](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L76-L84), [lines 113–120](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L113-L120). This is an imposed charge-symmetry approximation, not six independently evolved histories. Its applicability requires review for the specified charge-symmetric source and plasma. Averaged mixing is applied to injection at [lines 122–124](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L122-L124), then mixed collision contributions are added at [lines 129–143](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L129-L143). The canonical source must therefore be exported **before** the mixing assignment; tau can become populated afterward.

## Concrete blockers and required evidence

| Topic | Inspected behavior | Consequence for an adapter |
|---|---|---|
| Physical endpoint | `ylimit=max(x_stop*m_mu/2,40)` without direct injection; physical `p=q*m_e/x`. [Core 66–74](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Core.py#L66-L74), [RHS 113–114](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L113-L114). | Where the muon term dominates, the upper physical momentum at `x_stop` is `m_e*m_mu/2`, about 27.00629 MeV with native constants, rather than 52.85 MeV. Use `q_max*c(t)>=m_mu/2` throughout actual injection and validate returned support. |
| Grid refinement | Uniform positive grid with composite three-node integration weights; default 301 bins. [Momentum_Grid 72–90](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Momentum_Grid.py#L72-L90), [GlobalParameters 5–7](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/GlobalParameters.py#L5-L7). | Increasing the boundary at fixed bin count coarsens thermal and weak-threshold sampling. Domain extension and local resolution need separate checks; the positive lower cutoff also needs adequacy checks. |
| Actual time cutoff | `limitInjection` interpolates fixed `scaleFactorTime.csv` at `tau*lifetimeFactor`; injection tests `x<stopPoint`. [Core 76–89](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Core.py#L76-L89), [RHS 116–120](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L116-L120). | Setting `lifetimeFactor=18` does not prove the frozen half-open actual-time condition `0<=t<18*tau` when expansion changes. Implement and witness the intended time gate and define the time origin. |
| Full histories | `getSolution` exposes the in-memory solver result, but the shipped text exporter writes `a,t,T` and only the final three spectra. [Core 172–209](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Core.py#L172-L209). | Full occupation histories can be exported by an adapter. Six declared symmetry-related histories, grid weights, background component histories and canonical states are additional evidence, not present in shipped text output. |
| Source and stepper witnesses | The source is accumulated inside `System_Nudec`, transformed by mixing, then combined with collisions; the full RHS alone is returned. [RHS 113–168](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L113-L168). | Instrument the actual pre-mixing accumulator, its unit conversion and a source toggle. Produce same-state source-on/off production-stepper witnesses at `h` and `h/2`; ideal reconstructed Michel sidecars do not establish actual source consumption. |
| Weak/BBN handoff | This tree provides transport, collision and thermodynamic code; no shipped weak-rate histories, nuclear network or BBN canary handoff were identified. | A separate corrected, domain-complete six-process rate adapter and instrumented nuclear consumer are required. The current frozen five-column sum contract must remain intact; complete six-process outputs need a separately versioned supplement. |

The endpoint discrepancy is a direct consequence of the two inspected expressions, not a measured production-run error. No abundance impact is inferred. The time-cutoff issue similarly identifies a condition that must be tested, without estimating its magnitude for an unrun history.

## Energy bookkeeping that needs execution evidence

The Hubble density includes photons, ideal electrons/positrons, neutrinos and antineutrinos, QED corrections, and the parent density: [System_Nudecoupling.py lines 90–108](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L90-L108); explicit six-species neutrino energy counting is in [Thermodynamics_ideal_gas.py lines 11–20](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Thermodynamics/Thermodynamics_ideal_gas.py#L11-L20). The temperature RHS uses the neutrino-energy derivative, including collision exchange, and the negative parent-deposition term: [System_Nudecoupling.py lines 145–160](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L145-L160).

The source functions have mean neutrino energies `0.30*m_mu` and `0.35*m_mu`. Consequently the prompt source puts `0.65*N_mu*m_mu=1.3*B_mumu*m_mu` into all neutrinos per parent decay; the source contribution to plasma heating uses the remaining parent energy. This is an algebraic source-only interpretation of the active RHS, not a numerical energy-conservation test. No independent electromagnetic source history is exported. A test must separate the source-only neutrino moment from collision energy transfer and verify the combined parent/plasma/neutrino continuity equation with the stated equation of state.

After the `x` cutoff, the parent density in the Hubble term still contains `exp(-t/tau)`, while parent deposition is set to zero: [lines 99–104](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L99-L104), [lines 153–157](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py#L153-L157). The adapter must state how the remaining parent tail is handled and test or bound the residual continuity term. At an actual cutoff of `18*tau`, the exponential fraction is about `1.52e-8`; that alone does not give a bound on any final observable or establish this backend reaches that actual cutoff time.

## Next executable diagnostic

The next bounded calculation should call the **inspected native `muonDistribution` and native grid builder**, without invoking `SingleShot`, `BatchLauncher`, `System_Nudec`, collision JIT or a full solve. Choose an explicit unblinded test grid and coordinate, record native constants and executed source hashes, and integrate moments `k=0,...,5` with the returned native weights converted by `dp/dq=m_e/x`. Compare them with analytic Michel moments, and repeat on finer grids and on deliberately clipped versus endpoint-complete domains. Record the native/frozen mass distinction rather than making it disappear through an undisclosed override. Expected checks include finite nonnegative source, zero tau source, physical support, unit multiplicities, analytic energy moments, and independent stability under refinement.

A successful emitter probe establishes source shape and quadrature behavior only. It does not execute the time-dependent source RHS, energy coupling, oscillations, collisions, actual source cutoff, canonical occupation map or paired production-stepper response. Those are the next adapter requirements. A failed or clipped probe should retain its raw negative evidence; it must not be repaired by normalizing a truncated spectrum after the fact.

Only after source instrumentation, exact-time/domain checks, and a matched zero-source transport control should evolved spectra be passed to a six-process weak-rate adapter. Thermal detailed balance must not replace direct integration of transported occupations. Full-domain rate convergence, recoil/radiative/plasma corrections, cache-independent nuclear consumption and an abundance precision budget remain subsequent gates. None of this source inspection changes the established limitations of DMDE's unspecified late-time dark-energy sector.

## Provenance and scope

`SOURCE_CAPABILITY_PROVENANCE.json` records source identity, fetched refs, SHA-256 values for all tracked upstream members and the public specification files used, inspected paths, and immutable citation anchors. Hashing and source/AST inspection execute trusted inspection tools; no upstream Python module or backend callable was imported or run for this audit. The numerical examples above are arithmetic/algebra from inspected constants and formulas, not transport results. Public source hashes identify bytes; they do not certify numerical or physical correctness.
