import tkinter as tk
from tkinter import ttk
import os

# Проверяем наличие файлов
required_files = ['database.py', 'expert_system.py', 'gui_fixed.py']
missing_files = []

for file in required_files:
    if not os.path.exists(file):
        missing_files.append(file)

if missing_files:
    print("❌ Отсутствуют необходимые файлы:")
    for file in missing_files:
        print(f"   - {file}")
    print("\nУбедитесь, что все файлы находятся в одной папке.")
    input("Нажмите Enter для выхода...")
    exit(1)

# Импортируем модули
try:
    from database import Database
    from expert_system import ExpertSystem
    from gui_fixed import DiagnosticGUI
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    print("Убедитесь, что все файлы находятся в одной папке.")
    input("Нажмите Enter для выхода...")
    exit(1)

def set_styles():
    """Настройка стилей интерфейса"""
    style = ttk.Style()
    
    # Пробуем разные темы
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'alt' in available_themes:
        style.theme_use('alt')
    elif 'default' in available_themes:
        style.theme_use('default')
    
    # Настройка стиля для кнопок
    style.configure('Accent.TButton',
                   font=('Arial', 10, 'bold'),
                   padding=10)

def main():
    """Главная функция приложения"""
    print("=" * 60)
    print("🚗 ЭКСПЕРТНАЯ СИСТЕМА ДИАГНОСТИКИ АВТОМОБИЛЕЙ")
    print("=" * 60)
    
    try:
        # Инициализация базы данных
        print("📁 Инициализация базы знаний...")
        db = Database('knowledge_base.db')
        
        # Инициализация экспертной системы
        print("🧠 Загрузка экспертной системы...")
        expert_system = ExpertSystem(db)
        
        # Создание главного окна
        print("🎨 Создание интерфейса...")
        root = tk.Tk()
        
        # Настройка стилей
        set_styles()
        
        # Создание GUI
        app = DiagnosticGUI(root, expert_system)
        
        # Центрирование окна
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Обработка закрытия окна
        def on_closing():
            print("\n👋 Закрытие приложения...")
            try:
                db.close()
            except:
                pass
            root.destroy()
            print("✅ Приложение закрыто.")
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("\n✅ Система готова к работе!")
        print("\n" + "=" * 60)
        print("📋 КРАТКАЯ ИНСТРУКЦИЯ:")
        print("  1. Выберите симптомы в левой панели")
        print("  2. Нажмите 'ВЫПОЛНИТЬ ДИАГНОСТИКУ'")
        print("  3. Просмотрите результаты в правой панели")
        print("=" * 60 + "\n")
        
        # Запуск главного цикла
        root.mainloop()
        
    except Exception as e:
        print(f"\n❌ Ошибка при запуске приложения: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()