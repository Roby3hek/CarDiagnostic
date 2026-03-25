import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import json
import uuid

class DiagnosticGUI:
    def __init__(self, root, expert_system):
        self.root = root
        self.es = expert_system
        self.root.title("Экспертная система диагностики автомобилей")
        self.root.geometry("1200x700")
        
        # Переменные
        self.selected_symptoms = {}  # symptom_id: symptom_name
        self.current_faults = []
        self.current_session_id = str(uuid.uuid4())[:8]
        
        # Словарь для хранения ID симптомов
        self.symptom_index_to_id = {}
        
        # Создание интерфейса
        self.create_widgets()
        self.load_initial_data()
    
    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        # Главный контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Панели с разделителем
        paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - симптомы
        left_frame = ttk.LabelFrame(paned, text="📋 Выбор симптомов", padding=10)
        paned.add(left_frame, weight=1)
        
        # Фильтр по системе
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Фильтр по системе:").pack(side=tk.LEFT, padx=(0, 5))
        self.system_var = tk.StringVar()
        self.system_combo = ttk.Combobox(filter_frame, textvariable=self.system_var, 
                                        state="readonly", width=25)
        self.system_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.system_combo.bind('<<ComboboxSelected>>', self.filter_symptoms)
        
        # Поиск по названию
        ttk.Label(filter_frame, text="Поиск:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT)
        search_entry.bind('<KeyRelease>', self.search_symptoms)
        
        # Список симптомов с прокруткой
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем два виджета: Listbox и Scrollbar
        self.symptoms_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE,
                                          font=('Arial', 10), bg='white')
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                 command=self.symptoms_listbox.yview)
        self.symptoms_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Упаковываем
        self.symptoms_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязываем событие выбора (ЭТО ВАЖНО!)
        self.symptoms_listbox.bind('<<ListboxSelect>>', self.on_symptom_select)
        
        # Кнопки для списка симптомов
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Выбрать все", 
                  command=self.select_all_symptoms).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Сбросить фильтр", 
                  command=self.reset_filter).pack(side=tk.RIGHT, padx=2)
        
        # Центральная панель - выбранные симптомы
        center_frame = ttk.LabelFrame(paned, text="✅ Выбранные симптомы", padding=10)
        paned.add(center_frame, weight=1)
        
        # Информация об автомобиле
        car_frame = ttk.LabelFrame(center_frame, text="Информация об автомобиле", padding=5)
        car_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Создаем сетку для полей
        row1 = ttk.Frame(car_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="Марка:").pack(side=tk.LEFT, padx=(0, 5))
        self.car_make = tk.StringVar()
        ttk.Entry(row1, textvariable=self.car_make, width=20).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(row1, text="Модель:").pack(side=tk.LEFT, padx=(0, 5))
        self.car_model = tk.StringVar()
        ttk.Entry(row1, textvariable=self.car_model, width=20).pack(side=tk.LEFT)
        
        row2 = ttk.Frame(car_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2, text="Год:").pack(side=tk.LEFT, padx=(0, 5))
        self.car_year = tk.StringVar()
        ttk.Entry(row2, textvariable=self.car_year, width=10).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(row2, text="Пробег (км):").pack(side=tk.LEFT, padx=(0, 5))
        self.car_mileage = tk.StringVar()
        ttk.Entry(row2, textvariable=self.car_mileage, width=15).pack(side=tk.LEFT)
        
        # Список выбранных симптомов
        selected_list_frame = ttk.Frame(center_frame)
        selected_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.selected_listbox = tk.Listbox(selected_list_frame, selectmode=tk.SINGLE,
                                          font=('Arial', 10), bg='#f0f0f0')
        
        selected_scrollbar = ttk.Scrollbar(selected_list_frame, orient=tk.VERTICAL,
                                          command=self.selected_listbox.yview)
        self.selected_listbox.configure(yscrollcommand=selected_scrollbar.set)
        
        self.selected_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        selected_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки для управления выбранными симптомами
        selected_btn_frame = ttk.Frame(center_frame)
        selected_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(selected_btn_frame, text="Удалить выбранный",
                  command=self.remove_selected_symptom).pack(side=tk.LEFT, padx=2)
        ttk.Button(selected_btn_frame, text="Очистить все",
                  command=self.clear_all_symptoms).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - результаты
        right_frame = ttk.LabelFrame(paned, text="🔍 Результаты диагностики", padding=10)
        paned.add(right_frame, weight=2)
        
        # Кнопка диагностики
        diag_btn_frame = ttk.Frame(right_frame)
        diag_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(diag_btn_frame, text="🚗 ВЫПОЛНИТЬ ДИАГНОСТИКУ",
                  command=self.perform_diagnosis,
                  style='Accent.TButton').pack(fill=tk.X)
        
        # Таблица результатов
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('Код', 'Неисправность', 'Система', 'Уверенность', 'Серьезность')
        self.results_tree = ttk.Treeview(tree_frame, columns=columns,
                                        show='headings', height=10)
        
        # Настраиваем столбцы
        col_widths = {
            'Код': 80,
            'Неисправность': 200,
            'Система': 120,
            'Уверенность': 100,
            'Серьезность': 80
        }
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=col_widths.get(col, 100))
        
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                      command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_tree.bind('<<TreeviewSelect>>', self.on_fault_select)
        
        # Детали неисправности
        details_frame = ttk.LabelFrame(right_frame, text="📄 Детали неисправности", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=12,
                                                     font=('Arial', 9), wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Нижняя панель с дополнительными кнопками
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(bottom_frame, text="📊 История диагностик",
                  command=self.show_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text="💾 Сохранить отчет",
                  command=self.save_report).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text="📈 Статистика",
                  command=self.show_statistics).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text="❓ Справка",
                  command=self.show_help).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text="🚪 Выход",
                  command=self.root.quit).pack(side=tk.RIGHT, padx=2)
    
    def load_initial_data(self):
        """Загрузка начальных данных"""
        # Загружаем системы для фильтра
        try:
            systems = self.es.db.get_car_systems()
            system_names = ['Все системы'] + [s['name'] for s in systems]
            self.system_combo['values'] = system_names
            self.system_combo.current(0)
            
            # Загружаем симптомы
            self.load_symptoms_list()
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
    
    def load_symptoms_list(self):
        """Загрузка списка симптомов"""
        self.symptoms_listbox.delete(0, tk.END)
        self.symptom_index_to_id.clear()  # Очищаем словарь соответствий
        
        # Определяем фильтр системы
        system_filter = None
        if self.system_var.get() and self.system_var.get() != 'Все системы':
            system_filter = self.system_var.get()
        
        # Получаем симптомы
        try:
            symptoms_by_system = self.es.db.get_symptoms_grouped_by_system(system_filter)
            
            if not symptoms_by_system:
                self.symptoms_listbox.insert(tk.END, "Нет симптомов для отображения")
                return
            
            index = 0
            for system_name, symptoms in symptoms_by_system.items():
                # Добавляем разделитель системы
                self.symptoms_listbox.insert(tk.END, f" ─ {system_name.upper()} ─")
                self.symptoms_listbox.itemconfig(index, {'fg': 'blue', 'bg': '#e0e0e0'})
                index += 1
                
                # Добавляем симптомы этой системы
                for symptom in symptoms:
                    # Отображаем симптом
                    severity = symptom.get('severity', 1)
                    severity_stars = "★" * severity
                    display_text = f"   • {symptom['name']} {severity_stars}"
                    
                    self.symptoms_listbox.insert(tk.END, display_text)
                    
                    # Сохраняем соответствие индекса и ID симптома
                    self.symptom_index_to_id[index] = symptom['id']
                    
                    # Настраиваем цвет в зависимости от серьезности
                    if severity >= 4:
                        self.symptoms_listbox.itemconfig(index, {'fg': 'red'})
                    elif severity >= 3:
                        self.symptoms_listbox.itemconfig(index, {'fg': 'orange'})
                    
                    index += 1
                
                # Добавляем пустую строку между системами
                self.symptoms_listbox.insert(tk.END, "")
                index += 1
        except Exception as e:
            print(f"Ошибка при загрузке симптомов: {e}")
            self.symptoms_listbox.insert(tk.END, f"Ошибка загрузки: {e}")
    
    def filter_symptoms(self, event=None):
        """Фильтрация симптомов по выбранной системе"""
        self.load_symptoms_list()
        self.search_var.set("")  # Сбрасываем поиск
    
    def search_symptoms(self, event=None):
        """Поиск симптомов по тексту"""
        search_text = self.search_var.get().lower()
        if not search_text:
            return
        
        # Подсвечиваем найденные симптомы
        for i in range(self.symptoms_listbox.size()):
            item_text = self.symptoms_listbox.get(i).lower()
            if search_text in item_text:
                self.symptoms_listbox.selection_set(i)
            else:
                self.symptoms_listbox.selection_clear(i)
    
    def reset_filter(self):
        """Сброс фильтра"""
        self.system_combo.current(0)
        self.search_var.set("")
        self.load_symptoms_list()
    
    def select_all_symptoms(self):
        """Выбор всех симптомов в текущем фильтре"""
        for i in range(self.symptoms_listbox.size()):
            if i in self.symptom_index_to_id:
                self.symptoms_listbox.selection_set(i)
        # Автоматически добавляем выбранные симптомы
        self.add_selected_symptoms()
    
    def on_symptom_select(self, event):
        """Обработка выбора симптома из списка - ТЕПЕРЬ РАБОТАЕТ!"""
        # Ждем немного, чтобы событие обработалось
        self.root.after(100, self.add_selected_symptoms)
    
    def add_selected_symptoms(self):
        """Добавление выбранных симптомов в список"""
        selected_indices = self.symptoms_listbox.curselection()
        
        for idx in selected_indices:
            # Пропускаем заголовки систем и пустые строки
            if idx not in self.symptom_index_to_id:
                continue
            
            # Получаем ID симптома
            symptom_id = self.symptom_index_to_id.get(idx)
            
            if symptom_id and symptom_id not in self.selected_symptoms:
                # Получаем текст симптома (без звездочек серьезности)
                symptom_text = self.symptoms_listbox.get(idx).strip()
                # Удаляем маркер и звездочки
                if "•" in symptom_text:
                    symptom_name = symptom_text.split("•")[1].strip()
                    # Удаляем звездочки серьезности
                    symptom_name = symptom_name.replace("★", "").replace("☆", "").strip()
                else:
                    symptom_name = symptom_text
                
                # Добавляем в словарь выбранных симптомов
                self.selected_symptoms[symptom_id] = symptom_name
                
                # Добавляем в список выбранных
                self.selected_listbox.insert(tk.END, symptom_name)
    
    def remove_selected_symptom(self):
        """Удаление выбранного симптома из списка"""
        selected_idx = self.selected_listbox.curselection()
        if selected_idx:
            # Получаем текст удаляемого симптома
            symptom_text = self.selected_listbox.get(selected_idx[0])
            
            # Находим и удаляем ID симптома из словаря
            for symptom_id, name in list(self.selected_symptoms.items()):
                if name == symptom_text:
                    del self.selected_symptoms[symptom_id]
                    break
            
            # Удаляем из списка
            self.selected_listbox.delete(selected_idx[0])
    
    def clear_all_symptoms(self):
        """Очистка всех выбранных симптомов"""
        self.selected_symptoms.clear()
        self.selected_listbox.delete(0, tk.END)
    
    def perform_diagnosis(self):
        """Выполнение диагностики"""
        if not self.selected_symptoms:
            messagebox.showwarning("Нет симптомов", 
                                 "Пожалуйста, выберите хотя бы один симптом для диагностики")
            return
        
        print(f"🔍 Начинаем диагностику по {len(self.selected_symptoms)} симптомам...")
        
        # Получаем ID выбранных симптомов
        symptom_ids = list(self.selected_symptoms.keys())
        
        # Выполняем диагностику
        try:
            self.current_faults, avg_confidence = self.es.diagnose(symptom_ids)
            
            # Очищаем таблицу результатов
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            if not self.current_faults:
                messagebox.showinfo("Результат", 
                                  "По выбранным симптомам не найдено неисправностей")
                return
            
            # Заполняем таблицу результатов
            for fault in self.current_faults:
                fault_id = fault.get('id')
                code = fault.get('code', 'N/A')
                name = fault.get('name', 'Неизвестно')
                confidence = fault.get('confidence', 0)
                severity = fault.get('severity', 1)
                
                # Получаем название системы
                system_name = "Неизвестно"
                if fault_id:
                    details = self.es.db.get_fault_details(fault_id)
                    if details:
                        system_name = details.get('system_name', f"Система {fault.get('system_id', 0)}")
                
                # Определяем цвет строки по серьезности
                tags = ()
                if severity >= 4:
                    tags = ('critical',)
                elif severity >= 3:
                    tags = ('high',)
                elif severity >= 2:
                    tags = ('medium',)
                
                # Добавляем в таблицу
                self.results_tree.insert('', tk.END,
                                       values=(code, name, system_name, 
                                              f"{confidence:.1%}",
                                              '★' * severity),
                                       tags=tags, iid=str(fault_id))
            
            # Настраиваем цвета для тегов
            self.results_tree.tag_configure('critical', background='#ffcccc')
            self.results_tree.tag_configure('high', background='#fff0cc')
            self.results_tree.tag_configure('medium', background='#e8f4ff')
            
            # Очищаем детали
            self.details_text.delete(1.0, tk.END)
            
            # Сохраняем в историю
            session_data = {
                'session_id': self.current_session_id,
                'car_make': self.car_make.get(),
                'car_model': self.car_model.get(),
                'car_year': self.car_year.get(),
                'mileage': self.car_mileage.get(),
                'symptoms_selected': list(self.selected_symptoms.values()),
                'symptoms_descriptions': {},
                'faults_found': [f.get('id') for f in self.current_faults],
                'confidence': avg_confidence
            }
            
            self.es.db.save_diagnostic_session(session_data)
            
            # Показываем результат
            messagebox.showinfo("Диагностика выполнена",
                              f"Найдено {len(self.current_faults)} возможных неисправностей\n"
                              f"Средняя уверенность: {avg_confidence:.1%}")
            
        except Exception as e:
            print(f"Ошибка при диагностике: {e}")
            messagebox.showerror("Ошибка", f"Не удалось выполнить диагностику: {e}")
    
    def on_fault_select(self, event):
        """Обработка выбора неисправности из таблицы"""
        selected_items = self.results_tree.selection()
        if not selected_items:
            return
        
        fault_id = int(selected_items[0])
        
        try:
            # Получаем детали неисправности
            fault_details = self.es.db.get_fault_details(fault_id)
            if not fault_details:
                return
            
            # Получаем рекомендации
            recommendations = self.es.get_recommendations(fault_details)
            if not recommendations:
                return
            
            # Формируем текст с деталями
            details_text = f"🔧 {recommendations['name']} ({recommendations.get('code', 'N/A')})\n"
            details_text += "=" * 50 + "\n\n"
            
            details_text += f"📌 Система: {recommendations['system']}\n"
            details_text += f"⚠️  Срочность: {recommendations['urgency']}\n"
            details_text += f"💰 Ориентировочная стоимость: {recommendations['estimated_cost']}\n"
            details_text += f"⏱️  Время ремонта: {recommendations['estimated_time']}\n"
            details_text += f"📈 Серьезность: {'★' * fault_details.get('severity', 1)}\n\n"
            
            details_text += f"📖 Описание:\n{recommendations['description']}\n\n"
            
            # Получаем связанные симптомы
            related_symptoms = self.es.db.get_symptoms_for_fault(fault_id)
            if related_symptoms:
                details_text += "🔍 Связанные симптомы:\n"
                for symptom in related_symptoms:
                    details_text += f"  • {symptom['name']} (уверенность: {symptom['confidence']:.1%})\n"
                details_text += "\n"
            
            # Добавляем рекомендации
            if recommendations.get('additional_advice'):
                details_text += "💡 Рекомендации:\n"
                for advice in recommendations['additional_advice']:
                    details_text += f"  • {advice}\n"
            
            # Отображаем детали
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, details_text)
            
        except Exception as e:
            print(f"Ошибка при загрузке деталей: {e}")
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, f"Ошибка при загрузке деталей: {e}")
    
    def show_history(self):
        """Отображение истории диагностик"""
        history_window = tk.Toplevel(self.root)
        history_window.title("История диагностик")
        history_window.geometry("900x500")
        
        # Создаем вкладки
        notebook = ttk.Notebook(history_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка со списком
        list_frame = ttk.Frame(notebook)
        notebook.add(list_frame, text="📋 Список диагностик")
        
        # Таблица истории
        columns = ('ID', 'Дата', 'Марка', 'Модель', 'Симптомы', 'Неисправности', 'Уверенность')
        history_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        col_widths = {'ID': 50, 'Дата': 120, 'Марка': 80, 'Модель': 80, 
                     'Симптомы': 150, 'Неисправности': 150, 'Уверенность': 80}
        
        for col in columns:
            history_tree.heading(col, text=col)
            history_tree.column(col, width=col_widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)
        
        history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Загружаем историю
        try:
            history = self.es.db.get_diagnostics_history()
            for record in history:
                symptoms = json.loads(record['symptoms_selected'])
                faults = json.loads(record['faults_found'])
                
                history_tree.insert('', tk.END, values=(
                    record['id'],
                    record['timestamp'][:19],
                    record['car_make'] or '-',
                    record['car_model'] or '-',
                    len(symptoms),
                    len(faults),
                    f"{record['confidence']:.1%}" if record['confidence'] else '-'
                ))
        except Exception as e:
            print(f"Ошибка при загрузке истории: {e}")
            history_tree.insert('', tk.END, values=('Ошибка', str(e), '', '', '', '', ''))
        
        # Вкладка со статистикой
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📈 Статистика")
        
        try:
            stats = self.es.db.get_statistics()
            
            stats_text = f"""
            📊 СТАТИСТИКА ДИАГНОСТИК
            {'='*40}
            
            Всего выполнено диагностик: {stats['total_diagnostics']}
            Средняя уверенность диагностик: {stats['avg_confidence']:.1%}
            
            💡 Советы по использованию:
            1. Регулярно выполняйте диагностику при появлении симптомов
            2. Сохраняйте отчеты для отслеживания истории неисправностей
            3. Обращайтесь в сервис при серьезных неисправностях
            """
        except Exception as e:
            stats_text = f"Ошибка при загрузке статистики: {e}"
        
        stats_display = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD,
                                                 font=('Courier', 10))
        stats_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        stats_display.insert(1.0, stats_text)
        stats_display.config(state=tk.DISABLED)
        
        # Кнопки управления
        btn_frame = ttk.Frame(history_window)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        def refresh_history():
            """Обновление таблицы истории"""
            for item in history_tree.get_children():
                history_tree.delete(item)
            
            try:
                history = self.es.db.get_diagnostics_history()
                for record in history:
                    symptoms = json.loads(record['symptoms_selected'])
                    faults = json.loads(record['faults_found'])
                    
                    history_tree.insert('', tk.END, values=(
                        record['id'],
                        record['timestamp'][:19],
                        record['car_make'] or '-',
                        record['car_model'] or '-',
                        len(symptoms),
                        len(faults),
                        f"{record['confidence']:.1%}" if record['confidence'] else '-'
                    ))
            except Exception as e:
                print(f"Ошибка при обновлении истории: {e}")
        
        ttk.Button(btn_frame, text="Обновить", 
                  command=refresh_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Закрыть", 
                  command=history_window.destroy).pack(side=tk.RIGHT, padx=2)
    
    def save_report(self):
        """Сохранение отчета в файл"""
        if not self.current_faults:
            messagebox.showwarning("Нет данных", 
                                 "Сначала выполните диагностику для сохранения отчета")
            return
        
        from tkinter import filedialog
        
        # Предлагаем сохранить файл
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            initialfile=f"diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Заголовок
                f.write("=" * 60 + "\n")
                f.write("ОТЧЕТ О ДИАГНОСТИКЕ АВТОМОБИЛЯ\n")
                f.write("=" * 60 + "\n\n")
                
                # Информация о диагностике
                f.write(f"Дата диагностики: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"ID сессии: {self.current_session_id}\n\n")
                
                # Информация об автомобиле
                if self.car_make.get() or self.car_model.get():
                    f.write("ИНФОРМАЦИЯ ОБ АВТОМОБИЛЕ:\n")
                    f.write("-" * 40 + "\n")
                    if self.car_make.get():
                        f.write(f"Марка: {self.car_make.get()}\n")
                    if self.car_model.get():
                        f.write(f"Модель: {self.car_model.get()}\n")
                    if self.car_year.get():
                        f.write(f"Год: {self.car_year.get()}\n")
                    if self.car_mileage.get():
                        f.write(f"Пробег: {self.car_mileage.get()} км\n")
                    f.write("\n")
                
                # Выбранные симптомы
                f.write("ВЫБРАННЫЕ СИМПТОМЫ:\n")
                f.write("-" * 40 + "\n")
                for symptom in self.selected_symptoms.values():
                    f.write(f"• {symptom}\n")
                f.write(f"\nВсего симптомов: {len(self.selected_symptoms)}\n\n")
                
                # Найденные неисправности
                f.write("НАЙДЕННЫЕ НЕИСПРАВНОСТИ:\n")
                f.write("-" * 40 + "\n")
                
                for fault in self.current_faults:
                    fault_id = fault.get('id')
                    if fault_id:
                        details = self.es.db.get_fault_details(fault_id)
                        if details:
                            f.write(f"\n{details.get('name')} ({details.get('code', 'N/A')}):\n")
                            f.write(f"  Система: {details.get('system_name', 'Неизвестно')}\n")
                            f.write(f"  Серьезность: {details.get('severity', 1)}/5\n")
                            f.write(f"  Уверенность: {fault.get('confidence', 0):.1%}\n")
                            f.write(f"  Описание: {details.get('description', 'Нет описания')}\n")
                            f.write(f"  Стоимость ремонта: {details.get('repair_cost_min', 0)}-{details.get('repair_cost_max', 0)} руб\n")
                            f.write(f"  Время ремонта: {details.get('repair_time_min', 0)}-{details.get('repair_time_max', 0)} часов\n")
                
                # Рекомендации
                f.write("\n" + "=" * 60 + "\n")
                f.write("ВАЖНО: Данный отчет является предварительным.\n")
                f.write("Для точной диагностики обратитесь в специализированный сервис.\n")
                f.write("=" * 60 + "\n")
            
            messagebox.showinfo("Успех", f"Отчет успешно сохранен в файл:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчет:\n{str(e)}")
    
    def show_statistics(self):
        """Отображение статистики"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Статистика диагностик")
        stats_window.geometry("500x400")
        
        try:
            stats = self.es.db.get_statistics()
            
            stats_text = f"""
            📊 СТАТИСТИКА ДИАГНОСТИК
            {'='*40}
            
            Всего выполнено диагностик: {stats['total_diagnostics']}
            Средняя уверенность диагностик: {stats['avg_confidence']:.1%}
            
            ⚠️  Дополнительная статистика будет доступна
                после накопления большего количества данных.
            
            💡 Советы по использованию:
            1. Регулярно выполняйте диагностику при появлении симптомов
            2. Сохраняйте отчеты для отслеживания истории неисправностей
            3. Обращайтесь в сервис при серьезных неисправностях
            """
        except Exception as e:
            stats_text = f"Ошибка при загрузке статистики: {e}"
        
        text = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD,
                                        font=('Courier', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(1.0, stats_text)
        text.config(state=tk.DISABLED)
        
        ttk.Button(stats_window, text="Закрыть", 
                  command=stats_window.destroy).pack(pady=10)
    
    def show_help(self):
        """Отображение справки"""
        help_text = """
        🚗 ЭКСПЕРТНАЯ СИСТЕМА ДИАГНОСТИКИ АВТОМОБИЛЕЙ
        
        ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:
        
        1. ВЫБОР СИМПТОМОВ:
           • В левой панели выберите систему автомобиля из выпадающего списка
           • Выделите симптомы из списка (они появятся в центральной панели)
           • Для удаления симптома выделите его в центральной панели и нажмите "Удалить выбранный"
           • Для очистки всех симптомов нажмите "Очистить все"
        
        2. ДИАГНОСТИКА:
           • Нажмите кнопку "ВЫПОЛНИТЬ ДИАГНОСТИКУ"
           • В правой панели появятся возможные неисправности
           • Цвет строки указывает на серьезность неисправности:
             - Красный: критическая неисправность
             - Желтый: серьезная неисправность
             - Синий: средняя серьезность
        
        3. ПРОСМОТР ДЕТАЛЕЙ:
           • Выберите неисправность в таблице для просмотра деталей
           • В нижней панели появится подробное описание и рекомендации
        
        4. ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ:
           • "История диагностик" - просмотр предыдущих диагностик
           • "Сохранить отчет" - сохранение результатов в текстовый файл
           • "Статистика" - просмотр статистики диагностик
        
        ⚠️ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ:
        Данная система предоставляет только предварительную диагностику.
        Для точного определения и ремонта неисправностей обязательно
        обратитесь в специализированный автомобильный сервис.
        
        Система использует базу знаний с более чем 25 симптомами
        и 15+ наиболее распространенными неисправностями автомобилей.
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Справка по использованию системы")
        help_window.geometry("700x500")
        
        text_area = scrolledtext.ScrolledText(help_window, wrap=tk.WORD,
                                             font=('Arial', 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(1.0, help_text)
        text_area.config(state=tk.DISABLED)
        
        ttk.Button(help_window, text="Закрыть", 
                  command=help_window.destroy).pack(pady=10)