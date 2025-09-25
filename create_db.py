from app import app, db

with app.app_context():
    db.drop_all()   #  Удаляет все старые таблицы
    db.create_all() #  Создаёт таблицы заново с актуальными моделями

print("База данных пересоздана!")