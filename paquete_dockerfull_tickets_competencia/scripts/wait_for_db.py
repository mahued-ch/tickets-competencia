import os
import time
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
TIMEOUT_SECONDS = int(os.getenv('DB_WAIT_TIMEOUT', '90'))

if not DATABASE_URL:
    raise SystemExit('DATABASE_URL no definido')

engine = create_engine(DATABASE_URL, future=True)
start = time.time()

while True:
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Base de datos disponible.')
        break
    except Exception as ex:
        elapsed = time.time() - start
        if elapsed > TIMEOUT_SECONDS:
            raise SystemExit(f'No fue posible conectar a la BD en {TIMEOUT_SECONDS}s: {ex}')
        print('Esperando disponibilidad de la base de datos...')
        time.sleep(3)
