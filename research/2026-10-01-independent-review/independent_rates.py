"""Independent SciPy adaptive quadrature in electron energy, all six Born rates."""
import argparse, json, math
from pathlib import Path
from scipy.integrate import quad
from scipy.special import expit
from scipy.optimize import brentq
ME=0.51099895
Q=1.29333236
TAU=879.4

def fd(energy,temperature):
    return expit(-energy/temperature)

def quad_eps(fun, lo, hi):
    return quad(fun,lo,hi,epsabs=1e-100,epsrel=3e-11,limit=300)[0]

def electron_phase(e):
    return e*math.sqrt(max(e*e-ME*ME,0.0))

I0=quad_eps(lambda e: electron_phase(e)*(Q-e)**2,ME,Q)
A=1/(TAU*I0)

def rates(t,t_nu=None):
    if t_nu is None:
        t_nu=t
    f=lambda e: fd(e,t)
    g=lambda e: fd(e,t_nu)
    # Integrate incoming-neutrino capture / electron capture in electron E >= Q.
    high=lambda e: electron_phase(e)*(e-Q)**2
    n_nu=A*quad_eps(lambda e: high(e)*g(e-Q)*(1-f(e)),Q,math.inf)
    p_e=A*quad_eps(lambda e: high(e)*f(e)*(1-g(e-Q)),Q,math.inf)
    # Electron E >= me and antineutrino energy E+Q.
    low=lambda e: electron_phase(e)*(e+Q)**2
    n_ep=A*quad_eps(lambda e: low(e)*f(e)*(1-g(e+Q)),ME,math.inf)
    p_an=A*quad_eps(lambda e: low(e)*g(e+Q)*(1-f(e)),ME,math.inf)
    beta_phase=lambda e: electron_phase(e)*(Q-e)**2
    beta=A*quad_eps(lambda e: beta_phase(e)*(1-f(e))*(1-g(Q-e)),ME,Q)
    inverse=A*quad_eps(lambda e: beta_phase(e)*f(e)*g(Q-e),ME,Q)
    n=n_nu+n_ep+beta
    p5=p_e+p_an
    p6=p5+inverse
    return dict(T_gamma_MeV=t,T_nu_MeV=t_nu,n_nu=n_nu,n_ep=n_ep,beta=beta,p_e=p_e,p_an=p_an,inverse=inverse,n=n,p5=p5,p6=p6,relative_to_p5=inverse/p5,omitted_fraction_p6=inverse/p6,p6_over_n_boltzmann_ratio=p6/n/math.exp(-Q/t),beta_fraction_n=beta/n)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Optional new JSON file; default is stdout only. Existing files are never overwritten.')
    args=parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error(f'Refusing to overwrite existing output: {args.output}')
    rows=[rates(t) for t in [.01,.02,.03,.05,.075,.1,.15,.2,.3,.5,1,3,5,10]]
    root=brentq(lambda t: rates(t)['relative_to_p5']-.1,.01,.5,xtol=1e-14)
    output={'method':'scipy.integrate.quad in electron energy, epsrel=3e-11; no imports from producer or frozen validator','I0_MeV5':I0,'tau_s':TAU,'A_s_inv_MeV_minus5':A,'equal_temperature_crossing_inverse_over_p5_0p1_MeV':root,'equal_temperature_rows':rows,'decoupled_example':rates(.1,.1*(4/11)**(1/3))}
    receipt=json.dumps(output,indent=2)+'\n'
    if args.output is not None:
        with args.output.open('x') as stream:
            stream.write(receipt)
    print(receipt,end='')
