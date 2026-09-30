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

# --- НАШ НОВЫЙ ЭНДПОИНТ ДЛЯ РЕЙСОВ ---
@app.get("/api/v1/flights", summary="Получить список рейсов с фильтром по аэропорту")
def get_flights(departure_airport: str = None, limit: int = 20):
    """
    Возвращает список рейсов.
    - **departure_airport**: код аэропорта отправления (например, DME, SVO) — необязательный параметр.
    - **limit**: количество записей на странице (по умолчанию 20).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Базовый SQL-запрос к таблице рейсов (flights)
    query = "SELECT flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status FROM flights"
    params = []
    
    # Если пользователь передал код аэропорта, добавляем фильтрацию WHERE
    if departure_airport:
        query += " WHERE departure_airport = %s"
        params.append(departure_airport.upper()) # приводим к верхнему регистру (Dme -> DME)
        
    # Добавляем ограничение на количество строк, чтобы не перегружать память
    query += " LIMIT %s;"
    params.append(limit)
    
    try:
        cursor.execute(query, params)
        flights = cursor.fetchall()
        return flights
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при чтении данных о рейсах")
    finally:
        cursor.close()
        conn.close()
