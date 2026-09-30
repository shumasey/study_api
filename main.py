from fastapi import FastAPI, HTTPException
import psycopg
from psycopg.rows import dict_row

app = FastAPI(title="Avia REST API")

# Настройки подключения к вашей базе данных (замените на свои данные)
DB_CONFIG = {
    "dbname": "demo",       # имя базы данных
    "user": "postgres",     # имя пользователя
    "password": "1", # ваш пароль
    "host": "host.docker.internal",    # адрес (если база на том же ПК)
    "port": "5432"          # стандартный порт PostgreSQL
}

def get_db_connection():
    try:
        # RealDictCursor позволяет получать данные из БД сразу в виде словарей (JSON)
        conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

@app.get("/")
def read_root():
    return {"message": "REST API для авиабазы успешно работает!"}

# Эндпоинт для получения списка самолетов (таблица aircrafts_data)
@app.get("/api/v1/aircrafts")
def get_aircrafts():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Делаем запрос к таблице aircrafts_data из вашей схемы
    cursor.execute("SELECT aircraft_code, model, range FROM aircrafts_data;")
    aircrafts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return aircrafts
