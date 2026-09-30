# DMDE v0.9.20 analytic candidate: frozen-pair differential response

## Result status

This is a new source-level analytic and numerical-design result derived from the byte-frozen v0.9.19 provider cards and payloads. It is **not** a neutrino-transport result, weak-rate result, BBN abundance prediction, cosmological fit, or discovery claim.

The useful advance is that the blinded pair is not merely “close.” In logarithmic source-amplitude space, it is an exceptionally clean finite-difference direction for the neutrino-injection response, with a quantified electromagnetic nuisance projection and an explicit precision requirement for the production backend.

## 1. Two-amplitude representation

Both cards have the same lifetime, cutoff, muon mass, time profile, and four Michel kernels. Before transport, each card is therefore specified by two independent amplitudes:

\[
a_i=B_{\mu\mu,i}Y_{0,i},
\qquad
e_i=f_{{\rm EM},i}m_{R,i}Y_{0,i}.
\]

Here, \(a_i\) multiplies each emitted Michel spectrum and \(e_i\) multiplies the electromagnetic energy-source history. The common finite-cutoff completeness \(1-e^{-18}\) cancels from all pair ratios. The neutrino energy amplitude is exactly \(q_{\nu,i}=1.3m_\mu a_i\), while source-card energy closure gives

\[
m_{R,i}Y_{0,i}=e_i+q_{\nu,i}.
\]

Therefore the parent rest-energy abundance is not a missing third independent coordinate in this reduced frozen-source contract. It does change when \(a\) changes, however, so the \(a\)-response includes the associated neutrino-energy and parent-density/expansion response; it is not a weak-kernel-only derivative.

The audited frozen values are

| quantity | 4Q7N | 8M2K | 8M2K / 4Q7N |
|---|---:|---:|---:|
| \(a_i\), neutrino number amplitude per emitted species | \(4.03832754900946\times10^{-6}\) | \(4.073429651777095\times10^{-6}\) | 1.0086922376507683 |
| \(e_i\), EM energy amplitude (MeV) | 0.001908522352315735 | 0.0019085299596456747 | 1.0000039859789593 |
| \(m_RY_0=e_i+q_{\nu,i}\), parent rest-energy amplitude (MeV) | 0.002463210419441653 | 0.002468039507273097 | 1.001960485305408 |

The payload arrays independently reproduce these ratios pointwise to binary64 rounding: the largest ratio nonconstancy is \(4.45\times10^{-16}\).

Define

\[
u=\ln a,\qquad v=\ln e.
\]

Then the frozen contrast is

\[
\Delta u=0.008654677649784786,
\qquad
\Delta v=3.985971015349140\times10^{-6},
\]

and

\[
\rho\equiv\frac{\Delta v}{\Delta u}
=4.605568429747650\times10^{-4}.
\]

Thus the pair direction is only \(0.02638796^\circ\) from the pure-neutrino axis in \((\ln a,\ln e)\) space. Equivalently, its log neutrino contrast is 2171.2846 times its log EM contrast.

## 2. Exact differential-response identity

Let \(O(a,e)>0\) be any differentiable backend output, and write \(G=\ln O\). This could later be applied separately to \(Y_p\), D/H, or \(N_{\rm eff}\), but no value of any such output is assumed here.

Define the observable pair secant

\[
\widehat g_{\rm pair}
=\frac{G(a_2,e_2)-G(a_1,e_1)}{\Delta u}.
\]

Parameterize the straight path in log-amplitude space by

\[
u(s)=u_1+s\Delta u,
\qquad
v(s)=v_1+s\Delta v,
\qquad 0\le s\le1.
\]

The fundamental theorem of calculus gives the exact identity

\[
\boxed{
\widehat g_{\rm pair}
=\int_0^1
\left[
\frac{\partial\ln O}{\partial\ln a}
+\rho\frac{\partial\ln O}{\partial\ln e}
\right]_{(u(s),v(s))}
\,ds
}
\]

with no linear-response approximation.

Consequently, if the EM log-elasticity obeys the explicitly conditional bound

\[
\left|\frac{\partial\ln O}{\partial\ln e}\right|\le M_{\rm EM}
\]

along the pair path, then

\[
\left|
\widehat g_{\rm pair}
-\int_0^1\frac{\partial\ln O}{\partial\ln a}\,ds
\right|
\le 4.60556843\times10^{-4}M_{\rm EM}.
\]

For example, **only if** \(M_{\rm EM}\le1\), the absolute EM contamination in the recovered path-averaged neutrino elasticity is at most \(4.61\times10^{-4}\). No bound on \(M_{\rm EM}\) is asserted by the frozen source alone.

