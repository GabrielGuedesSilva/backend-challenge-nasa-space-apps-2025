from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    custom_errors = []

    for error in exc.errors():
        field = error['loc'][-1]
        message = error['msg']
        invalid_value = error.get('input')

        custom_errors.append({
            'field': field,
            'input': invalid_value,
            'message': message,
        })

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={'detail': custom_errors},
    )
