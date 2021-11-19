import uuid
import httpx
from fastapi import Request
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.sql import select

from .database import sessions
from .database import _engine
from .config import cfg
from .schemas import CurrentUser
from .errors import HTTPabort


async def check_token(token):
    try:
        payload = jwt.decode(token, cfg.TOKEN_SECRET_KEY, algorithms=['HS256'])
        account_id: int = int(payload.get('account_id'))
        role: str = payload.get('role')
        session_id = uuid.UUID(payload.get('session_id'))
        login_time = datetime.fromisoformat(payload.get('login_time'))
        client = payload.get('client')
    except:
        return CurrentUser()

    async with _engine.begin() as conn:
        if datetime.utcnow() > (login_time + timedelta(days=cfg.TOKEN_EXPIRE_TIME)):
            query = sessions.delete().where(sessions.c.id == session_id)
            await conn.execute(query)
            return CurrentUser()

        query = select(sessions).where(sessions.c.id == session_id)
        result = await conn.execute(query)
        current_user = result.first()

        if not current_user:
            return CurrentUser()

        return CurrentUser(current_user, role)


async def auth_required(request: Request):
    token = request.cookies.get(cfg.TOKEN_NAME)
    current_user = await check_token(token)
    if not current_user.is_auth:
        HTTPabort(401, 'Unauthorized')
    return current_user


async def auth_forbidden(request: Request):
    token = request.cookies.get(cfg.TOKEN_NAME)
    current_user = await check_token(token)
    if current_user.is_auth:
        HTTPabort(409, 'User must be unauthorized')


async def get_current_user(request: Request):
    token = request.cookies.get(cfg.TOKEN_NAME)
    return await check_token(token)


async def is_auth(token):
    current_user = await check_token(token)
    if not current_user.is_auth:
        HTTPabort(401, 'Unauthorized')
    return current_user.auth_info()


async def authenticate_user(login, password):
    async with httpx.AsyncClient() as ac:
        json = {
            'login': login,
            'password': password
        }
        answer = await ac.post(cfg.BA_VERIFY_ACCOUNT_LINK, json=json)

        if answer.status_code != 200:
            HTTPabort(answer.status_code, answer.json()['detail'])
        account = answer.json()['content']
        account_id = int(account['account_id'])
        role = account['role']

    async with _engine.begin() as conn:
        query = sessions.insert().values(account_id=account_id, client='web')
        result = await conn.execute(query)

    jwt_account_data = {
        'account_id': account_id,
        'role': role,
        'session_id': str(result.inserted_primary_key[0]),
        'client': 'web',
        'login_time': datetime.utcnow().isoformat()
    }

    return jwt.encode(jwt_account_data, cfg.TOKEN_SECRET_KEY, algorithm='HS256')


async def logout_user(session_id):
    async with _engine.begin() as conn:
        query = sessions.delete().where(sessions.c.id == session_id)
        await conn.execute(query)


async def delete_sessions(account_id, session_id, mode):
    async with _engine.begin() as conn:
        query = sessions.delete().where(sessions.c.account_id == account_id)
        if mode == 'one':
            query = query.where(sessions.c.id == uuid.UUID(session_id))
        elif mode == 'other':
            query = query.where(sessions.c.id != uuid.UUID(session_id))
        await conn.execute(query)


async def close_sessions(current_user, password_and_session, mode):
    async with httpx.AsyncClient() as ac:
        json = {
            'account_id': current_user.account_id,
            'password': password_and_session.password
        }
        answer = await ac.post(cfg.BA_VERIFY_ACCOUNT_LINK, json=json)

        if answer.status_code != 200:
            HTTPabort(answer.status_code, answer.json()['detail'])

    session_id = password_and_session.session_id if password_and_session.session_id else current_user.session_id
    await delete_sessions(current_user.account_id, session_id, mode)
