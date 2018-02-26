import unittest
import numpy as np

from expan.core.statistical_test import *
from expan.core.util import generate_random_data
from expan.core.experiment import Experiment


class StatisticalTestCase(unittest.TestCase):
    def setUp(self):
        np.random.seed(41)
        self.data, self.metadata = generate_random_data()

        # simple statistical test
        self.test_kpi = KPI('normal_same')
        self.test_variants = Variants('variant', 'A', 'B')
        self.test_revenue_overall = StatisticalTest(self.test_kpi, [], self.test_variants)

    def tearDown(self):
        pass

    def test_setup_single_test(self):
        variants = Variants('variant', 'control', 'treatment')
        mobile = FeatureFilter('device_type', 'mobile')
        kpi = KPI('revenue')

        test_revenue_overall = StatisticalTest(kpi, [], variants)
        test_revenue_mobile = StatisticalTest(kpi, [mobile], variants)

        self.assertEqual(test_revenue_overall.kpi.name, "revenue")
        self.assertEqual(test_revenue_overall.variants.control_name, "control")
        self.assertEqual(test_revenue_overall.variants.treatment_name, "treatment")

        self.assertEqual(test_revenue_mobile.kpi.name, "revenue")
        self.assertEqual(test_revenue_mobile.variants.control_name, "control")
        self.assertEqual(test_revenue_mobile.variants.treatment_name, "treatment")
        self.assertEqual(test_revenue_mobile.features[0].column_name, "device_type")
        self.assertEqual(test_revenue_mobile.features[0].column_value, "mobile")

    def test_setup_multiple_test_suite(self):
        variants = Variants('variant', 'control', 'treatment')
        mobile = FeatureFilter('device_type', 'mobile')
        desktop = FeatureFilter('device_type', 'desktop')
        tablet = FeatureFilter('device_type', 'tablet')
        kpi = KPI('revenue')

        test_revenue_overall = StatisticalTest(kpi, [], variants)
        test_revenue_mobile = StatisticalTest(kpi, [mobile], variants)
        test_revenue_desktop = StatisticalTest(kpi, [desktop], variants)
        test_revenue_tablet = StatisticalTest(kpi, [tablet], variants)

        tests = [test_revenue_overall, test_revenue_mobile, test_revenue_desktop, test_revenue_tablet]
        multi_test_suite = StatisticalTestSuite(tests, "bh")

        self.assertEqual(multi_test_suite.size, 4)
        self.assertEqual(multi_test_suite.correction_method, "bh")

    def test_make_derived_kpi(self):
        numerator = "normal_same"
        denominator = "normal_shifted"
        derived_kpi_name = "derived_kpi_one"
        DerivedKPI(derived_kpi_name, numerator, denominator).make_derived_kpi(self.data)

        # checks if column with the derived kpi was created
        self.assertTrue(derived_kpi_name in self.data.columns)

        # checks if values of new columns are of type float
        self.assertTrue(all(isinstance(kpi_value, float) for kpi_value in self.data[derived_kpi_name]))

    def test_get_variant(self):
        control = self.test_revenue_overall.variants.get_variant(
            self.data, self.test_revenue_overall.variants.control_name)[self.test_revenue_overall.kpi.name]
        self.assertEqual(len(control), 6108)
        self.assertTrue(isinstance(control, pd.Series))

    def test_analyze_statistical_test_fixed_horizon(self):
        experiment = Experiment(self.data, self.metadata)
        results = experiment.analyze_statistical_test(self.test_revenue_overall, testmethod='fixed_horizon', alpha=0.05)

        # Control sample size
        self.assertEqual(results.result.control_statistics.sample_size, 6108)

        # Treatment sample size
        self.assertEqual(results.result.treatment_statistics.sample_size, 3892)

        # Statistical power
        self.assertAlmostEqual(results.result.statistical_power, 0.36400577293301273)

        # Test statistical power with 0.1 alpha is bigger than with 0.05
        results_2 = experiment.analyze_statistical_test(self.test_revenue_overall, testmethod='fixed_horizon', alpha=0.1)
        self.assertEqual(results_2.result.statistical_power, 0.4869722734005255)
        self.assertTrue(results_2.result.statistical_power > results.result.statistical_power)
