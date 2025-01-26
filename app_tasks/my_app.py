from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Модель для задач
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(10), nullable=False, default='pending')  # Новый статус задачи

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status
        }

# Создание таблиц, если они ещё не созданы
with app.app_context():
    db.create_all()

# Главная страница
@app.route('/')
@app.route('/home')
def home():
    tasks = Task.query.all()
    return render_template('home.html', tasks=tasks)

# Страница создания задачи
@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')

        if not title:
            flash('Название задачи обязательно!', 'error')
            return redirect(url_for('create_task'))

        new_task = Task(title=title, description=description)
        try:
            db.session.add(new_task)
            db.session.commit()
            flash('Задача успешно добавлена!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('Не удалось создать задачу', 'error')
            return redirect(url_for('create_task'))

    return render_template('create_task.html')

# API для получения всех задач в формате JSON
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks])

# Удаление задачи
@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    try:
        db.session.delete(task)
        db.session.commit()
        flash('Задача успешно удалена!', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        flash('Не удалось удалить задачу', 'error')
        return redirect(url_for('home'))

# Редактирование задачи
@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')

        if not title:
            flash('Название задачи обязательно!', 'error')
            return redirect(url_for('edit_task', task_id=task_id))

        task.title = title
        task.description = description
        try:
            db.session.commit()
            flash('Задача успешно обновлена!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('Не удалось обновить задачу', 'error')
            return redirect(url_for('edit_task', task_id=task_id))

    return render_template('edit_task.html', task=task)

# Обновление статуса задачи (выполнена или не выполнена)
@app.route('/toggle_task_status/<int:task_id>', methods=['POST'])
def toggle_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    task.status = 'completed' if task.status == 'pending' else 'pending'
    
    try:
        db.session.commit()
        flash(f'Задача "{task.title}" успешно обновлена!', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        flash('Не удалось обновить статус задачи', 'error')
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
