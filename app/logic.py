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
    if not token:
        HTTPabort(401, 'Incorrect token name')

    current_user = await check_token(token)
    if not current_user.is_auth:
        HTTPabort(401, 'Unauthorized')
    return current_user


async def get_current_user(request: Request):
    token = request.cookies.get(cfg.TOKEN_NAME)
    return await check_token(token)


async def is_auth(token):
    cu = await check_token(token)
    return cu.auth_info()


async def authenticate_user(login, password):
    async with httpx.AsyncClient() as ac:
        json = {
            'login': login,
            'password': password
        }
        answer = await ac.post(f'{cfg.BACKEND_ACCOUNTS_ADDRESS}/verify_account',
                               json=json)

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


async def close_other_sessions(current_user, password):
    async with httpx.AsyncClient() as ac:
        json = {
            'account_id': current_user.account_id,
            'password': password
        }
        answer = await ac.post(f'{cfg.M_ACCOUNTS_ADDRESS}/verify_account', json=json)

        if answer.status_code != 200:
            HTTPabort(answer.status_code, answer.json()['content'])

    async with _engine.begin() as conn:
        query = sessions.delete().where(sessions.c.account_id == current_user.account_id).where(sessions.c.id != current_user.session_id)
        await conn.execute(query)


async def delete_sessions(session, which=None):
    async with _engine.begin() as conn:
        query = sessions.delete().where(sessions.c.account_id == session.account_id)
        if which == 'other':
            query = query.where(sessions.c.id != session.session_id)
        await conn.execute(query)
