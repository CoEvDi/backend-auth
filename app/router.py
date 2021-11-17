from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from typing import Optional

from . import schemas
from . import logic
from .config import cfg
from .errors import HTTPabort


router = APIRouter()


def HTTPanswer(status_code, description, action_cookie=None, token=None):
    response = JSONResponse(
        status_code=status_code,
        content={'content': description},
    )
    if action_cookie == 'set':
        response.set_cookie(key=cfg.TOKEN_NAME, value=token, path='/',
                            max_age=cfg.TOKEN_EXPIRE_TIME * 24 * 3600,
                            domain=cfg.DOMAIN, httponly=True, samesite=None)
    if action_cookie == 'delete':
        response.delete_cookie(cfg.TOKEN_NAME, path='/', domain=cfg.DOMAIN)

    return response


@router.get('/version')
async def version():
    return HTTPanswer(200, f'Current version - {cfg.VERSION}')


# external general route to check auth 

@router.post('/is_auth')
async def is_auth(token: schemas.Token):
    return await logic.is_auth(token.token)


# external routes for manage sessions

@router.post('/login')
async def login(account: schemas.AuthCredentials,
                current_user = Depends(logic.get_current_user)):
    if current_user.is_auth:
        HTTPabort(409, 'User already logged-in')
    token = await logic.authenticate_user(account.login, account.password)
    return HTTPanswer(200, 'Successfully logged-in', 'set', token)


@router.get('/logout')
async def logout(current_user = Depends(logic.auth_required)):
    await logic.logout_user(current_user.session_id)
    return HTTPanswer(200, 'Successfully logouted', 'delete')


@router.post('/close_sessions/{mode}')
async def close_sessions(mode: str, password_and_session: schemas.PasswordSession,
                         current_user = Depends(logic.auth_required)):
    if mode not in ['all', 'one', 'other']:
        HTTPabort(404, 'Unknown closing mode')
    await logic.close_sessions(current_user, password_and_session, mode)
    return HTTPanswer(200, f'Closed {mode} session(s)')


# internal routes for accounts micro-service

@router.post('/delete_sessions/{mode}')
async def delete_other_sessions(mode: str, session: schemas.SessionDel):
    if mode not in ['all', 'one', 'other']:
        HTTPabort(404, 'Unknown closing mode')
    await logic.delete_sessions(session.account_id, session.session_id, mode)
    return HTTPanswer(200, 'Deleted')
