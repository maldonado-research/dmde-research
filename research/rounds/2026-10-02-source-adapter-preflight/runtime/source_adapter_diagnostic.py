#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Bounded fixed-state native-source adapter diagnostic, never a trajectory.

Only the runtime source catalog is replaced. Native constants, EOS, collision
term, mixing, and RHS implementation are retained. Output is a fresh directory
reserved atomically before any artifacts are written; failures preserve logs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
SOURCE = Path('/workspace/shared/dmde-upstream/nudec')
EXPECTED_HEAD = '0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62'
ME = 0.5109989
MMU_SOURCE = 105.6583755
SPECIES = ('nue', 'nuebar', 'numu', 'numubar', 'nutau', 'nutaubar')
THREAD_ENV = {'PYTHONDONTWRITEBYTECODE': '1', 'OMP_NUM_THREADS': '1',
              'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
              'NUMEXPR_NUM_THREADS': '1', 'NUMBA_NUM_THREADS': '1'}
DECLARATION = {
    'schema': 'DMDE-fixed-state-native-source-adapter-v1',
    'status': 'predeclared_before_execution', 'private_inputs': False,
    'upstream_commit': EXPECTED_HEAD,
    'native_transport_me_MeV': ME, 'source_muon_mass_MeV': MMU_SOURCE,
    'native_muon_mass_MeV_unchanged': 105.7,
    'x0': 0.1, 'z0': 1.00003, 'g_s_ref': 10.75,
    'normalization': 'T_ref=z0*me/x0; s0=2*pi^2/45*g_s_ref*T_ref^3; s_ref(x)=s0*(x0/x)^3; C0=s0*(x0/me)^3; llp_count=Y0*C0',
    'B_mumu': 0.4, 'N_mu': 0.8, 'Y0': 1e-6, 'tau_seconds': 10.0,
    'parent_mass_MeV': 300.0,
    'x': 4.0, 'z': 1.4, 'state_t_seconds': 1.0,
    'n': 65, 'q_min': 0.01, 'q_max_formula': '4.1*m_mu_source/(2*me_native)',
    'fd_occupations': 'all three native flavors f(q)=1/(exp(q/z)+1); native antineutrinos copied',
    'catalog': '[authored frozen_michel callback]', 'native_branches': [0.8],
    'callback': 'physical dN/dp Michel shapes, hard actual 0<=p<=m_mu_source/2 support; mu decay probability1; no snap, renormalization or epsilon',
    'source_toggle': 'callback phi versus callback zero, identical positive parent count and native gate; this redirects neutrino energy to EM and is not entire decay off',
    'native_gate': 'stopPoint=nextafter(actual x,+inf) iff 0<=actual state t<18*tau; otherwise0',
    'negative_time_policy': 'reject actual state t<0 at wrapper interface before native RHS; recorded gate decision false is not a physical negative-time evaluation',
    'time_gate_cases': [
        {'tag': 't_zero', 'x': 4.0, 't': 0.0},
        {'tag': 't_left_18tau', 'x': 4.0, 't': math.nextafter(180.0, -math.inf)},
        {'tag': 't_exact_18tau', 'x': 4.0, 't': 180.0},
        {'tag': 't_right_18tau', 'x': 4.0, 't': math.nextafter(180.0, math.inf)},
        {'tag': 'x_small_t_late', 'x': 0.25, 't': 181.0},
        {'tag': 'x_large_t_early', 'x': 4.05, 't': 1.0},
        {'tag': 't_negative_rejected', 'x': 4.0, 't': -0.01},
    ],
    'worker_timeout_seconds': 60,
    'coefficient_relative_tolerance': 1e-10,
    'frozen_full_stepper_source_relative_ceiling': 0.005,
    'scope': 'real native fixed-state RHS calls with compiled collision term; no integration, cosmological trajectory, weak rates, BBN, fit, production or physics validation',
    'grid_limit': 'N65 is a deliberately coarse local fixture; source moments and thermal occupations are not certified; do not infer trajectory convergence',
    'known_blockers': ['native unsplit mixing modifies preoscillation source and produces a tau response',
                       'independent native QED P2 derivative and rho3 identity inconsistencies'],
}


