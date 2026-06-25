from fastapi import HTTPException


class AppError(Exception):
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


def bad_request(message: str, code: str = "BAD_REQUEST") -> HTTPException:
    return HTTPException(status_code=400, detail={"code": code, "message": message})


def unauthorized(message: str = "Unauthorized") -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": "UNAUTHORIZED", "message": message},
    )


def forbidden(message: str = "Forbidden") -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": "FORBIDDEN", "message": message},
    )


def not_found(message: str = "Not found") -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "NOT_FOUND", "message": message},
    )
