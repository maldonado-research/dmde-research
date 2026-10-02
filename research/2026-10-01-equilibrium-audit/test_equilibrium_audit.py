"""Analytic limits, independent integration, and omission controls."""
import math
import unittest

import numpy as np

import equilibrium_audit as audit


class BornEquilibriumTests(unittest.TestCase):
    def test_closed_form_normalization_against_quadrature(self):
        _, _, weighted_phase = audit.beta_quadrature(192)
        self.assertLess(abs(weighted_phase.sum()/audit.analytic_i0()-1), 5e-13)

    def test_vacuum_neutron_lifetime(self):
        pair = audit.beta_pair(1e-5, np.zeros_like)
        self.assertLess(abs(pair["beta_s_inv"]*audit.TAU_N-1), 5e-13)
        self.assertEqual(pair["inverse_s_inv"], 0.)

    def test_high_temperature_beta_quarter_limit(self):
        # Each of the two blocking/occupation factors tends independently to 1/2.
        pair = audit.beta_pair(1e9, lambda p: audit.fd(p, 1e9))
        for key in ("beta_s_inv", "inverse_s_inv"):
            self.assertLess(abs(pair[key]*4*audit.TAU_N-1), 1e-8)

    def test_each_reverse_pair_detailed_balance(self):
        for t in audit.TEMPERATURES:
            with self.subTest(T=t):
                r = audit.thermal_rates(t)
                expected = math.exp(-audit.DELTA/t)
                for forward, reverse in ((0, 4), (1, 3), (2, 5)):
                    self.assertLess(abs(r[reverse]/r[forward]/expected-1), 1e-11)

    def test_total_detailed_balance_and_omission_negative_control(self):
        for t in audit.TEMPERATURES:
            r = audit.thermal_rates(t)
            expected = math.exp(-audit.DELTA/t)
            self.assertLess(abs(r[3:].sum()/r[:3].sum()/expected-1), 1e-11)
            # The missing-rate fraction exactly predicts the incomplete ratio.
            defect = 1-r[3:5].sum()/r[:3].sum()/expected
            self.assertLess(abs(defect-r[2]/r[:3].sum()), 1e-13)
        r = audit.thermal_rates(.2)
        self.assertGreater(1-r[3:5].sum()/r[:3].sum()/math.exp(-audit.DELTA/.2), .3)

    def test_arbitrary_occupation_identity_and_extreme_bounds(self):
        for t in (.05, .1, .5, 5.):
            low = audit.beta_pair(t, np.zeros_like)
            high = audit.beta_pair(t, np.ones_like)
            varied = audit.beta_pair(t, lambda p: .2+.6*(p/(audit.DELTA-audit.M_E))**2)
            self.assertEqual(low["inverse_s_inv"], 0.)
            self.assertEqual(high["beta_s_inv"], 0.)
            self.assertEqual(high["inverse_s_inv"], high["inverse_upper_bound_s_inv"])
            self.assertGreater(varied["inverse_s_inv"], 0.)
            self.assertLess(varied["inverse_s_inv"], varied["inverse_upper_bound_s_inv"])
            self.assertLess(abs(varied["beta_s_inv"]-varied["inverse_s_inv"]-varied["net_identity_s_inv"]), 1e-16)

    def test_nonthermal_occupation_cannot_use_thermal_inverse_formula(self):
        pair = audit.beta_pair(.2, lambda p: np.full_like(p, .6))
        ratio = pair["inverse_s_inv"]/pair["beta_s_inv"]
        self.assertGreater(abs(ratio/math.exp(-audit.DELTA/.2)-1), 1.)

    def test_unequal_temperatures_do_not_obey_common_temperature_balance(self):
        r = audit.thermal_rates(.5, neutrino_temperature=.35)
        defect = r[3:].sum()/r[:3].sum()/math.exp(-audit.DELTA/.5)-1
        self.assertGreater(abs(defect), .01)

    def test_independent_order_and_tail_refinements(self):
        for t in audit.TEMPERATURES:
            r = audit.thermal_rates(t)
            self.assertLess(float(np.max(np.abs(r/audit.thermal_rates(t, order=192)-1))), 1e-10)
            self.assertLess(float(np.max(np.abs(r/audit.thermal_rates(t, tail_in_T=80.)-1))), 1e-10)

    def test_clipped_tail_negative_control_survives_balance_check(self):
        # Pair ratios alone cannot validate domain completeness: identical omitted
        # tails preserve reciprocity but significantly bias absolute capture rates.
        clipped = audit.thermal_rates(5., tail_in_T=10.)
        full = audit.thermal_rates(5., tail_in_T=80.)
        self.assertGreater(float(np.max(np.abs(clipped/full-1))), 1e-3)
        metric = audit.balance_residuals(clipped, 5.)
        self.assertLess(abs(metric["six_process_total_relative_residual"]), 1e-11)

    def test_frozen_provider_integrands_agree_with_independent_reference(self):
        for t in (5., .8, .3, .2, .1, .05):
            result = audit.frozen_comparison(t)
            self.assertLess(result["max_relative_difference_after_matching_normalization"], 1e-10)
            self.assertLess(result["max_raw_rate_relative_difference"], 3e-8)

    def test_lifetime_scaling_is_common_to_every_process(self):
        reference = audit.thermal_rates(.5)
        changed = audit.thermal_rates(.5, tau_n=2*audit.TAU_N)
        np.testing.assert_allclose(changed, reference/2, rtol=1e-14, atol=0.)

    def test_invalid_inputs_fail(self):
        for t in (0., -1., math.nan, math.inf):
            with self.assertRaises(ValueError):
                audit.thermal_rates(t)
        for bad in (lambda p: p*0-0.1, lambda p: p*0+1.1,
                    lambda p: p*math.nan, lambda p: np.array([.5])):
            with self.assertRaises(ValueError):
                audit.beta_pair(.5, bad)


if __name__ == "__main__":
    unittest.main()
