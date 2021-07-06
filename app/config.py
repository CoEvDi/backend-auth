import os
import asyncio
import yaml
from aiofile import async_open
from types import SimpleNamespace


class YamlConfigManager:
    def __init__(self, interval):
        self._update_interval = interval
        self._config_file = 'config.yaml'


    async def _update_loop(self, config):
        while True:
            try:
                await self._update(config)
            except Exception as e:
                print(f'Failed to update config, see you next time \n{repr(e)}')
            await asyncio.sleep(self._update_interval)


    async def _init(self, config):
        async with async_open(self._config_file, 'r') as f:
            data = yaml.safe_load(await f.read())

            database = data['database']
            config.DB_CONNECTION_STRING = f"postgresql+asyncpg://{database['user']}:{database['password']}@{database['host']}:{database['port']}/{database['database']}"

            admin = data['admin']
            config.ADMIN_LOGIN = admin['login']
            config.ADMIN_PASSWORD = admin['password']


    async def _update(self, config):
        async with async_open(self._config_file, 'r') as f:
            data = yaml.safe_load(await f.read())

            config.DOMAIN = data['domain']
            self._update_interval = data['update_interval']

            security = data['security']
            config.TOKEN_SECRET_KEY = security['token_secret_key']
            config.TOKEN_NAME = security['token_name']
            config.TOKEN_EXPIRE_TIME = security['expire_time']

            backend_accounts = data['backend_accounts']
            config.BACKEND_ACCOUNTS_ADDRESS = f"http://{backend_accounts['host']}:{backend_accounts['port']}"


    async def start(self, config):
        self._update_task = asyncio.ensure_future(self._update_loop(config))
        await self._init(config)
        await self._update(config)


cfg = SimpleNamespace()

cfg.STARTUP_DB_ACTION = False