This result is stronger and safer than interpreting the raw endpoint difference as “the weak-spectrum effect”: it states exactly what the endpoint comparison measures and exposes the EM nuisance term. The neutrino coordinate intentionally includes its linked energy-density and expansion response.

## 3. Production precision needed

If each endpoint has a worst-case log-output error no larger than \(\epsilon\), then

\[
|\delta\widehat g_{\rm pair}|\le\frac{2\epsilon}{\Delta u}.
\]

Therefore:

| desired absolute accuracy in \(\widehat g_{\rm pair}\) | maximum error at each endpoint |
|---:|---:|
| 0.10 | 432.73 ppm |
| 0.05 | 216.37 ppm |
| 0.02 | 86.55 ppm |
| 0.01 | 43.27 ppm |
| 0.005 | 21.64 ppm |
| 0.001 | 4.33 ppm |

These are worst-case numerical-error allocations, not observational uncertainties.

If instead the two endpoint log-output uncertainties are independent Gaussian standard deviations \(\sigma\), an elasticity magnitude \(|g_\nu|\) produces an approximate significance

\[
Z=\frac{|g_\nu|\Delta u}{\sqrt2\,\sigma}.
\]

Some useful thresholds are:

| assumed \(|g_\nu|\) | maximum per-endpoint \(\sigma\) for 3σ | maximum per-endpoint \(\sigma\) for 5σ |
|---:|---:|---:|
| 1.00 | 2039.93 ppm | 1223.96 ppm |
| 0.30 | 611.98 ppm | 367.19 ppm |
| 0.10 | 203.99 ppm | 122.40 ppm |
| 0.03 | 61.20 ppm | 36.72 ppm |
| 0.01 | 20.40 ppm | 12.24 ppm |

The practical recommendation is to ask the external backend for repeatability and meaningful-refinement evidence at or below about **20 ppm in each positive scalar output** if sensitivity to a pair-averaged neutrino elasticity as small as 0.01 is scientifically important. If that target is unattainable, the table makes the detectable elasticity floor explicit before interpreting a null contrast.

## 4. Optional orthogonal execution canaries

The physical blinded endpoints are

\[
P_{11}=(a_1,e_1)=\text{4Q7N},
\qquad
P_{22}=(a_2,e_2)=\text{8M2K}.
\]

Two optional, nonphysical execution canaries can be assembled without altering any frozen amplitude:

\[
P_{21}=(a_2,e_1),
\qquad
P_{12}=(a_1,e_2).
\]

They permit fixed-EM neutrino secants and the exact finite mixed interaction diagnostic

\[
I_{\nu,{\rm EM}}
=\frac{
G(P_{22})-G(P_{21})-G(P_{12})+G(P_{11})
}{\Delta u\,\Delta v}.
\]

These hybrids must be labeled **execution diagnostics only**. They are not new physical branch points, must not enter blinded scoring, and do not relax the frozen-source rule. Because \(\Delta v\) is only 3.986 ppm, the EM derivative and mixed interaction are intrinsically ill-conditioned at the native contrast; an amplified EM canary would be a separate future design decision, not part of this result.

## 5. What this does and does not advance

This closes a planning ambiguity before paying the cost of a production run:

1. it gives the exact mathematical meaning of the two-card endpoint contrast;
2. it quantifies the EM nuisance projection rather than merely calling it small;
3. it establishes the numerical precision required to resolve a chosen response scale; and
4. it provides an optional factorial diagnostic capable of separating implementation response channels.

It does **not** say whether the neutrino elasticity is large, small, positive, or negative. Only a validated transport → weak-rate → BBN execution can determine that.

## Reproduction

From the extracted provider packet root:

```bash
python3 code/dmde_v0920_pair_geometry.py \
  --provider-root . \
  --json-out receipts/DMDE_v0920_FROZEN_PAIR_GEOMETRY.json \
  --csv-out tables/DMDE_v0920_PRECISION_DESIGN.csv

python3 code/dmde_v0920_validate_blind_payloads_deep.py --base .
```

Expected result: the audit prints `PASS`, followed by six passing unit tests.

After real endpoint files have passed the complete provider-return validator, the companion calculator can be used as follows:

```bash
python3 code/dmde_v0920_analyze_pair_outputs.py \
  --low-json validated_4Q7N_final_outputs.json \
  --high-json validated_8M2K_final_outputs.json \
  --geometry-json receipts/DMDE_v0920_FROZEN_PAIR_GEOMETRY.json \
  --endpoint-log-error-bound 2e-5 \
  --em-elasticity-bound 1.0 \
  --output pair_response.json
```

The calculator labels its output `CALCULATED_NOT_PHYSICS_VALIDATED` and refuses mismatched blind IDs or payload hashes. The EM bound is optional and must be supported externally; the tool does not invent it.
