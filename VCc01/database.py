import psycopg2
import random
import time
from datetime import datetime
from config import Config

class PostgreSQLStorage:
    def __init__(self):
        pass

    def _get_connection(self):
        try:
            print("🔄 Попытка подключения к PostgreSQL...")
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                dbname=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                connect_timeout=15,          # увеличен таймаут
                keepalives=1,
                keepalives_idle=10,
                keepalives_interval=5,
                keepalives_count=5,
                tcp_user_timeout=15000,
                sslmode='require'
            )
            conn.autocommit = True
            print("✅ Соединение установлено.")
            with conn.cursor() as cur:
                cur.execute("SELECT current_database();")
                db_name = cur.fetchone()[0]
                print(f"🔍 Подключено к БД: {db_name}")
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = 'users'
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                print("📋 Столбцы таблицы public.users по мнению бота:")
                for col in columns:
                    print(f"   - {col[0]} ({col[1]})")
            return conn
        except psycopg2.OperationalError as e:
            print(f"❌ Ошибка подключения (OperationalError): {e}")
            # Дополнительная информация
            if "password" in str(e).lower():
                print("   ➜ Возможно, неверный пароль.")
            elif "host" in str(e).lower():
                print("   ➜ Возможно, хост недоступен или IP не в белом списке.")
            elif "ssl" in str(e).lower():
                print("   ➜ Проблема с SSL. Попробуйте изменить sslmode.")
            raise
        except Exception as e:
            print(f"❌ Неизвестная ошибка подключения: {e}")
            raise

    def save_user_data(self, full_name: str, birthday: str, retries: int = 3) -> bool:
        bday_obj = datetime.strptime(birthday, "%d.%m.%Y")
        bday_str = bday_obj.strftime("%Y-%m-%d")
        summ = round(random.uniform(100.0, 5000.0), 2)
        card_number = random.randint(1000000000000000, 9999999999999999)

        for attempt in range(1, retries + 1):
            conn = None
            try:
                conn = self._get_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO public.users (full_name, summ, card_num, birthday)
                        VALUES (%s, %s, %s, %s)
                    """, (full_name, summ, card_number, bday_str))
                conn.close()
                print(f"✅ Данные сохранены в PostgreSQL для {full_name}")
                return True

            except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
                print(f"⚠️ Попытка {attempt}/{retries} не удалась: {e}")
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                if attempt < retries:
                    wait = 2 ** attempt
                    print(f"   Повтор через {wait} сек...")
                    time.sleep(wait)
                else:
                    print(f"❌ Все попытки сохранения в PostgreSQL исчерпаны.")
                    return False

            except Exception as e:
                print(f"❌ Неизвестная ошибка: {e}")
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                return False
        return False

    def close(self):
        pass