class ExpertSystem:
    def __init__(self, database):
        self.db = database
    
    def diagnose(self, symptom_ids):
        """Основная функция диагностики"""
        if not symptom_ids:
            return [], 0.0
        
        # Получаем возможные неисправности
        faults = self.db.get_faults_by_symptoms(symptom_ids)
        
        if not faults:
            return [], 0.0
        
        # Рассчитываем среднюю уверенность
        if faults:
            avg_confidence = sum(fault.get('confidence', 0) for fault in faults) / len(faults)
        else:
            avg_confidence = 0.0
        
        return faults, avg_confidence
    
    def get_recommendations(self, fault):
        """Получение рекомендаций по неисправности"""
        if not fault:
            return None
        
        # Определяем срочность по серьезности
        severity = fault.get('severity', 1)
        urgency_map = {
            1: "Низкая срочность - можно отложить ремонт",
            2: "Средняя срочность - рекомендуется скоро устранить",
            3: "Высокая срочность - требуется срочный ремонт",
            4: "Критическая - немедленно прекратить эксплуатацию",
            5: "Опасная - движение запрещено"
        }
        
        recommendations = {
            'name': fault.get('name', 'Неизвестная неисправность'),
            'code': fault.get('code', 'N/A'),
            'system': fault.get('system_name', 'Неизвестная система'),
            'severity': severity,
            'urgency': urgency_map.get(severity, "Не определена"),
            'description': fault.get('description', 'Нет описания'),
            'estimated_cost': f"{fault.get('repair_cost_min', 0)}-{fault.get('repair_cost_max', 0)} руб",
            'estimated_time': f"{fault.get('repair_time_min', 0)}-{fault.get('repair_time_max', 0)} часов",
            'additional_advice': self._get_additional_advice(fault)
        }
        
        return recommendations
    
    def _get_additional_advice(self, fault):
        """Генерация дополнительных советов"""
        system = fault.get('system_name', '')
        severity = fault.get('severity', 1)
        
        advice = []
        
        if severity >= 4:
            advice.append("⚠️ НЕМЕДЛЕННО прекратите эксплуатацию автомобиля!")
        elif severity >= 3:
            advice.append("⚠️ Рекомендуется обратиться в сервис как можно скорее")
        
        if "Двигатель" in system:
            advice.append("🔧 Проверьте уровень масла и охлаждающей жидкости")
            if severity >= 4:
                advice.append("🚫 Не продолжайте движение при перегреве двигателя")
        elif "Тормоз" in system:
            advice.append("🛑 Проверьте уровень тормозной жидкости")
            advice.append("🚫 Избегайте резких торможений и высокой скорости")
        elif "Подвеск" in system or "Рулев" in system:
            advice.append("🔄 Проверьте состояние шин и давление в них")
            advice.append("🚗 Избегайте неровных дорог и высоких скоростей")
        
        advice.append("📞 Перед ремонтом получите несколько оценок от разных сервисов")
        advice.append("📋 Сохраните этот отчет для консультации с механиком")
        
        return advice