import os
from fastapi import FastAPI, HTTPException
import psycopg
from psycopg.rows import dict_row

app = FastAPI(title="Avia REST API")

# Теперь настройки считываются из переменных окружения.
# Если переменная не найдена, подставится значение по умолчанию (второй аргумент)
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "demo"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "host.docker.internal"),
    "port": os.getenv("DB_PORT", "5432")
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

# --- НОВЫЙ ЭНДПОИНТ: ПОЛУЧЕНИЕ СПИСКА АЭРОПОРТОВ ---
@app.get("/api/v1/flights", summary="Получить список рейсов с фильтром по названию города")
def get_flights(city_name: str = None, limit: int = 20):
    """
    Возвращает список рейсов.
    - **city_name**: название города отправления на русском языке (например: Москва, Сочи, Анапа) — необязательный параметр.
    - **limit**: количество записей на странице (по умолчанию 20).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Пишем запрос со связыванием таблиц через JOIN.
    # Нам нужно вытащить данные из flights, но проверить город в bookings.airports_data
    query = """
        SELECT 
            f.flight_id, 
            f.flight_no, 
            f.scheduled_departure, 
            f.scheduled_arrival, 
            f.departure_airport, 
            f.arrival_airport, 
            f.status,
            a.city->>'ru' AS departure_city  -- Добавим в ответ название города для наглядности
        FROM flights f
        JOIN bookings.airports_data a ON f.departure_airport = a.airport_code
    """
    params = []
    
    # 2. Если передан город, добавляем фильтрацию по текстовому полю внутри JSON
    if city_name:
        # Использование ILIKE делает поиск регистронезависимым (москва, Москва, МОСКВА)
        # % позволяет искать по части слова (например, "Моск" найдет "Москва")
        query += " WHERE a.city->>'ru' ILIKE %s"
        params.append(f"%{city_name}%")
        
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
