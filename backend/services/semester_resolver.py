"""Single source of truth for the current semester."""

from backend.api.errors import ServiceUnavailableError
from backend.models.semester_config import SemesterConfig


class CurrentSemesterResolver:
    @staticmethod
    def resolve(session):
        rows = session.query(SemesterConfig).filter_by(is_current=1).limit(2).all()
        if not rows:
            raise ServiceUnavailableError(
                "尚未配置当前学期", code="SEMESTER_NOT_CONFIGURED"
            )
        if len(rows) > 1:
            raise ServiceUnavailableError(
                "当前学期配置冲突", code="SEMESTER_CONFIG_CONFLICT"
            )
        return rows[0]
