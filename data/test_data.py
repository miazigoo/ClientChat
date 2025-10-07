# Тестовые данные клиентов
TEST_USERS = [
    {
        "id": "CRM001",
        "name": "Иванов Иван Иванович",
        "email": "ivanov@example.com",
        "phone": "+7 (999) 123-45-67",
        "status": "VIP",
        "avatar": "👤"
    },
    {
        "id": "CRM002",
        "name": "Петрова Мария Сергеевна",
        "email": "petrova@example.com",
        "phone": "+7 (999) 234-56-78",
        "status": "Обычный",
        "avatar": "👩"
    },
    {
        "id": "CRM003",
        "name": "Сидоров Петр Александрович",
        "email": "sidorov@example.com",
        "phone": "+7 (999) 345-67-89",
        "status": "Премиум",
        "avatar": "👨"
    },
    {
        "id": "CRM004",
        "name": "Козлова Елена Викторовна",
        "email": "kozlova@example.com",
        "phone": "+7 (999) 456-78-90",
        "status": "VIP",
        "avatar": "👩‍💼"
    },
    {
        "id": "CRM005",
        "name": "Морозов Андрей Дмитриевич",
        "email": "morozov@example.com",
        "phone": "+7 (999) 567-89-01",
        "status": "Обычный",
        "avatar": "👨‍💻"
    }
]

# Тестовые чаты (заявки)
# Статусы: "Новая", "В работе", "Ожидает клиента", "Ожидает оператора", "Закрыта"
TEST_CHATS = [
    {
        "id": "CH-0001",
        "user_id": "CRM001",
        "title": "Проблема входа в ЛК",
        "status": "В работе",
        "created_at": "2025-10-07 09:00",
        "updated_at": "2025-10-07 09:20",
        "messages": [
            {"sender": "operator", "operator": "Анна Петрова", "text": "Добрый день! Чем могу помочь?", "time": "09:01"},
            {"sender": "user", "text": "Не могу войти в личный кабинет.", "time": "09:02"},
            {"sender": "operator", "operator": "Анна Петрова", "text": "Какую ошибку видите при входе?", "time": "09:05"}
        ]
    },
    {
        "id": "CH-0002",
        "user_id": "CRM001",
        "title": "Вопрос по оплате",
        "status": "Закрыта",
        "created_at": "2025-10-01 14:00",
        "updated_at": "2025-10-01 15:30",
        "messages": [
            {"sender": "user", "text": "Платеж не проходит через карту.", "time": "14:05"},
            {"sender": "operator", "operator": "Анна Петрова", "text": "Проверьте лимит операций и 3DS.", "time": "14:10"},
            {"sender": "user", "text": "Проверил, всё сработало. Спасибо!", "time": "15:26"},
            {"sender": "operator", "operator": "Анна Петрова", "text": "Отлично! Тогда закрываю заявку.", "time": "15:30"}
        ]
    },
    {
        "id": "CH-0003",
        "user_id": "CRM002",
        "title": "Ошибка при загрузке файла",
        "status": "Новая",
        "created_at": "2025-10-07 10:00",
        "updated_at": "2025-10-07 10:00",
        "messages": [
            {"sender": "user", "text": "При загрузке файла появляется ошибка 413.", "time": "10:00"}
        ]
    }
]
