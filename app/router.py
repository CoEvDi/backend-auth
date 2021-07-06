from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from typing import Optional

from . import schemas
from . import logic
from .config import cfg


router = APIRouter()


def HTTPanswer(status_code, description, action_cookie=None, token=None):
    response = JSONResponse(
        status_code=status_code,
        content={'content': description},
    )
    if action_cookie == 'set':
        response.set_cookie(key=cfg.TOKEN_NAME, value=token, path='/',
                            domain=cfg.DOMAIN, httponly=True, samesite=None)
    if action_cookie == 'delete':
        response.delete_cookie(cfg.TOKEN_NAME, path='/', domain=cfg.DOMAIN)

    return response


# external general rout to check auth

@router.get('/is_auth')
async def is_auth(current_user = Depends(logic.auth_required)):
    return HTTPanswer(200, 'Auth OK')


# external routes for manage sessions

@router.post('/login')
async def login(account: schemas.AuthCredentials,
                current_user = Depends(logic.auth_required)):
    if current_user.is_auth:
        HTTPanswer(409, 'User already logged-in')
    token = await logic.authenticate_user(account.login, account.password)
    return HTTPanswer(200, 'Successfully logged-in', 'set', token)


@router.get('/logout')
async def logout(current_user = Depends(logic.auth_required)):
    await logic.logout_user(current_user.session_id)
    return HTTPanswer(200, 'Successfully logouted', 'delete')


@router.post('/close_other_sessions')
async def close_other_sessions(password: schemas.Password,
                               current_user = Depends(logic.auth_required)):
    await logic.close_other_sessions(current_user, password.password)
    return HTTPanswer(200, 'Closed all other sessions')


# internal routes for accounts micro-service

@router.delete('/delete_other_sessions')
async def delete_other_sessions(session: schemas.Session):
    await logic.delete_sessions(session, 'other')
    return HTTPanswer(200, 'Deleted')


@router.delete('/delete_all_sessions')
async def delete_all_sessions(session: schemas.Session):
    await logic.delete_sessions(session)
    return HTTPanswer(200, 'Deleted')
