import sqlite3
from datetime import datetime
import json
import os

class Database:
    def __init__(self, db_name='knowledge_base.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.insert_extended_data()
    
    def create_tables(self):
        """Создание таблиц с проверкой и обновлением структуры"""
        cursor = self.conn.cursor()
        
        # Таблица автомобильных систем
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS car_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                description TEXT
            )
        ''')
        
        # Таблица симптомов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symptoms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                system_id INTEGER,
                description TEXT,
                commonality INTEGER DEFAULT 3,
                severity INTEGER DEFAULT 2
            )
        ''')
        
        # Добавляем недостающие столбцы в symptoms если они есть
        try:
            cursor.execute("SELECT system_id FROM symptoms LIMIT 1")
        except sqlite3.OperationalError:
            # Столбец system_id не существует, добавляем его
            print("⚠️  Обновление структуры таблицы symptoms...")
            cursor.execute('''
                CREATE TABLE symptoms_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    system_id INTEGER,
                    description TEXT,
                    commonality INTEGER DEFAULT 3,
                    severity INTEGER DEFAULT 2
                )
            ''')
            
            # Копируем данные из старой таблицы
            cursor.execute("SELECT id, name, description FROM symptoms")
            old_data = cursor.fetchall()
            
            for row in old_data:
                # Для старых записей устанавливаем system_id = 1 (Двигатель) по умолчанию
                cursor.execute(
                    "INSERT INTO symptoms_new (id, name, system_id, description, commonality, severity) VALUES (?, ?, ?, ?, ?, ?)",
                    (row['id'], row['name'], 1, row['description'], 3, 2)
                )
            
            cursor.execute("DROP TABLE symptoms")
            cursor.execute("ALTER TABLE symptoms_new RENAME TO symptoms")
        
        # Таблица неисправностей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faults (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                system_id INTEGER,
                severity INTEGER,
                description TEXT,
                repair_cost_min INTEGER,
                repair_cost_max INTEGER,
                repair_time_min INTEGER,
                repair_time_max INTEGER,
                danger_level INTEGER DEFAULT 1,
                frequency INTEGER DEFAULT 3
            )
        ''')
        
        # Таблица связей симптомов и неисправностей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symptom_fault_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symptom_id INTEGER,
                fault_id INTEGER,
                confidence REAL,
                weight REAL DEFAULT 1.0,
                is_primary BOOLEAN DEFAULT 0,
                UNIQUE(symptom_id, fault_id)
            )
        ''')
        
        # Таблица комбинационных правил
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS combined_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT,
                fault_id INTEGER,
                required_symptoms TEXT,
                required_count INTEGER,
                confidence REAL
            )
        ''')
        
        # Таблица истории диагностик
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnostics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                car_make TEXT,
                car_model TEXT,
                car_year INTEGER,
                mileage INTEGER,
                symptoms_selected TEXT,
                symptoms_descriptions TEXT,
                faults_found TEXT,
                confidence REAL,
                recommendations TEXT,
                user_notes TEXT,
                is_saved BOOLEAN DEFAULT 0
            )
        ''')
        
        # Таблица статистики
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fault_id INTEGER,
                diagnosis_count INTEGER DEFAULT 0,
                confirmed_count INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0,
                last_diagnosed DATETIME
            )
        ''')
        
        self.conn.commit()
        print("✅ Структура базы данных успешно проверена/обновлена")
    
    def insert_extended_data(self):
        """Заполнение базы данных тестовыми данными с расширенными правилами"""
        cursor = self.conn.cursor()
        
        # Проверяем, есть ли уже данные в car_systems
        cursor.execute("SELECT COUNT(*) as count FROM car_systems")
        count = cursor.fetchone()['count']
        
        if count > 0:
            print("✅ База данных уже содержит данные, пропускаем инициализацию")
            return
        
        print("📊 Начинаем загрузку данных в базу...")
        
        # 1. Создаем системы автомобиля (оставляем как было)
        systems = [
            (1, "Двигатель", None, "Силовая установка автомобиля"),
            (2, "Трансмиссия", None, "Система передачи крутящего момента"),
            (3, "Подвеска", None, "Ходовая часть автомобиля"),
            (4, "Тормозная система", None, "Система замедления и остановки"),
            (5, "Электрика", None, "Электрооборудование автомобиля"),
            (6, "Рулевое управление", None, "Система управления направлением"),
            (7, "Система охлаждения", 1, "Поддержание температурного режима"),
            (8, "Топливная система", 1, "Подача топлива"),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO car_systems (id, name, parent_id, description) VALUES (?, ?, ?, ?)",
            systems
        )
        print(f"✅ Добавлено {len(systems)} систем автомобиля")
        
        # 2. Добавляем симптомы (дополняем список)
        symptoms_data = [
            # Двигатель (system_id = 1)
            ("Белый дым из выхлопа", 1, "Белый густой дым при работе двигателя", 2, 3),
            ("Черный дым из выхлопа", 1, "Черный дым при нажатии на газ", 3, 2),
            ("Сизый дым", 1, "Синий или сизый дым с запахом гари", 2, 4),
            ("Стук в двигателе", 1, "Металлический стук на холостом ходу", 3, 5),
            ("Потеря мощности", 1, "Автомобиль плохо разгоняется", 4, 3),
            ("Повышенный расход топлива", 1, "Расход выше нормы на 20% и более", 5, 2),
            ("Двигатель троит", 1, "Неравномерная работа, вибрация", 4, 3),
            ("Перегрев двигателя", 1, "Температура выше нормы", 3, 5),
            ("Долгий запуск", 1, "Двигатель заводится после нескольких попыток", 4, 2),
            ("Глохнет на холостых", 1, "Двигатель глохнет на нейтральной передаче", 3, 3),
            
            # Подвеска (system_id = 3)
            ("Стук на повороте", 3, "Стук при повороте руля", 5, 3),
            ("Стук на неровностях", 3, "Стук при езде по кочкам", 4, 3),
            ("Скрип при повороте", 3, "Скрипящий звук при вращении руля", 4, 2),
            ("Пробой подвески", 3, "Удар при проезде неровностей", 3, 3),
            ("Раскачка кузова", 3, "Продолжительные колебания после кочек", 4, 2),
            
            # Рулевое (system_id = 6)
            ("Люфт руля", 6, "Свободный ход рулевого колеса", 3, 4),
            ("Автомобиль тянет в сторону", 6, "При отпускании руля уводит с прямой", 4, 3),
            ("Вибрация на руле", 6, "Дрожание руля на скорости", 4, 4),
            ("Тяжелый руль", 6, "Усилие на руле больше обычного", 3, 2),
            ("Увод руля в сторону", 6, "Руль не возвращается в центр", 2, 3),
            
            # Тормоза (system_id = 4)
            ("Скрип тормозов", 4, "Скрип при нажатии на тормоз", 5, 1),
            ("Биение педали тормоза", 4, "Пульсация педали при торможении", 3, 4),
            ("Мягкая педаль тормоза", 4, "Педаль проваливается", 4, 5),
            ("Тянет при торможении", 4, "Машину уводит в сторону при торможении", 2, 5),
            ("Визг тормозов", 4, "Высокий визг при торможении", 4, 2),
            ("Длинный ход педали", 4, "Педаль опускается почти до пола", 3, 4),
            
            # Электрика (system_id = 5)
            ("Не заводится", 5, "Двигатель не запускается", 4, 5),
            ("Тусклый свет фар", 5, "Фары горят слабее обычного", 3, 2),
            ("Разряжается аккумулятор", 5, "АКБ быстро садится", 3, 3),
            ("Горит CHECK ENGINE", 5, "Индикатор проверки двигателя", 5, 3),
            ("Горит лампочка аккумулятора", 5, "Индикатор зарядки горит", 3, 4),
            ("Щелчки при повороте ключа", 5, "Щелчки вместо запуска", 4, 3),
            
            # Трансмиссия (system_id = 2)
            ("Пробуксовка АКПП", 2, "Коробка передач пробуксовывает", 3, 4),
            ("Рывки при переключении", 2, "Рывки при смене передач", 4, 4),
            ("Шум из коробки", 2, "Гул или скрежет из КПП", 3, 3),
            ("Пинки при переключении", 2, "Рывки при смене передач АКПП", 4, 4),
            ("Скрежет при включении передач", 2, "Скрежет при переключении", 3, 4),
            ("Самовыключение передачи", 2, "Передача выбивает при движении", 2, 4),
            
            # Система охлаждения (system_id = 7)
            ("Запотевание стекол", 7, "Стекла запотевают изнутри", 4, 1),
            ("Сладкий запах в салоне", 7, "Запах антифриза в салоне", 2, 3),
            ("Бульканье в печке", 7, "Булькающие звуки из системы отопления", 3, 2),
            ("Холодная печка", 7, "Печка не греет или слабо греет", 4, 2),
            
            # Топливная система (system_id = 8)
            ("Рывки при разгоне", 8, "Автомобиль дергается при нажатии на газ", 4, 3),
            ("Провалы при нажатии на газ", 8, "Отсутствие реакции на педаль газа", 3, 3),
            ("Затрудненный запуск на горячую", 8, "Проблемы с запуском прогретого двигателя", 3, 2),
            ("Запах бензина в салоне", 8, "Запах топлива в салоне автомобиля", 2, 4),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO symptoms (name, system_id, description, commonality, severity) VALUES (?, ?, ?, ?, ?)",
            symptoms_data
        )
        print(f"✅ Добавлено {len(symptoms_data)} симптомов")
        
        # 3. Добавляем неисправности (расширяем список)
        faults_data = [
            # Двигатель
            ("ENG-001", "Прогорание прокладки ГБЦ", 1, 5, 
            "Прокладка между блоком и головкой блока цилиндров повреждена",
            15000, 40000, 6, 12, 3, 2),
            ("ENG-002", "Износ поршневых колец", 1, 4,
            "Кольца не обеспечивают должного уплотнения в цилиндрах",
            25000, 60000, 10, 24, 2, 2),
            ("ENG-003", "Неисправность форсунок", 1, 3,
            "Топливные форсунки засорились или вышли из строя",
            3000, 15000, 2, 4, 2, 4),
            ("ENG-004", "Неисправность свечей зажигания", 1, 2,
            "Свечи требуют замены или чистки",
            1000, 5000, 1, 1, 1, 5),
            ("ENG-005", "Загрязнение дроссельной заслонки", 1, 2,
            "Дроссельная заслонка загрязнена",
            1500, 5000, 1, 2, 1, 5),
            ("ENG-006", "Неисправность датчика кислорода", 1, 3,
            "Лямбда-зонд вышел из строя",
            2000, 10000, 1, 2, 1, 4),
            
            # Подвеска
            ("SUSP-001", "Износ шаровой опоры", 3, 3,
            "Шаровая опора имеет критический люфт",
            2000, 8000, 1, 2, 2, 5),
            ("SUSP-002", "Износ сайлентблоков", 3, 2,
            "Резинометаллические шарниры разрушены",
            3000, 10000, 2, 4, 1, 4),
            ("SUSP-003", "Неисправность стойки стабилизатора", 3, 2,
            "Стойка стабилизатора имеет люфт",
            1000, 4000, 1, 1, 1, 5),
            ("SUSP-004", "Износ опорного подшипника", 3, 2,
            "Подшипник в стойке амортизатора изношен",
            2000, 6000, 1, 2, 1, 4),
            ("SUSP-005", "Износ амортизаторов", 3, 3,
            "Амортизаторы не гасят колебания",
            6000, 18000, 2, 4, 1, 4),
            
            # Рулевое
            ("STEER-001", "Износ рулевых наконечников", 6, 3,
            "Рулевые тяги имеют люфт",
            1500, 6000, 1, 2, 2, 4),
            ("STEER-002", "Неисправность рулевой рейки", 6, 4,
            "Рулевая рейка течет или имеет люфт",
            10000, 40000, 4, 8, 2, 3),
            ("STEER-003", "Износ насоса ГУР", 6, 3,
            "Насос гидроусилителя руля неисправен",
            5000, 20000, 2, 4, 1, 3),
            ("STEER-004", "Износ ШРУСа рулевой колонки", 6, 3,
            "Карданный шарнир рулевой колонки",
            4000, 12000, 2, 4, 1, 2),
            
            # Тормоза
            ("BRAKE-001", "Износ тормозных колодок", 4, 2,
            "Тормозные колодки требуют замены",
            2000, 8000, 1, 1, 2, 5),
            ("BRAKE-002", "Деформация тормозных дисков", 4, 3,
            "Тормозные диски имеют биение",
            3000, 15000, 1, 2, 2, 4),
            ("BRAKE-003", "Завоздушивание системы", 4, 2,
            "В тормозной системе есть воздух",
            1000, 3000, 1, 1, 2, 4),
            ("BRAKE-004", "Неисправность суппорта", 4, 4,
            "Тормозной суппорт заклинил",
            4000, 12000, 1, 2, 2, 3),
            ("BRAKE-005", "Износ тормозных шлангов", 4, 3,
            "Тормозные шланги потрескались",
            2000, 6000, 1, 2, 2, 3),
            
            # Электрика
            ("ELEC-001", "Неисправность генератора", 5, 4,
            "Генератор не заряжает аккумулятор",
            5000, 20000, 2, 4, 2, 3),
            ("ELEC-002", "Неисправность стартера", 5, 4,
            "Стартер не крутит или крутит медленно",
            4000, 15000, 2, 4, 2, 3),
            ("ELEC-003", "Разряд аккумулятора", 5, 3,
            "АКБ быстро разряжается",
            3000, 10000, 1, 1, 1, 4),
            ("ELEC-004", "Неисправность датчика детонации", 5, 3,
            "Датчик детонации не работает",
            1500, 6000, 1, 2, 1, 3),
            ("ELEC-005", "Неисправность катушки зажигания", 5, 3,
            "Катушка зажигания дает слабую искру",
            2000, 8000, 1, 2, 1, 4),
            
            # Трансмиссия
            ("TRANS-001", "Износ синхронизаторов", 2, 4,
            "Синхронизаторы коробки передач изношены",
            15000, 40000, 6, 12, 2, 3),
            ("TRANS-002", "Износ фрикционов АКПП", 2, 4,
            "Фрикционные диски автомата изношены",
            30000, 80000, 8, 24, 2, 3),
            ("TRANS-003", "Неисправность гидроблока АКПП", 2, 4,
            "Клапанный блок АКПП загрязнен",
            15000, 40000, 4, 8, 2, 3),
            ("TRANS-004", "Износ диска сцепления", 2, 3,
            "Фрикционный диск сцепления изношен",
            8000, 25000, 4, 8, 1, 4),
            
            # Система охлаждения
            ("COOL-001", "Неисправность термостата", 7, 3,
            "Термостат заклинил в открытом/закрытом положении",
            2000, 6000, 1, 3, 2, 4),
            ("COOL-002", "Неисправность помпы", 7, 4,
            "Водяной насос не качает антифриз",
            4000, 12000, 2, 4, 2, 3),
            
            # Топливная система
            ("FUEL-001", "Неисправность топливного насоса", 8, 4,
            "Топливный насос не создает давление",
            4000, 15000, 2, 4, 2, 3),
            ("FUEL-002", "Загрязнение топливного фильтра", 8, 2,
            "Топливный фильтр забит",
            1000, 3000, 1, 1, 1, 5),
        ]
        
        cursor.executemany(
            """INSERT OR IGNORE INTO faults 
            (code, name, system_id, severity, description, repair_cost_min, repair_cost_max, 
            repair_time_min, repair_time_max, danger_level, frequency) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            faults_data
        )
        print(f"✅ Добавлено {len(faults_data)} неисправностей")
        
        # Получаем ID для создания правил
        cursor.execute("SELECT id, name FROM symptoms")
        symptom_rows = cursor.fetchall()
        symptom_ids = {}
        for row in symptom_rows:
            symptom_ids[row['name']] = row['id']
        
        cursor.execute("SELECT id, code FROM faults")
        fault_rows = cursor.fetchall()
        fault_ids = {}
        for row in fault_rows:
            fault_ids[row['code']] = row['id']
        
        # 4. Создаем ПРАВИЛА СВЯЗЕЙ - ЭТО САМОЕ ВАЖНОЕ!
        # Расширяем правила связей для лучшей диагностики
        rules_data = [
            # Двигатель - расширенные правила
            ("Белый дым из выхлопа", "ENG-001", 0.9, 1.5, 1),
            ("Перегрев двигателя", "ENG-001", 0.7, 1.2, 1),
            ("Потеря мощности", "ENG-001", 0.6, 1.0, 0),
            ("Повышенный расход топлива", "ENG-001", 0.4, 0.7, 0),
            
            ("Сизый дым", "ENG-002", 0.8, 1.3, 1),
            ("Повышенный расход топлива", "ENG-002", 0.9, 1.5, 1),
            ("Потеря мощности", "ENG-002", 0.7, 1.1, 0),
            ("Повышенный расход масла", "ENG-002", 0.8, 1.3, 1),
            
            ("Черный дым из выхлопа", "ENG-003", 0.7, 1.1, 1),
            ("Двигатель троит", "ENG-003", 0.6, 1.0, 0),
            ("Потеря мощности", "ENG-003", 0.5, 0.8, 0),
            ("Повышенный расход топлива", "ENG-003", 0.6, 1.0, 0),
            ("Рывки при разгоне", "ENG-003", 0.5, 0.8, 0),
            
            ("Двигатель троит", "ENG-004", 0.8, 1.2, 1),
            ("Потеря мощности", "ENG-004", 0.4, 0.7, 0),
            ("Долгий запуск", "ENG-004", 0.5, 0.8, 0),
            ("Глохнет на холостых", "ENG-004", 0.4, 0.7, 0),
            
            ("Двигатель троит", "ENG-005", 0.7, 1.1, 1),
            ("Плавающие обороты", "ENG-005", 0.8, 1.3, 1),
            ("Глохнет на холостых", "ENG-005", 0.6, 1.0, 0),
            ("Долгий запуск", "ENG-005", 0.4, 0.7, 0),
            
            ("Горит CHECK ENGINE", "ENG-006", 0.9, 1.5, 1),
            ("Повышенный расход топлива", "ENG-006", 0.7, 1.1, 0),
            ("Потеря мощности", "ENG-006", 0.6, 1.0, 0),
            ("Двигатель троит", "ENG-006", 0.5, 0.8, 0),
            
            # Подвеска - расширенные правила
            ("Стук на повороте", "SUSP-001", 0.8, 1.3, 1),
            ("Стук на неровностях", "SUSP-001", 0.7, 1.1, 0),
            ("Люфт руля", "SUSP-001", 0.5, 0.8, 0),
            ("Вибрация на руле", "SUSP-001", 0.4, 0.7, 0),
            
            ("Стук на неровностях", "SUSP-002", 0.6, 1.0, 1),
            ("Автомобиль тянет в сторону", "SUSP-002", 0.7, 1.1, 1),
            ("Скрип при повороте", "SUSP-002", 0.5, 0.8, 0),
            ("Пробой подвески", "SUSP-002", 0.4, 0.7, 0),
            
            ("Стук на неровностях", "SUSP-003", 0.7, 1.1, 1),
            ("Крен в поворотах", "SUSP-003", 0.6, 1.0, 1),
            ("Скрип при повороте", "SUSP-003", 0.5, 0.8, 0),
            
            ("Скрип при повороте", "SUSP-004", 0.8, 1.3, 1),
            ("Тяжелый руль", "SUSP-004", 0.7, 1.1, 1),
            ("Стук на повороте", "SUSP-004", 0.5, 0.8, 0),
            
            ("Раскачка кузова", "SUSP-005", 0.9, 1.5, 1),
            ("Пробой подвески", "SUSP-005", 0.8, 1.3, 1),
            ("Стук на неровностях", "SUSP-005", 0.6, 1.0, 0),
            ("Увод руля в сторону", "SUSP-005", 0.5, 0.8, 0),
            
            # Рулевое - расширенные правила
            ("Люфт руля", "STEER-001", 0.7, 1.1, 1),
            ("Стук на повороте", "STEER-001", 0.6, 1.0, 0),
            ("Вибрация на руле", "STEER-001", 0.5, 0.8, 0),
            ("Увод руля в сторону", "STEER-001", 0.4, 0.7, 0),
            
            ("Люфт руля", "STEER-002", 0.8, 1.3, 1),
            ("Стук при движении", "STEER-002", 0.7, 1.1, 0),
            ("Течь рулевой жидкости", "STEER-002", 0.9, 1.5, 1),
            ("Тяжелый руль", "STEER-002", 0.6, 1.0, 0),
            
            ("Скрип при повороте", "STEER-003", 0.6, 1.0, 0),
            ("Тяжелый руль", "STEER-003", 0.8, 1.3, 1),
            ("Шум из насоса ГУР", "STEER-003", 0.9, 1.5, 1),
            ("Люфт руля", "STEER-003", 0.5, 0.8, 0),
            
            ("Стук на повороте", "STEER-004", 0.7, 1.1, 1),
            ("Люфт руля", "STEER-004", 0.6, 1.0, 0),
            ("Вибрация на руле", "STEER-004", 0.5, 0.8, 0),
            
            # Тормоза - расширенные правила
            ("Скрип тормозов", "BRAKE-001", 0.9, 1.5, 1),
            ("Визг тормозов", "BRAKE-001", 0.8, 1.3, 0),
            ("Длинный ход педали", "BRAKE-001", 0.6, 1.0, 0),
            ("Увеличенный тормозной путь", "BRAKE-001", 0.5, 0.8, 0),
            
            ("Биение педали тормоза", "BRAKE-002", 0.8, 1.3, 1),
            ("Вибрация на руле при торможении", "BRAKE-002", 0.7, 1.1, 0),
            ("Скрип тормозов", "BRAKE-002", 0.5, 0.8, 0),
            ("Визг тормозов", "BRAKE-002", 0.4, 0.7, 0),
            
            ("Мягкая педаль тормоза", "BRAKE-003", 0.9, 1.5, 1),
            ("Проваливается педаль", "BRAKE-003", 0.8, 1.3, 0),
            ("Длинный ход педали", "BRAKE-003", 0.7, 1.1, 0),
            ("Снижение эффективности торможения", "BRAKE-003", 0.6, 1.0, 0),
            
            ("Тянет при торможении", "BRAKE-004", 0.8, 1.3, 1),
            ("Перегрев колесного диска", "BRAKE-004", 0.7, 1.1, 1),
            ("Скрип тормозов", "BRAKE-004", 0.6, 1.0, 0),
            ("Визг тормозов", "BRAKE-004", 0.5, 0.8, 0),
            
            ("Мягкая педаль тормоза", "BRAKE-005", 0.7, 1.1, 1),
            ("Течь тормозной жидкости", "BRAKE-005", 0.9, 1.5, 1),
            ("Снижение эффективности торможения", "BRAKE-005", 0.6, 1.0, 0),
            
            # Электрика - расширенные правила
            ("Тусклый свет фар", "ELEC-001", 0.7, 1.1, 0),
            ("Разряжается аккумулятор", "ELEC-001", 0.8, 1.3, 1),
            ("Горит лампочка аккумулятора", "ELEC-001", 0.9, 1.5, 1),
            ("Мигание света на оборотах", "ELEC-001", 0.6, 1.0, 0),
            
            ("Не заводится", "ELEC-002", 0.8, 1.3, 1),
            ("Щелчки при повороте ключа", "ELEC-002", 0.9, 1.5, 1),
            ("Медленная прокрутка", "ELEC-002", 0.7, 1.1, 0),
            ("Разряжается аккумулятор", "ELEC-002", 0.5, 0.8, 0),
            
            ("Разряжается аккумулятор", "ELEC-003", 0.9, 1.5, 1),
            ("Не заводится", "ELEC-003", 0.6, 1.0, 0),
            ("Тусклый свет фар", "ELEC-003", 0.5, 0.8, 0),
            ("Проблемы с электрооборудованием", "ELEC-003", 0.4, 0.7, 0),
            
            ("Детонация (стук пальцев)", "ELEC-004", 0.8, 1.3, 1),
            ("Потеря мощности", "ELEC-004", 0.7, 1.1, 0),
            ("Повышенный расход топлива", "ELEC-004", 0.6, 1.0, 0),
            ("Горит CHECK ENGINE", "ELEC-004", 0.5, 0.8, 0),
            
            ("Двигатель троит", "ELEC-005", 0.8, 1.3, 1),
            ("Пропуски зажигания", "ELEC-005", 0.9, 1.5, 1),
            ("Потеря мощности", "ELEC-005", 0.6, 1.0, 0),
            ("Повышенный расход топлива", "ELEC-005", 0.5, 0.8, 0),
            
            # Трансмиссия - расширенные правила
            ("Скрежет при включении передач", "TRANS-001", 0.9, 1.5, 1),
            ("Тугое переключение", "TRANS-001", 0.7, 1.1, 0),
            ("Самовыключение передачи", "TRANS-001", 0.6, 1.0, 0),
            ("Шум в нейтрали", "TRANS-001", 0.5, 0.8, 0),
            
            ("Пробуксовка АКПП", "TRANS-002", 0.9, 1.5, 1),
            ("Пинки при переключении", "TRANS-002", 0.8, 1.3, 1),
            ("Задержка при переключении", "TRANS-002", 0.7, 1.1, 0),
            ("Автомобиль дергается", "TRANS-002", 0.6, 1.0, 0),
            
            ("Пинки при переключении", "TRANS-003", 0.8, 1.3, 1),
            ("Задержка при переключении", "TRANS-003", 0.9, 1.5, 1),
            ("Пробуксовка АКПП", "TRANS-003", 0.7, 1.1, 0),
            ("Шум из коробки", "TRANS-003", 0.6, 1.0, 0),
            
            ("Пробуксовка сцепления", "TRANS-004", 0.9, 1.5, 1),
            ("Ведение сцепления", "TRANS-004", 0.8, 1.3, 1),
            ("Вибрация педали сцепления", "TRANS-004", 0.7, 1.1, 0),
            ("Шум при выжиме сцепления", "TRANS-004", 0.6, 1.0, 0),
            
            # Система охлаждения
            ("Перегрев двигателя", "COOL-001", 0.7, 1.2, 1),
            ("Холодная печка", "COOL-001", 0.6, 1.0, 0),
            ("Долгий прогрев", "COOL-001", 0.5, 0.8, 0),
            ("Запотевание стекол", "COOL-001", 0.4, 0.7, 0),
            
            ("Перегрев двигателя", "COOL-002", 0.8, 1.3, 1),
            ("Течь антифриза", "COOL-002", 0.9, 1.5, 1),
            ("Шум из помпы", "COOL-002", 0.7, 1.1, 1),
            ("Бульканье в печке", "COOL-002", 0.6, 1.0, 0),
            
            # Топливная система
            ("Рывки при разгоне", "FUEL-001", 0.8, 1.3, 1),
            ("Провалы при нажатии на газ", "FUEL-001", 0.9, 1.5, 1),
            ("Двигатель троит", "FUEL-001", 0.7, 1.1, 0),
            ("Потеря мощности", "FUEL-001", 0.6, 1.0, 0),
            ("Затрудненный запуск на горячую", "FUEL-001", 0.5, 0.8, 0),
            
            ("Потеря мощности", "FUEL-002", 0.7, 1.1, 1),
            ("Рывки при разгоне", "FUEL-002", 0.6, 1.0, 0),
            ("Повышенный расход топлива", "FUEL-002", 0.5, 0.8, 0),
            ("Двигатель троит", "FUEL-002", 0.4, 0.7, 0),
        ]
        
        added_rules = 0
        for symptom_name, fault_code, confidence, weight, is_primary in rules_data:
            symptom_id = symptom_ids.get(symptom_name)
            fault_id = fault_ids.get(fault_code)
            if symptom_id and fault_id:
                try:
                    cursor.execute(
                        """INSERT OR IGNORE INTO symptom_fault_rules 
                        (symptom_id, fault_id, confidence, weight, is_primary) 
                        VALUES (?, ?, ?, ?, ?)""",
                        (symptom_id, fault_id, confidence, weight, is_primary)
                    )
                    added_rules += 1
                except:
                    pass
        
        print(f"✅ Добавлено {added_rules} правил связей")
        
        # 5. Создаем комбинационные правила для сложных случаев
        try:
            comb_rules = [
                ("Перегрев + Белый дым", "ENG-001", 
                json.dumps([symptom_ids["Перегрев двигателя"], symptom_ids["Белый дым из выхлопа"]]), 
                2, 0.98),
                ("Стук в повороте + Люфт руля", "SUSP-001", 
                json.dumps([symptom_ids["Стук на повороте"], symptom_ids["Люфт руля"]]), 
                2, 0.95),
                ("Скрип + Тяжелый руль", "STEER-003", 
                json.dumps([symptom_ids["Скрип при повороте"], symptom_ids["Тяжелый руль"]]), 
                2, 0.92),
                ("Биение + Вибрация при торможении", "BRAKE-002", 
                json.dumps([symptom_ids["Биение педали тормоза"], symptom_ids["Вибрация на руле"]]), 
                2, 0.96),
                ("Троит + Потеря мощности", "ENG-004", 
                json.dumps([symptom_ids["Двигатель троит"], symptom_ids["Потеря мощности"]]), 
                2, 0.90),
                ("Черный дым + Повышенный расход", "ENG-003", 
                json.dumps([symptom_ids["Черный дым из выхлопа"], symptom_ids["Повышенный расход топлива"]]), 
                2, 0.93),
                ("Сизый дым + Расход масла", "ENG-002", 
                json.dumps([symptom_ids["Сизый дым"], symptom_ids["Повышенный расход топлива"]]), 
                2, 0.94),
            ]
            
            for rule_name, fault_code, symptom_ids_list, required_count, confidence in comb_rules:
                fault_id = fault_ids.get(fault_code)
                if fault_id:
                    cursor.execute(
                        """INSERT INTO combined_rules 
                        (rule_name, fault_id, required_symptoms, required_count, confidence) 
                        VALUES (?, ?, ?, ?, ?)""",
                        (rule_name, fault_id, symptom_ids_list, required_count, confidence)
                    )
            
            print("✅ Добавлены комбинационные правила")
        except Exception as e:
            print(f"⚠️  Не удалось добавить комбинационные правила: {e}")
        
        # 6. Инициализируем статистику
        cursor.execute("SELECT id FROM faults")
        fault_rows = cursor.fetchall()
        
        for row in fault_rows:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO statistics (fault_id) VALUES (?)",
                    (row['id'],)
                )
            except:
                pass
        
        self.conn.commit()
        print("✅ Расширенная база данных успешно инициализирована!")
        print(f"📊 Всего в базе: {len(systems)} систем, {len(symptoms_data)} симптомов, {len(faults_data)} неисправностей")
        print(f"📈 Связей симптом-неисправность: {added_rules} правил")
    
    def get_car_systems(self):
        """Получение списка систем автомобиля"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, parent_id, description FROM car_systems ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_symptoms_grouped_by_system(self, system_filter=None):
        """Получение симптомов, сгруппированных по системам"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT s.id, s.name, s.description, s.severity, cs.name as system_name
            FROM symptoms s
            JOIN car_systems cs ON s.system_id = cs.id
        '''
        
        params = []
        if system_filter and system_filter != 'Все системы':
            query += ' WHERE cs.name = ?'
            params.append(system_filter)
        
        query += ' ORDER BY cs.name, s.name'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Группируем по системам
        grouped = {}
        for row in rows:
            system_name = row['system_name']
            if system_name not in grouped:
                grouped[system_name] = []
            grouped[system_name].append(dict(row))
        
        return grouped
    
    def get_faults_by_symptoms(self, symptom_ids):
        """Получение неисправностей по симптомам"""
        if not symptom_ids:
            return []
        
        cursor = self.conn.cursor()
        placeholders = ','.join(['?'] * len(symptom_ids))
        
        # Основные правила
        query = f'''
            SELECT f.id, f.code, f.name, f.system_id, f.severity, f.description,
                   f.repair_cost_min, f.repair_cost_max, f.repair_time_min, f.repair_time_max,
                   sf.confidence, COUNT(sf.symptom_id) as matched_count
            FROM faults f
            JOIN symptom_fault_rules sf ON f.id = sf.fault_id
            WHERE sf.symptom_id IN ({placeholders})
            GROUP BY f.id, f.code, f.name, f.system_id, f.severity, f.description
            ORDER BY matched_count DESC, MAX(sf.confidence) DESC
        '''
        
        cursor.execute(query, symptom_ids)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        
        return results
    
    def get_fault_details(self, fault_id):
        """Получение деталей неисправности"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT f.*, cs.name as system_name
            FROM faults f
            LEFT JOIN car_systems cs ON f.system_id = cs.id
            WHERE f.id = ?
        ''', (fault_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_symptoms_for_fault(self, fault_id):
        """Получение симптомов для неисправности"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.name, s.description, sf.confidence
            FROM symptoms s
            JOIN symptom_fault_rules sf ON s.id = sf.symptom_id
            WHERE sf.fault_id = ?
            ORDER BY sf.confidence DESC
        ''', (fault_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def save_diagnostic_session(self, session_data):
        """Сохранение сессии диагностики"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO diagnostics_history 
                (session_id, car_make, car_model, car_year, mileage, 
                 symptoms_selected, symptoms_descriptions, faults_found, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_data.get('session_id'),
                session_data.get('car_make'),
                session_data.get('car_model'),
                session_data.get('car_year'),
                session_data.get('mileage'),
                json.dumps(session_data.get('symptoms_selected', [])),
                json.dumps(session_data.get('symptoms_descriptions', {})),
                json.dumps(session_data.get('faults_found', [])),
                session_data.get('confidence', 0)
            ))
            
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"⚠️  Ошибка при сохранении сессии: {e}")
            return None
    
    def get_diagnostics_history(self, period=None, car_make=None, limit=100):
        """Получение истории диагностик"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT id, session_id, timestamp, car_make, car_model, car_year, mileage,
                   symptoms_selected, faults_found, confidence
            FROM diagnostics_history
            WHERE 1=1
        '''
        params = []
        
        if period and period != "Все":
            if period == "Сегодня":
                query += " AND date(timestamp) = date('now')"
            elif period == "Неделя":
                query += " AND timestamp > datetime('now', '-7 days')"
            elif period == "Месяц":
                query += " AND timestamp > datetime('now', '-30 days')"
            elif period == "Год":
                query += " AND timestamp > datetime('now', '-365 days')"
        
        if car_make:
            query += " AND car_make LIKE ?"
            params.append(f'%{car_make}%')
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_diagnostic_details(self, record_id):
        """Получение деталей диагностики по ID"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM diagnostics_history WHERE id = ?
        ''', (record_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_diagnostic_record(self, record_id):
        """Удаление записи диагностики"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM diagnostics_history WHERE id = ?", (record_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except:
            return False
    
    def clear_all_history(self):
        """Очистка всей истории"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM diagnostics_history")
            self.conn.commit()
            return True
        except:
            return False
    
    def get_statistics(self):
        """Получение статистики"""
        cursor = self.conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) as total FROM diagnostics_history")
        total_row = cursor.fetchone()
        total_diagnostics = total_row['total'] if total_row else 0
        
        cursor.execute("SELECT AVG(confidence) as avg_conf FROM diagnostics_history WHERE confidence IS NOT NULL")
        avg_row = cursor.fetchone()
        avg_confidence = avg_row['avg_conf'] if avg_row else 0
        
        return {
            'total_diagnostics': total_diagnostics,
            'avg_confidence': avg_confidence or 0,
            'top_systems': [],
            'top_faults': []
        }
    
    def close(self):
        """Закрытие соединения с БД"""
        self.conn.close()

