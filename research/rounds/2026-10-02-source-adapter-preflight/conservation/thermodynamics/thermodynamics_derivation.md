# Independent NuDec thermodynamic audit

This read-only audit uses NuDec commit `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62` at `/workspace/shared/dmde-upstream/nudec`. It derives a continuum thermodynamic reference, identifies differences in the native energy functions, and states the limits of a conservation interpretation. No upstream code was edited and no parameters were tuned.

## Variables and physical densities

Write `q` for the native numerical momentum coordinate (called `y` in the upstream code). Its conversion to physical momentum is fixed by the native numerical convention

\[
a_{\rm native}=x/m_e,\qquad c=m_e/x,
\qquad T_\gamma=z/a_{\rm native}=cz,\qquad p=q/a_{\rm native}=cq.
\]

`Core.py:187–191` exports exactly these numerical conversions; `System_Nudecoupling.py:114` also converts the neutrino grid to physical momentum. With the physical electron mass declared in MeV (`Constants.py:8`), `c` is the physical MeV-per-unit-`q` conversion, and `p` and `T_\gamma` above are physical values in MeV. The scale-factor normalization is arbitrary. Neither the grid docstring nor these numerical relations independently certifies dimensions for `q`, `x`, or `z`, or establishes that `a_native` is dimensionless. In the native coordinate notation define `E_y=\sqrt{y^2+x^2}`, `f_e=(\exp(E_y/z)+1)^{-1}`, and rescaled densities `\bar\rho=\rho/c^4`, `\bar P=P/c^4`. These are the quantities appearing in the native fourth-power rescaling, rather than energy in a comoving volume.

For zero electron chemical potential and massless neutrinos,

\[
\bar\rho_\gamma={\pi^2z^4\over15},\qquad
\bar P_\gamma={\bar\rho_\gamma\over3},
\]
\[
\bar\rho_e={2\over\pi^2}\int_0^\infty dy\,y^2E_yf_e,
\qquad
\bar P_e={2\over3\pi^2}\int_0^\infty dy\,{y^4\over E_y}f_e,
\]
\[
\bar\rho_\nu={1\over2\pi^2}\sum_\alpha\int_0^\infty dy\,y^3(f_\alpha+\bar f_\alpha),
\qquad \bar P_\nu={\bar\rho_\nu\over3}.
\]

Physical energy density and pressure in MeV to the fourth power are obtained by multiplying each barred expression by `c^4=(m_e/x)^4`. NuDec identifies neutrino and antineutrino distributions (`System_Nudecoupling.py:79–81`), so its neutrino expression becomes `\bar\rho_\nu=\pi^{-2}\sum_\alpha\int y^3f_\alpha dy`.

The native electron coefficient `2/pi^2` is correct for the four spin/particle degrees of freedom of `e^-` and `e^+`; there is no ideal-electron factor-of-two normalization defect. The native functions are in `Thermodynamics/Thermodynamics_ideal_gas.py:14–20`. Native electrons and neutrinos use `gridVals/gridWeights`; `Momentum_Grid.py:86–90` constructs a composite Simpson grid. The photon expression is used in `System_Nudecoupling.py:103`.

## Pressure identities and QED corrections

At fixed `x`, an equilibrium component with zero chemical potential obeys

\[
\bar\rho=z\,\partial_z\bar P-\bar P.
\]

Use the native QED-grid quantities

\[
A=2\int dy\,{y^2\over E_y}f_e,\qquad
I=2\int dy\,{2y^2+x^2\over E_y}f_e.
\]

They are native `tmp` in `P_2` and native `I` in `Thermal_QED_corrections.py:20–29,50–58`. The consistent pressure corrections are

\[
\bar P_2=-{e^2z^2\over12\pi^2}A-{e^2\over8\pi^4}A^2,
\qquad
\bar P_3={e^3z\over12\pi^4}I^{3/2}.
\]

The cubic coefficient follows from the Debye pressure `P_3=T m_D^3/(12\pi)`, with `\bar m_D^2=e^2 I/\pi^2`. In the massless continuum limit `I=\pi^2z^2/3`, so this gives the usual `m_D^2=e^2T^2/3`. The coefficient is independently consistent with the native `G3_1,G3_2`, as shown below.

The corresponding energy corrections are

\[
\bar\rho_2=-\bar P_2+z\left[-{e^2z\over6\pi^2}A
-{e^2z^2\over12\pi^2}A_z
-{e^2\over4\pi^4}AA_z\right],
\]
\[
\bar\rho_3={e^3z^2\over8\pi^4}\sqrt I\,I_z.
\]

Two native differences are explicit:

1. `dP_2dz` uses `-e^2 AA_z/(4*pi^2)` at `Thermal_QED_corrections.py:44–45`; differentiating its own `P_2` requires the denominator `4*pi^4`.
2. Native `rho_3` uses `x^2` at `Thermal_QED_corrections.py:15`; the pressure identity and native `G3` require `z^2`.

For the same finite QED grid, these exact algebraic differences are

