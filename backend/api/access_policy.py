"""Central resource-ownership authorization for course-plan scoped actions."""

import functools

from flask import g, request

from backend.api.errors import ForbiddenError, ApiError, ServiceUnavailableError
from backend.models.base import DatabaseManager
from backend.models.course_plan import CoursePlan
from backend.models.enrollment import Enrollment


def authorize_plan_access(session, actor: dict, plan_id: int, capability="read"):
    """Return the plan if the actor may use it, otherwise raise a typed error."""
    plan = session.query(CoursePlan).filter_by(plan_id=plan_id).first()
    if plan is None:
        raise ApiError("课程计划不存在", code="PLAN_NOT_FOUND", status_code=404)

    role = actor.get("role")
    user_id = actor.get("user_id")
    if role == "admin":
        return plan
    if role == "teacher" and plan.teacher_id == user_id:
        return plan
    if role == "student" and capability in {"read", "self_export"}:
        enrolled = session.query(Enrollment).filter_by(
            student_id=user_id, plan_id=plan_id, status="已选"
        ).first()
        if enrolled:
            return plan
    raise ForbiddenError("无权访问该课程计划", code="PLAN_ACCESS_DENIED")


def _extract_plan_id(source, name):
    if source == "path":
        value = request.view_args.get(name)
    elif source == "query":
        value = request.args.get(name)
    elif source == "form":
        value = request.form.get(name)
    else:
        value = (request.get_json(silent=True) or {}).get(name)
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ApiError("缺少有效的 plan_id", code="PLAN_ID_INVALID", status_code=422)


def require_plan_access(capability="read", *, source="path", name="plan_id"):
    """Decorator that makes resource authorization mandatory and discoverable."""
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            plan_id = _extract_plan_id(source, name)
            try:
                with DatabaseManager.get_instance().get_session() as session:
                    authorize_plan_access(
                        session, g.current_user, plan_id, capability=capability
                    )
            except ApiError:
                raise
            except Exception as exc:
                raise ServiceUnavailableError(
                    "授权数据暂时不可用", code="AUTHORIZATION_SERVICE_UNAVAILABLE"
                ) from exc
            return f(*args, **kwargs)

        decorated._plan_access_policy = {
            "capability": capability,
            "source": source,
            "name": name,
        }
        return decorated

    return decorator
