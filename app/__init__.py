from fastapi import FastAPI

from .config import YamlConfigManager
from .config import cfg
from .errors import exception_handlers


ConfigManager = YamlConfigManager(interval=60)

app = FastAPI(exception_handlers=exception_handlers)


@app.on_event('startup')
async def startup():
    await ConfigManager.start(cfg)

    from . import database
    await database.check_database()

    if cfg.STARTUP_DB_ACTION:
        await database.recreate_tables()

    from .router import router

    app.include_router(router)


@app.on_event('shutdown')
async def shutdown():
    from .database import _engine
    _engine.dispose()
