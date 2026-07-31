"""Typed application errors with stable HTTP semantics."""


class ApiError(Exception):
    def __init__(self, message, *, code="INVALID_REQUEST", status_code=400, data=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.data = data


class ServiceUnavailableError(ApiError):
    def __init__(self, message="服务暂时不可用", *, code="SERVICE_UNAVAILABLE", data=None):
        super().__init__(message, code=code, status_code=503, data=data)


class ForbiddenError(ApiError):
    def __init__(self, message="无权访问该资源", *, code="RESOURCE_FORBIDDEN", data=None):
        super().__init__(message, code=code, status_code=403, data=data)