def write_json(path, value):
    serialized = json.dumps(value, indent=2, sort_keys=True, allow_nan=False)
    with Path(path).open('x', encoding='utf-8') as handle:
        handle.write(serialized + '\n')


def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(SOURCE), *args], text=True).strip()


def source_snapshot():
    names = sorted(filter(None, git('ls-files', '-z').split('\0')))
    result = {'source': str(SOURCE), 'head': git('rev-parse', 'HEAD'),
              'tree': git('rev-parse', 'HEAD^{tree}'),
              'porcelain': git('status', '--porcelain=v1', '--untracked-files=all'),
              'tracked_file_sha256': {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() for name in names}}
    if result['head'] != EXPECTED_HEAD or result['porcelain'] or len(names) != 21:
        raise RuntimeError('Native source must be the clean pinned21-file checkout')
    return result


def versions():
    import numpy, scipy, numba, llvmlite
    result = {'python': platform.python_version(), 'numpy': numpy.__version__,
              'scipy': scipy.__version__, 'numba': numba.__version__, 'llvmlite': llvmlite.__version__}
    expected = {'numpy': '2.3.5', 'scipy': '1.16.3', 'numba': '0.63.1', 'llvmlite': '0.46.0'}
    if any(result[k] != v for k, v in expected.items()):
        raise RuntimeError(f'Runtime package pin mismatch: {result}')
    return result


def native_module_receipt():
    result = {}
    for name, module in sorted(sys.modules.items()):
        file = getattr(module, '__file__', None)
        if file and Path(file).resolve().is_relative_to(SOURCE):
            result[name] = {'path': str(Path(file).resolve()),
                            'sha256': hashlib.sha256(Path(file).read_bytes()).hexdigest()}
    return result


def native_scalar_globals():
    result = {}
    for name, module in sorted(sys.modules.items()):
        file = getattr(module, '__file__', None)
        if file and Path(file).resolve().is_relative_to(SOURCE):
            # Native RHS progress counters naturally mutate; no setup or physics
            # global is assigned by the adapter after setupGrid.
            scalars = {k: float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v
                       for k, v in vars(module).items()
                       if not k.startswith('__') and k not in ('callNumber', 'lastPrintTime')
                       and isinstance(v, (bool, int, float, str))}
            result[name] = scalars
    return result


def frozen_michel(momentum, x, decay_probabilities):
    """Authored physical3xN dN/dp callback; owns only the source muon mass."""
    import numpy as np
    p = np.asarray(momentum)
    result = np.zeros((3, len(p)), dtype=float)
    support = (p >= 0.0) & (p <= MMU_SOURCE / 2.0)
    active = p[support]
    result[0, support] = 96 * active**2 * (1 - 2 * active / MMU_SOURCE) / MMU_SOURCE**3
    result[1, support] = 48 * active**2 * (1 - 4 * active / (3 * MMU_SOURCE)) / MMU_SOURCE**3
    return float(decay_probabilities['mu']) * result


def independent_mixing(constants, temperature, p):
    """Direct scalar rotation construction, separate from native implementation."""
    import numpy as np
    matrices = []
    for momentum in p:
        matter = constants.MSWPrefactor * float(momentum)**2 * temperature**4
        th12 = math.atan2(constants.ds12, constants.dc12 + matter / constants.Dm21sq) / 2
        th13 = math.atan2(constants.ds13, constants.dc13 + matter / constants.Dm31sq) / 2
        th23 = math.asin(constants.s23)
        a, b, c = (math.cos(th12), math.cos(th13), math.cos(th23))
        sa, sb, sc = (math.sin(th12), math.sin(th13), math.sin(th23))
        u = np.array([[1., 0., 0.], [0., c, sc], [0., -sc, c]]) @ np.array([[b, 0., sb], [0., 1., 0.], [-sb, 0., b]]) @ np.array([[a, sa, 0.], [-sa, a, 0.], [0., 0., 1.]])
        squared = u * u
        matrices.append(squared @ squared.T)
    return np.array(matrices)


