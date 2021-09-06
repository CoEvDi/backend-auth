from fastapi import HTTPException
from fastapi.responses import JSONResponse


def HTTPabort(status_code, description):
    raise HTTPException(status_code=status_code, detail=description)


async def server_error(request, exc):
    return JSONResponse(
        status_code=500,
        content='Internal server error - we are sorry(',
    )


exception_handlers = {
    500: server_error
}
