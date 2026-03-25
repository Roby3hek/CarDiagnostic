# make_exe.py - автоматическая сборка EXE
import os
import sys
import subprocess
import shutil

def check_dependencies():
    """Проверка и установка зависимостей"""
    print("Проверка зависимостей...")
    
    try:
        import PyInstaller
        print("✓ PyInstaller установлен")
    except ImportError:
        print("Установка PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Проверяем наличие всех файлов
    required_files = [
        "database.py",
        "expert_system.py", 
        "gui_fixed.py",
        "main_fixed.py",
        "knowledge_base.db"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        print("Запустите программу сначала для создания базы данных:")
        print("  python main_fixed.py")
        return False
    
    print("✓ Все необходимые файлы присутствуют")
    return True

def create_icon():
    """Создание иконки если ее нет"""
    if not os.path.exists("car_icon.ico"):
        print("Создание иконки приложения...")
        
        # Простая иконка через tkinter
        import tkinter as tk
        from PIL import Image, ImageDraw, ImageTk
        
        # Создаем изображение
        img = Image.new('RGB', (256, 256), color='#3498db')
        draw = ImageDraw.Draw(img)
        
        # Рисуем автомобиль
        draw.rectangle([60, 140, 196, 176], fill='#2c3e50', outline='white', width=3)  # Кузов
        draw.rectangle([76, 120, 100, 140], fill='#2c3e50', outline='white', width=2)   # Кабина
        draw.ellipse([70, 170, 90, 190], fill='#e74c3c')  # Колесо 1
        draw.ellipse([166, 170, 186, 190], fill='#e74c3c')  # Колесо 2
        
        # Сохраняем в разных размерах
        img.save('car_icon.ico', format='ICO', 
                sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        
        print("✓ Иконка создана: car_icon.ico")

def build_exe():
    """Сборка EXE файла"""
    print("\n" + "="*50)
    print("Сборка CarDiagnosticSystem.exe")
    print("="*50)
    
    # Команда для PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=CarDiagnosticSystem",
        "--icon=car_icon.ico",
        f"--add-data=knowledge_base.db;.",
        "--clean",
        "main_fixed.py"
    ]
    
    print(f"Выполняем команду: {' '.join(cmd)}")
    
    try:
        # Запускаем сборку
        subprocess.run(cmd, check=True)
        print("\n✅ Сборка завершена успешно!")
        
        # Копируем базу данных рядом с EXE
        exe_dir = "dist"
        if os.path.exists("knowledge_base.db"):
            shutil.copy2("knowledge_base.db", exe_dir)
            print(f"✓ База данных скопирована в {exe_dir}/")
        
        print(f"\n📁 Ваш EXE файл находится в: {exe_dir}/CarDiagnosticSystem.exe")
        print("📦 Размер папки dist: ", end="")
        
        # Вычисляем размер
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(exe_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        
        print(f"{total_size / 1024 / 1024:.2f} MB")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при сборке: {e}")
        return False
    
    return True

def create_readme():
    """Создание README файла"""
    readme_content = """# 🚗 Экспертная система диагностики автомобилей

## Описание
Программа для диагностики неисправностей автомобилей по симптомам.

## Возможности
- Диагностика по 50+ симптомам
- База из 30+ неисправностей
- История диагностик
- Сохранение отчетов
- Статистика

## Системные требования
- Windows 7/8/10/11
- 100 MB свободного места
- .NET Framework 4.5 (обычно уже установлен)

## Установка
Просто запустите `CarDiagnosticSystem.exe` - установка не требуется.

## Использование
1. Выберите симптомы в левой панели
2. Нажмите "ВЫПОЛНИТЬ ДИАГНОСТИКУ"
3. Просмотрите результаты
4. Сохраните отчет при необходимости

## Важно
Программа предоставляет предварительную диагностику.
Для точного ремонта обратитесь в сервисный центр.

## Контакты
Для вопросов и предложений: [ваш email]

© 2024 Экспертная система диагностики автомобилей
"""
    
    with open("dist/README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("✓ README файл создан")

def create_zip():
    """Создание ZIP архива для распространения"""
    import zipfile
    import datetime
    
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    zip_name = f"CarDiagnosticSystem_{date_str}.zip"
    
    print(f"\nСоздание архива {zip_name}...")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Добавляем EXE файл
        exe_path = "dist/CarDiagnosticSystem.exe"
        if os.path.exists(exe_path):
            zipf.write(exe_path, "CarDiagnosticSystem.exe")
        
        # Добавляем базу данных
        db_path = "dist/knowledge_base.db"
        if os.path.exists(db_path):
            zipf.write(db_path, "knowledge_base.db")
        
        # Добавляем README
        readme_path = "dist/README.txt"
        if os.path.exists(readme_path):
            zipf.write(readme_path, "README.txt")
    
    print(f"✓ Архив создан: {zip_name}")
    print(f"📦 Размер архива: {os.path.getsize(zip_name) / 1024 / 1024:.2f} MB")

def main():
    """Главная функция"""
    print("="*50)
    print("СБОРКА EXE ФАЙЛА ДЛЯ ДИАГНОСТИКИ АВТОМОБИЛЕЙ")
    print("="*50)
    
    # Проверяем зависимости
    if not check_dependencies():
        input("\nНажмите Enter для выхода...")
        return
    
    # Создаем иконку
    create_icon()
    
    # Собираем EXE
    if build_exe():
        # Создаем README
        create_readme()
        
        # Создаем ZIP архив
        create_zip()
        
        print("\n" + "="*50)
        print("✅ ВСЁ ГОТОВО!")
        print("="*50)
        print("\nЧто было создано:")
        print("1. dist/CarDiagnosticSystem.exe - исполняемый файл")
        print("2. dist/knowledge_base.db - база данных")
        print("3. dist/README.txt - инструкция")
        print("4. CarDiagnosticSystem_YYYYMMDD_HHMM.zip - архив для распространения")
        
        print("\n📋 Следующие шаги:")
        print("1. Распакуйте архив на целевом компьютере")
        print("2. Запустите CarDiagnosticSystem.exe")
        print("3. Для деинсталляции просто удалите файлы")
    
    input("\nНажмите Enter для завершения...")

if __name__ == "__main__":
    main()