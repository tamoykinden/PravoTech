"""Запуск backend командой ``python -m backend``."""

import os
import uvicorn


if __name__ == '__main__':
    uvicorn.run(
        'backend.main:app',
        host=os.getenv('BACKEND_HOST', '127.0.0.1'),
        port=int(os.getenv('BACKEND_PORT', '8000')),
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips=os.getenv('FORWARDED_ALLOW_IPS', '127.0.0.1'),
    )
