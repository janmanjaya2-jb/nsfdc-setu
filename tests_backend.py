import unittest
from backend import calculate_emi, calculate_max_loan, get_loan_estimate, load_schemes, recommend_scheme


class TestNSFDCBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemes = load_schemes()

    def test_mfs_exact_boundary(self):
        s = recommend_scheme({"purpose": "project", "project_cost": 140000}, self.schemes)
        self.assertEqual(s["scheme_id"], "MFS")

    def test_tl_at_140001(self):
        s = recommend_scheme({"purpose": "project", "project_cost": 140001}, self.schemes)
        self.assertEqual(s["scheme_id"], "TL")

    def test_tl_exact_boundary(self):
        s = recommend_scheme({"purpose": "project", "project_cost": 5000000}, self.schemes)
        self.assertEqual(s["scheme_id"], "TL")

    def test_above_tl_limit(self):
        s = recommend_scheme({"purpose": "project", "project_cost": 5000001}, self.schemes)
        self.assertIsNone(s)

    def test_education(self):
        s = recommend_scheme({"purpose": "education", "project_cost": 2000000}, self.schemes)
        self.assertEqual(s["scheme_id"], "EDU")

    def test_mfs_loan_cap(self):
        mfs = next(s for s in self.schemes if s["scheme_id"] == "MFS")
        self.assertEqual(calculate_max_loan(140000, mfs), 125000.0)

    def test_tl_loan_cap(self):
        tl = next(s for s in self.schemes if s["scheme_id"] == "TL")
        self.assertEqual(calculate_max_loan(5000000, tl), 4500000.0)

    def test_edu_loan_cap(self):
        edu = next(s for s in self.schemes if s["scheme_id"] == "EDU")
        self.assertEqual(calculate_max_loan(5000000, edu), 4000000.0)

    def test_emi_zero_interest(self):
        self.assertEqual(calculate_emi(120000, 0, 1, 0)["emi"], 10000.0)

    def test_tl_extended_moratorium(self):
        result = get_loan_estimate(
            {"purpose": "project", "project_cost": 500000},
            self.schemes,
            moratorium_months=12,
        )
        self.assertEqual(result["scheme_id"], "TL")
        self.assertEqual(result["selected_moratorium_months"], 12)

    def test_edu_moratorium_note(self):
        result = get_loan_estimate(
            {"purpose": "education", "project_cost": 1000000},
            self.schemes,
        )
        self.assertEqual(result["scheme_id"], "EDU")
        self.assertIn("moratorium_note", result)


if __name__ == "__main__":
    unittest.main()
