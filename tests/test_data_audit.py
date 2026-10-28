import copy
import unittest

from travel_constraints.audit_data import audit_records
from travel_constraints.build_data import build_records


class DataAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = build_records()

    def test_revised_corpus_passes(self):
        report = audit_records(self.records)
        self.assertTrue(report["passed"], report["issues"])
        self.assertEqual(report["unique_model_inputs"], 400)

    def test_identical_request_cannot_cross_splits(self):
        rows = copy.deepcopy(self.records)
        train = next(row for row in rows if row["split"] == "train")
        validation = next(row for row in rows if row["split"] == "validation")
        validation["input"]["change_request"] = train["input"]["change_request"]
        self.assertTrue(any(item["issue"] == "Identical request text crosses splits"
                            for item in audit_records(rows)["issues"]))

    def test_wrong_hotel_clock_is_detected(self):
        rows = copy.deepcopy(self.records)
        row = next(row for row in rows if row["family"] == "hotel_time")
        row["target"]["constraints"][0]["value"] = "23:59"
        self.assertTrue(any(item["issue"] == "Hotel clock value disagrees with request"
                            for item in audit_records(rows)["issues"]))


if __name__ == "__main__":
    unittest.main()
