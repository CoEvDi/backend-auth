import uvicorn
from argparse import ArgumentParser

from app import app
from app.config import cfg


if __name__ == '__main__':
    parser = ArgumentParser(description='Auth Management micro-service backend')
    parser.add_argument('--Create-Tables', '-CT',
                        action='store_true',
                        dest='recreate_tables',
                        help='(Re)Creating sessions database tables before launch')
    parser.add_argument('-H', '--Host',
                        required=True,
                        action='store',
                        dest='host',
                        help='Server host')
    parser.add_argument('-P', '--Port',
                        required=True,
                        action='store',
                        dest='port',
                        help='Server port')

    args = parser.parse_args()
    if args.recreate_tables:
        cfg.STARTUP_DB_ACTION = True
    
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config['formatters']['access']['fmt'] = '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s'

    uvicorn.run(
        'main:app',
        host=args.host,
        port=int(args.port),
        log_config=log_config,
        reload=False
    )
