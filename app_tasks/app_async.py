from quart import Quart, request, jsonify, render_template, redirect, url_for, flash
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.exc import SQLAlchemyError
import os

app = Quart(__name__)
app.secret_key = os.urandom(24)
host = '127.0.0.1'
port = 5000

# Настройки базы данных
DATABASE_URL = 'sqlite+aiosqlite:///tasks.db'
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionFactory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Декларативная база моделей
Base = declarative_base()


# Модель базы данных
class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    status = Column(String(10), default='pending')  # Новое поле для статуса задачи

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
        }


@app.before_serving
async def init_db():
    """
    Инициализация базы данных перед началом обслуживания запросов.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.route('/')
@app.route('/home', methods=['GET'])
async def home_page():
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Task))
        tasks = result.scalars().all()
        return await render_template('home.html', tasks=tasks)


@app.route('/create_task', methods=['GET', 'POST'])
async def create_task():
    if request.method == 'POST':
        form_data = await request.form
        title = form_data.get('title')
        description = form_data.get('description', '')

        if not title:
            await flash('Название задачи обязательно!', 'error')
            return await render_template('create_task.html'), 400

        new_task = Task(title=title, description=description)

        async with AsyncSessionFactory() as session:
            try:
                session.add(new_task)
                await session.commit()
                await flash('Задача успешно добавлена!', 'success')
                return redirect(url_for('home_page'))
            except SQLAlchemyError:
                await session.rollback()
                await flash('Не удалось создать задачу', 'error')
                return await render_template('create_task.html'), 500
    else:
        return await render_template('create_task.html')


@app.route('/tasks', methods=['GET'])
async def get_tasks():
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Task))
        tasks = result.scalars().all()
        return jsonify([task.to_dict() for task in tasks])


@app.route('/delete_task/<int:task_id>', methods=['POST'])
async def delete_task(task_id):
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar()

        if not task:
            await flash('Задача не найдена', 'error')
            return redirect(url_for('home_page'))

        try:
            await session.delete(task)
            await session.commit()
            await flash('Задача успешно удалена!', 'success')
            return redirect(url_for('home_page'))
        except SQLAlchemyError:
            await session.rollback()
            await flash('Не удалось удалить задачу', 'error')
            return redirect(url_for('home_page'))


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
async def edit_task(task_id):
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar()

        if not task:
            await flash('Задача не найдена', 'error')
            return redirect(url_for('home_page'))

        if request.method == 'POST':
            form_data = await request.form
            title = form_data.get('title')
            description = form_data.get('description', '')

            if not title:
                await flash('Название задачи обязательно!', 'error')
                return await render_template('edit_task.html', task=task), 400

            task.title = title
            task.description = description

            try:
                await session.commit()
                await flash('Задача успешно обновлена!', 'success')
                return redirect(url_for('home_page'))
            except SQLAlchemyError:
                await session.rollback()
                await flash('Не удалось обновить задачу', 'error')
                return await render_template('edit_task.html', task=task), 500
        else:
            return await render_template('edit_task.html', task=task)


@app.route('/toggle_task_status/<int:task_id>', methods=['POST'])
async def toggle_task_status(task_id):
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar()

        if not task:
            await flash('Задача не найдена', 'error')
            return redirect(url_for('home_page'))

        task.status = 'completed' if task.status == 'pending' else 'pending'

        try:
            await session.commit()
            await flash(f'Статус задачи "{task.title}" успешно обновлен!', 'success')
            return redirect(url_for('home_page'))
        except SQLAlchemyError:
            await session.rollback()
            await flash('Не удалось обновить статус задачи', 'error')
            return redirect(url_for('home_page'))


if __name__ == '__main__':
    app.run(host=host, port=port, debug=True)