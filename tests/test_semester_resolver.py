import unittest
from unittest.mock import MagicMock


class TestCurrentSemesterResolver(unittest.TestCase):
    def test_zero_current_is_configuration_failure(self):
        from backend.api.errors import ServiceUnavailableError
        from backend.services.semester_resolver import CurrentSemesterResolver

        session = MagicMock()
        session.query.return_value.filter_by.return_value.limit.return_value.all.return_value = []
        with self.assertRaises(ServiceUnavailableError) as raised:
            CurrentSemesterResolver.resolve(session)
        self.assertEqual(raised.exception.code, "SEMESTER_NOT_CONFIGURED")

    def test_multiple_current_is_configuration_failure(self):
        from backend.api.errors import ServiceUnavailableError
        from backend.services.semester_resolver import CurrentSemesterResolver

        session = MagicMock()
        session.query.return_value.filter_by.return_value.limit.return_value.all.return_value = [MagicMock(), MagicMock()]
        with self.assertRaises(ServiceUnavailableError) as raised:
            CurrentSemesterResolver.resolve(session)
        self.assertEqual(raised.exception.code, "SEMESTER_CONFIG_CONFLICT")


if __name__ == "__main__":
    unittest.main()