class NativeSourceAdapter:
    def __init__(self, system, distributions, grid, parent_count):
        self.system, self.distributions, self.grid = system, distributions, grid
        self.parent_count = parent_count
        self.captures = []
        self.context = {}
        self.distributions.getDistribution = [self.callback]

    def callback(self, p, x, decay_probabilities):
        import numpy as np
        phi = frozen_michel(p, x, decay_probabilities)
        if not self.context['source_on']:
            phi = np.zeros_like(phi)
        self.captures.append({'x': float(x), 'actual_state_t_seconds': self.context['t'],
                              'source_on': self.context['source_on'],
                              'momenta_MeV': np.array(p, copy=True), 'phi': phi.copy()})
        return phi

    def gate(self, x, state):
        t = float(state[3 * self.grid.n + 1])
        active = 0.0 <= t < 18 * DECLARATION['tau_seconds']
        return {'actual_x': float(x), 'actual_state_t_seconds': t,
                'time_gate_on': active,
                'stopPoint': math.nextafter(float(x), math.inf) if active else 0.0,
                'negative_time_interface_rejected': t < 0.0}

    def evaluate(self, x, state, source_on=True, parent_count=None, force_native_gate_off=False):
        import numpy as np
        if not math.isfinite(x) or x <= 0 or state.shape != (3 * self.grid.n + 2,) or not np.isfinite(state).all():
            raise ValueError('Finite positive x and a finite native state of declared length are required')
        decision = self.gate(x, state)
        self.captures.clear()
        if decision['negative_time_interface_rejected']:
            raise ValueError('Negative state time is rejected before calling native RHS')
        self.context = {'t': decision['actual_state_t_seconds'], 'source_on': bool(source_on)}
        stop = 0.0 if force_native_gate_off else decision['stopPoint']
        started = time.perf_counter()
        vector = self.system.System_Nudec(float(x), state.copy(), self.parent_count if parent_count is None else float(parent_count),
                                         DECLARATION['tau_seconds'], DECLARATION['parent_mass_MeV'],
                                         [2 * DECLARATION['B_mumu']], stop, lambda t: {'mu': 1.0})
        if vector.shape != state.shape or not np.isfinite(vector).all():
            raise RuntimeError('Actual native RHS returned an invalid vector')
        return vector, {**decision, 'effective_native_stopPoint': stop,
                        'elapsed_seconds': time.perf_counter() - started,
                        'source_on': bool(source_on), 'callback_count': len(self.captures)}


def csv(path, columns, array):
    import numpy as np
    with Path(path).open('x', encoding='utf-8') as handle:
        np.savetxt(handle, array, delimiter=',', header=','.join(columns), comments='', fmt='%.17g')


