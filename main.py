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
@app.get("/api/v1/airports", summary="Получить список всех аэропортов для выпадающего списка")
def get_airports():
    """
    Возвращает список кодов, названий и городов всех аэропортов на русском языке.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Извлекаем данные, вытаскивая русский язык из JSON-полей airport_name и city
    query = """
        SELECT 
            airport_code, 
            airport_name->>'ru' AS airport_name, 
            city->>'ru' AS city 
        FROM bookings.airports_data
        ORDER BY city->>'ru';
    """
    try:
        cursor.execute(query)
        airports = cursor.fetchall()
        return airports
    except Exception as e:
        print(f"Ошибка чтения аэропортов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при чтении данных об аэропортах")
    finally:
        cursor.close()
        conn.close()


# --- ОБНОВЛЕННЫЙ ЭНДПОИНТ РЕЙСОВ ---
@app.get("/api/v1/flights", summary="Получить список рейсов с фильтром по аэропорту")
def get_flights(departure_airport: str = None, limit: int = 20):
    # Код этого эндпоинта остается точно таким же, как был на прошлом шаге!
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status FROM flights"
    params = []
    
    if departure_airport:
        query += " WHERE departure_airport = %s"
        params.append(departure_airport.upper())
        
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