\[
\bar\rho_{2,\mathrm{native}}-\bar\rho_{2,\mathrm{pressure}}
=-{e^2z\over4\pi^4}(\pi^2-1)AA_z,
\]
\[
\bar\rho_{3,\mathrm{native}}
={x^2\over z^2}\bar\rho_{3,\mathrm{pressure}}.
\]

The ideal-gas energy and these two QED differences must be kept separate when attributing a total conservation residual.

## Consistency with the native temperature functions

Write `w=x/z`, `S=K+w^2k/2`, `h=2J+w^2j`, and let a prime mean the continuum derivative with respect to `w`. The native definitions imply

\[
A=2\pi^2z^2K,\quad A_z=2\pi^2zJ,
\quad I=4\pi^2z^2S,\quad I_z=2\pi^2zh.
\]

The integration-by-parts relations in the continuum are

\[
K'=-wk,\quad k'=-j/w,\quad J'=-wj,\quad Y'=-3wJ,
\quad J=2K-wK',\quad 2S-wS'=h/2.
\]

Thus, for the cubic pressure above,

\[
\bar\rho_3={e^3z^4\over2\pi}\sqrt S\,h,
\]
\[
{\partial_z\bar\rho_3\over2z^3}
={e^3\sqrt S\over4\pi}\left(3h-wh'+{h^2\over4S}\right).
\]

This is exactly the native `G3_2` (`Thermal_QED_corrections.py:98–101`) after using `Y'=-3wJ` and `J'=-wj`. Likewise,

\[
{(\bar\rho_3-3\bar P_3)/x-\partial_x\bar\rho_3\over2z^3}
={e^3\sqrt S\over4\pi}\left({h-4S\over w}-h'-{hS'\over2S}\right)
\]

equals native `G3_1` (`Thermal_QED_corrections.py:93–96`), because `w(k-j)+K'=2S'`.

For the quadratic pressure, set `F=K/6+J/6-K^2/2+KJ`. Then

\[
\bar\rho_{2,\mathrm{pressure}}=-e^2z^4F,
\quad {\partial_z\bar\rho_{2,\mathrm{pressure}}\over2z^3}
=-2e^2F+{e^2w\over2}F'.
\]

This agrees with native `G2_2` (`Thermal_QED_corrections.py:88–91`). Native `G2_1` (`:85–86`) similarly equals the quadratic continuity numerator. The native temperature functions therefore represent the continuum pressure-consistent reference, while the native QED energy functions have the two explicit differences above.

For photons plus ideal electrons,

\[
{\partial_z(\bar\rho_\gamma+\bar\rho_e)\over2z^3}
={2\pi^2\over15}+w^2J+Y,
\]
\[
{(\bar\rho_\gamma+\bar\rho_e-3\bar P_\gamma-3\bar P_e)/x
-\partial_x(\bar\rho_\gamma+\bar\rho_e)\over2z^3}=wJ.
\]

These are the ideal terms in native `dzdx` (`System_Nudecoupling.py:159–160`). Its neutrino feedback `drho_nudx` (`:150–151`) is `\bar\rho_\nu'/(2z^3)` after including antineutrinos; its apparent one-half factor is correct.

## What a conservation residual establishes

For an isotropic sector receiving physical energy `Q` per natural-unit time,

\[
{d\bar\rho\over dx}={\bar\rho-3\bar P\over x}+{Q\over c^4Hx}.
\]

For a closed sum of plasma, neutrinos, and a nonrelativistic parent with `P_parent=0`, internal transfers cancel. The useful local residual is

\[
R={d\bar\rho_{\rm total}\over dx}
-{\bar\rho_{\rm total}-3\bar P_{\rm total}\over x}.
\]

Equivalently, the equilibrium plasma equation uses `C=\partial_z\bar\rho_plasma/(2z^3)` and `N=[(\bar\rho_plasma-3\bar P_plasma)/x-\partial_x\bar\rho_plasma]/(2z^3)`, with `C z'=N-\bar\rho_\nu'/(2z^3)+Q_plasma/(2z^3c^4Hx)`.

A finite residual obtained with the literal native energy functions does not by itself prove an adapter transfer defect: those functions already disagree with the pressure-consistent QED thermodynamics. Conversely, a small pressure-consistent residual demonstrates a local energy-balance check for the evaluated state and source bookkeeping; it does not establish trajectory accuracy, collision-integral accuracy, or a cosmological observable.

The formulas identifying the two QED energy differences hold algebraically for the fixed native QED grid. The exact homogeneous identities and integration-by-parts relations used to identify `G` apply to continuum integrals with vanishing endpoint terms. Native `Momentum_Grid.py:93–97` uses a separate fixed QED grid of 81 points over `[0.01,20]`; ideal energy uses the neutrino grid instead. Fixed momentum cutoffs fail to scale with `x,z`, so changing variables to `u=y/z` moves the endpoints. Boundary terms and quadrature error therefore break exact homogeneous/continuity identities even after the two QED expressions are made pressure-consistent. Such discrepancies should be measured and reported separately, without treating a reference replacement as a native-code repair.