def worker(out):
    import numpy as np
    worker_source_before = source_snapshot()
    write_json(out / 'source_before.json', worker_source_before)
    write_json(out / 'worker_runtime.json', {'versions': versions(), 'python_executable': sys.executable})
    sys.path.insert(0, str(SOURCE))
    constants = importlib.import_module('Constants')
    grid = importlib.import_module('Momentum_Grid')
    distributions = importlib.import_module('Distributions')
    if constants.me != ME or constants.mmu != 105.7:
        raise RuntimeError('Unexpected native masses; global overrides are forbidden')
    grid.setupGrid(4.1 * MMU_SOURCE / (2 * ME), DECLARATION['n'], DECLARATION['q_min'])
    system = importlib.import_module('System_Nudecoupling')
    collision_module = importlib.import_module('Collision_term.Collision_term_diagonal')
    before_globals = native_scalar_globals()
    reference_temperature = DECLARATION['z0'] * ME / DECLARATION['x0']
    s0 = 2 * np.pi**2 / 45 * DECLARATION['g_s_ref'] * reference_temperature**3
    c0 = s0 * (DECLARATION['x0'] / ME)**3
    parent_count = DECLARATION['Y0'] * c0
    adapter = NativeSourceAdapter(system, distributions, grid, parent_count)
    q, weights = grid.gridVals.copy(), grid.gridWeights.copy()
    x, z = DECLARATION['x'], DECLARATION['z']
    f = 1 / (np.exp(q / z) + 1)
    state = np.concatenate((f, f, f, [z, DECLARATION['state_t_seconds']]))
    write_json(out / 'normalization.json', {'T_ref_MeV': reference_temperature, 's0_MeV3': float(s0),
                                         'C0': float(c0), 'llp_count': float(parent_count),
                                         's_ref_fixture_MeV3': float(s0 * (DECLARATION['x0'] / x)**3),
                                         'source_species_order': SPECIES, 'J_state_units': 'yield per dq',
                                         'S_source_units': 'yield per dq per second'})
    vectors, runs, captures = {}, {}, {}

    def execute(tag, xx, actual_state, source_on=True, count=None, force_off=False):
        vector, info = adapter.evaluate(xx, actual_state, source_on, count, force_off)
        vectors[tag], runs[tag] = vector.copy(), info
        records = []
        for item in adapter.captures:
            records.append({**item, 'momenta_MeV': item['momenta_MeV'].tolist(), 'phi': item['phi'].tolist()})
        captures[tag] = records
        canonical_f = np.repeat(actual_state[:3 * grid.n].reshape(3, grid.n), 2, axis=0)
        j = q*q * canonical_f / (2 * np.pi**2 * c0)
        p = q * ME / xx
        write_json(out / f'{tag}.json', {'actual_state': actual_state.tolist(), 'actual_native_dstate_dx': vector.tolist(),
                                       'run': info, 'callback_captures': records,
                                       'actual_canonical_occupations': canonical_f.tolist(), 'J_state': j.tolist()})
        csv(out / f'{tag}_rhs.csv', ('index', 'actual_state', 'actual_native_dstate_dx'),
            np.column_stack((np.arange(len(vector)), actual_state, vector)))
        csv(out / f'{tag}_occupations.csv', ('q', 'p_MeV', 'native_dq_weight', *('f_' + a for a in SPECIES), *('J_' + a for a in SPECIES)),
            np.column_stack((q, p, weights, canonical_f.T, j.T)))
        for serial, item in enumerate(records):
            csv(out / f'{tag}_callback{serial}.csv', ('q', 'p_MeV', 'phi_e', 'phi_mu', 'phi_tau'),
                np.column_stack((q, item['momenta_MeV'], np.array(item['phi']).T)))
        return vector

    execute('source_on', x, state, True)
    execute('source_zero_same_parent_gate', x, state, False)
    execute('native_gate_off_same_parent', x, state, True, force_off=True)
    execute('zero_parent_source_on', x, state, True, count=0.)
    execute('zero_parent_source_zero', x, state, False, count=0.)
    phi = np.array(captures['source_on'][0]['phi'])
    p = np.array(captures['source_on'][0]['momenta_MeV'])
    actual_t = float(state[-1])
    decay_factor = (DECLARATION['N_mu'] / 2) * DECLARATION['Y0'] * math.exp(-actual_t / DECLARATION['tau_seconds']) / DECLARATION['tau_seconds']
    expected_pre3 = decay_factor * (ME / x) * phi
    expected_pre6 = np.repeat(expected_pre3, 2, axis=0)
    measured_dtdx = float(vectors['source_on'][-1])
    source_delta = vectors['source_on'] - vectors['source_zero_same_parent_gate']
    actual_djdt3 = q*q / (2 * np.pi**2 * c0) * source_delta[:-2].reshape(3, grid.n) / measured_dtdx
    mixed_matrix = independent_mixing(constants, z * ME / x, p)
    expected_mixed3 = np.einsum('nij,jn->in', mixed_matrix, expected_pre3)
    native_matrix = system.calcMixingMatrixes(z * ME / x, p)
    reconstructed_dfdx = (2 * np.pi**2 * c0) / (q*q) * expected_mixed3 * measured_dtdx
    expected_scale = float(np.max(np.abs(expected_mixed3)))
    coefficient_error = float(np.max(np.abs(actual_djdt3 - expected_mixed3)) / expected_scale)
    full_stepper_error = float(np.max(np.abs(actual_djdt3 - expected_pre3)) / float(np.max(np.abs(expected_pre3))))
    actual6 = np.repeat(actual_djdt3, 2, axis=0)
    mixed6 = np.repeat(expected_mixed3, 2, axis=0)
    csv(out / 'canonical_sources.csv', ('q', 'p_MeV', *('S_pre_' + a for a in SPECIES), *('actual_native_dJdt_source_' + a for a in SPECIES), *('independent_mixed_S_' + a for a in SPECIES)),
        np.column_stack((q, p, expected_pre6.T, actual6.T, mixed6.T)))
    csv(out / 'source_only_delta.csv', ('index', 'actual_source_delta_dstate_dx'),
        np.column_stack((np.arange(len(source_delta)), source_delta)))
    write_json(out / 'coefficient_witness.json', {'captured_phi3': phi.tolist(), 'canonical_S_pre6': expected_pre6.tolist(),
                                               'actual_native_source_dJdt6': actual6.tolist(), 'independent_mixed_S6': mixed6.tolist(),
                                               'independent_mixing_matrix_N3x3': mixed_matrix.tolist(),
                                               'native_mixing_matrix_N3x3': native_matrix.tolist(),
                                               'reconstructed_neutrino_dfdx3': reconstructed_dfdx.tolist(),
                                               'measured_native_dtdx': measured_dtdx,
                                               'coefficient_error_relative_peak': coefficient_error,
                                               'coefficient_tolerance': DECLARATION['coefficient_relative_tolerance'],
                                               'source_only_delta_dzdx': float(source_delta[-2]),
                                               'source_only_delta_dtdx': float(source_delta[-1]),
                                               'sum_flavors_relative_error_peak': float(np.max(np.abs(actual_djdt3.sum(axis=0) - expected_pre3.sum(axis=0))) / expected_scale),
                                               'mixing_matrix_max_abs_native_minus_independent': float(np.max(np.abs(native_matrix - mixed_matrix))),
                                               'independence': 'expected coefficient authored from declared yield, source multiplicity, captured physical phi, coordinate Jacobian, independently constructed mixing, and measured native dtdx; not read from RHS source coefficient'})
    gate_cases = []
    for case in DECLARATION['time_gate_cases']:
        actual_state = state.copy()
        actual_state[-1] = case['t']
        if case['t'] < 0:
            decision = adapter.gate(case['x'], actual_state)
            try:
                adapter.evaluate(case['x'], actual_state)
            except ValueError as error:
                gate_cases.append({**case, **decision, 'rejection': str(error), 'native_rhs_called': False})
            else:
                raise AssertionError('Negative actual state time was not rejected')
            continue
        on = execute(case['tag'] + '_on', case['x'], actual_state, True)
        on_info = runs[case['tag'] + '_on']
        off = execute(case['tag'] + '_zero', case['x'], actual_state, False)
        delta = on - off
        gate_cases.append({**case, **on_info, 'native_rhs_called': True,
                           'callback_count_on': len(captures[case['tag'] + '_on']),
                           'source_toggle_neutrino_peak': float(np.max(np.abs(delta[:-2]))),
                           'source_toggle_vectors_bitwise_equal': bool(np.array_equal(on, off))})
    write_json(out / 'time_gate_cases.json', gate_cases)
    after_globals = native_scalar_globals()
    zero_equal = bool(np.array_equal(vectors['zero_parent_source_on'], vectors['zero_parent_source_zero']))
    collision = collision_module.Collision_term_diagonal
    checks = {
        'actual_preoscillation_phi_tau_exactly_zero': bool(np.all(phi[2] == 0.)),
        'actual_callback_support_mask_is_exact': bool(np.all(phi[:, (p < 0) | (p > MMU_SOURCE / 2)] == 0.)),
        'source_zero_callback_exactly_zero': bool(np.all(np.array(captures['source_zero_same_parent_gate'][0]['phi']) == 0.)),
        'zero_parent_source_toggle_vectors_bitwise_equal': zero_equal,
        'same_parent_source_toggle_dtdx_bitwise_equal': bool(vectors['source_on'][-1] == vectors['source_zero_same_parent_gate'][-1]),
        'native_physics_and_setup_scalar_globals_unchanged': before_globals == after_globals,
        'native_collision_nopython_compiled': bool(collision.nopython_signatures),
        'native_numba_JIT_enabled': not importlib.import_module('numba').config.DISABLE_JIT,
        'independent_native_RHS_coefficient_witness_passed': coefficient_error <= DECLARATION['coefficient_relative_tolerance'],
        'actual_source_tau_response_positive': bool(np.max(np.abs(actual_djdt3[2])) > 0.),
        'all_nonnegative_time_gates_agree_with_actual_state_time': all(a['callback_count_on'] == int(a['time_gate_on']) for a in gate_cases if a['native_rhs_called']),
        'all_off_time_gate_source_toggle_vectors_bitwise_equal': all(a['source_toggle_vectors_bitwise_equal'] for a in gate_cases if a['native_rhs_called'] and not a['time_gate_on']),
    }
    physics_gate = full_stepper_error <= DECLARATION['frozen_full_stepper_source_relative_ceiling']
    write_json(out / 'result.json', {'status': 'bounded_local_diagnostic_completed', 'checks': checks,
                                   'frozen_preoscillation_source_infinitesimal_RHS_comparison': {'passed': physics_gate,
                                       'error_relative_to_preoscillation_source_peak': full_stepper_error,
                                       'relative_ceiling': DECLARATION['frozen_full_stepper_source_relative_ceiling'],
                                       'preoscillation_tau_peak': float(np.max(np.abs(expected_pre3[2]))),
                                       'native_full_RHS_source_tau_peak': float(np.max(np.abs(actual_djdt3[2]))),
                                       'reason': 'Actual native unsplit RHS mixes injected flavors before return and differs from declared preoscillation phi at the infinitesimal derivative; no finite-step full-stepper h/h2 criterion was evaluated'},
                                   'native_gate_off_vs_source_zero': {'neutrino_difference_peak': float(np.max(np.abs(vectors['native_gate_off_same_parent'][:-2] - vectors['source_zero_same_parent_gate'][:-2]))),
                                       'dzdx_difference': float(vectors['native_gate_off_same_parent'][-2] - vectors['source_zero_same_parent_gate'][-2]),
                                       'dtdx_difference': float(vectors['native_gate_off_same_parent'][-1] - vectors['source_zero_same_parent_gate'][-1])},
                                   'runs': runs, 'modules': native_module_receipt(),
                                   'native_scalar_globals_before': before_globals, 'native_scalar_globals_after': after_globals,
                                   'native_collision_nopython_signatures': [str(s) for s in collision.nopython_signatures],
                                   'scope': DECLARATION['scope'], 'grid_limit': DECLARATION['grid_limit'],
                                   'physics_validation': 'blocked; native unsplit infinitesimal source differs from frozen preoscillation source, and independently reviewed native QED identities also fail',
                                   'trajectory_integrated': False})
    worker_source_after = source_snapshot()
    write_json(out / 'source_after.json', worker_source_after)
    if worker_source_before != worker_source_after:
        raise RuntimeError('Native source changed during fixed-state worker')
    if not all(checks.values()):
        raise AssertionError('One or more required adapter diagnostics failed; preserved result.json')
    if physics_gate:
        raise AssertionError('Expected known full-stepper flavor mismatch was not demonstrated')


