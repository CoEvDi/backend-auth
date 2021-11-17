import os
import asyncio
import yaml

from datetime import datetime, timezone, timedelta
from aiofiles import open as async_open
from aiofiles.os import stat as async_stat
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

            config.VERSION = data['version']

            database = data['database']
            config.DB_CONNECTION_STRING = f"postgresql+asyncpg://{database['user']}:{database['password']}@{database['host']}:{database['port']}/{database['database']}"

    async def _update(self, config):
        conf_stat = await async_stat(self._config_file)
        mod_conf_datetime = datetime.fromtimestamp(conf_stat.st_mtime)

        if not config.FIRST_RUN and datetime.now() > mod_conf_datetime + timedelta(seconds=self._update_interval):
            return
        cfg.FIRST_RUN = False

        async with async_open(self._config_file, mode='r') as conf:
            data = yaml.safe_load(await conf.read())

            config.DOMAIN = data['domain']
            self._update_interval = data['update_interval']

            security = data['security']
            config.TOKEN_SECRET_KEY = security['token_secret_key']
            config.TOKEN_NAME = security['token_name']
            config.TOKEN_EXPIRE_TIME = security['expire_time']

            backend_accounts = data['backend_accounts']
            config.BA_VERIFY_ACCOUNT_LINK = f"http://{backend_accounts['host']}:{backend_accounts['port']}/{backend_accounts['verify_route']}"

    async def start(self, config):
        self._update_task = asyncio.ensure_future(self._update_loop(config))
        await self._init(config)


cfg = SimpleNamespace()
cfg.STARTUP_DB_ACTION = False
cfg.FIRST_RUN = True