def run(out):
    out.mkdir(parents=True, exist_ok=False)  # atomic fresh-path reservation
    before = source_snapshot()
    write_json(out / 'source_before.json', before)
    write_json(out / 'predeclaration.json', DECLARATION)
    wrapper = Path(__file__).resolve()
    with (out / 'executed_wrapper.py').open('xb') as handle:
        handle.write(wrapper.read_bytes())
    write_json(out / 'runtime.json', {'versions': versions(), 'python_executable': sys.executable,
                                     'wrapper_path': str(wrapper), 'wrapper_sha256': hashlib.sha256(wrapper.read_bytes()).hexdigest(),
                                     'thread_environment': THREAD_ENV,
                                     'output_policy': 'atomic mkdir fresh-path reservation; artifacts opened exclusively; failures retained'})
    child = out / 'native_fixed_state'
    command = [sys.executable, '-B', str(wrapper), 'worker', '--out', str(child), '--source', str(SOURCE)]
    outcome = {'command': command, 'timeout': False, 'returncode': None}
    stdout, stderr = '', ''
    started = time.perf_counter()
    try:
        completed = subprocess.run(command, cwd=SOURCE, env={**os.environ, **THREAD_ENV},
                                   capture_output=True, text=True, timeout=DECLARATION['worker_timeout_seconds'])
        stdout, stderr = completed.stdout, completed.stderr
        outcome['returncode'] = completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or '', error.stderr or ''
        if isinstance(stdout, bytes): stdout = stdout.decode(errors='replace')
        if isinstance(stderr, bytes): stderr = stderr.decode(errors='replace')
        outcome['timeout'] = True
    except OSError as error:
        stderr = str(error)
        outcome['launch_error'] = str(error)
    finally:
        outcome['elapsed_seconds'] = time.perf_counter() - started
        after = source_snapshot()
        write_json(out / 'source_after.json', after)
        outcome['source_unchanged'] = before == after
        write_json(out / 'execution.json', outcome)
    for name, content in [('stdout.log', stdout), ('stderr.log', stderr)]:
        with (out / name).open('x') as handle:
            handle.write(content)
    hashes = {str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(out.rglob('*')) if path.is_file()}
    write_json(out / 'artifact_sha256.json', hashes)
    if outcome['returncode'] != 0 or outcome['timeout'] or not outcome['source_unchanged']:
        raise RuntimeError('Bounded native diagnostic failed or timed out; inspect retained logs and execution.json')
    print(json.dumps(outcome, sort_keys=True))


def main():
    global SOURCE
    if sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE') not in (None, '', '0'):
        raise RuntimeError('Optimized Python refused: unset PYTHONOPTIMIZE and omit -O/-OO')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('declare', 'run', 'worker'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=SOURCE)
    args = parser.parse_args()
    SOURCE = args.source.resolve()
    out = args.out.resolve()
    if out.exists():
        parser.error('--out must be fresh; existing evidence will never be overwritten')
    if args.mode == 'run':
        run(out)
    else:
        out.mkdir(parents=True, exist_ok=False)
        if args.mode == 'declare':
            write_json(out / 'predeclaration.json', DECLARATION)
            write_json(out / 'wrapper_identity.json', {'path': str(Path(__file__).resolve()),
                                                     'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
        else:
            worker(out)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
