import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Функция для записи в файл
def write_records(data):
    with open("records.txt", "w") as file:
        file.write(f"ФИО: {data['name']}, Забронированное время: {data['date']}\n")

# Функция для запуска бота
def startbot():
    # Установка уровня логирования
    logging.basicConfig(level=logging.INFO)
    # Чтение токена бота из файла token
    with open('token.txt', 'r') as f:
        token = f.read().strip()
    # Инициализация бота и диспетчера
    bot = Bot(token)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    # Описание состояний для FSM (Finite State Machine)
    class BookingForm(StatesGroup):
        waiting_for_name = State()
        waiting_for_doctor = State()
        waiting_for_date = State()

    # Обработчик команды /start
    @dp.message_handler(Command("start"))
    async def cmd_start(message: types.Message):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [KeyboardButton(text="Записаться в больницу")]
        keyboard.add(*buttons)
        await message.answer("Привет! Я чат-бот для записи в больницу. Что бы вы хотели сделать?", reply_markup=keyboard)

    # Обработчик выбора "Записаться в больницу"
    @dp.message_handler(lambda message: message.text == "Записаться в больницу", state="*")
    async def start_booking(message: types.Message):
        await BookingForm.waiting_for_name.set()
        await message.answer("Введите ФИО пациента:")

    # Обработчик ФИО пациента
    @dp.message_handler(state=BookingForm.waiting_for_name)
    async def process_name(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['name'] = message.text
        await BookingForm.waiting_for_doctor.set()
        await message.answer("Выберите врача:", reply_markup=doctors_keyboard())

    # Обработчик выбора врача
    @dp.message_handler(lambda message: message.text in ["Кошелев К.П.", "Малышева Е.В."], state=BookingForm.waiting_for_doctor)
    async def process_doctor(message: types.Message, state: FSMContext):
        async with state.proxy() as data: # доступ к state в виде списка
            data['doctor'] = message.text
        await BookingForm.waiting_for_date.set()
        await message.answer("Выберите дату и время:", reply_markup=dates_keyboard())

    # Обработчик выбора даты и времени
    @dp.message_handler(lambda message: message.text in ["21 мая, 13:25", "23 мая, 15:10", "24 мая, 11:45"], state=BookingForm.waiting_for_date)
    async def process_date(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['date'] = message.text
            write_records(data)  # Записываем данные в файл
        await state.finish()
        await message.answer("Вы успешно записаны в больницу!")

    # Генерация клавиатуры для выбора врача
    def doctors_keyboard():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [KeyboardButton(text="Кошелев К.П."), KeyboardButton(text="Малышева Е.В.")]
        keyboard.add(*buttons)
        return keyboard

    # Генерация клавиатуры для выбора даты и времени
    def dates_keyboard():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [KeyboardButton(text="21 мая, 13:25"), KeyboardButton(text="23 мая, 15:10"), KeyboardButton(text="24 мая, 11:45")]
        keyboard.add(*buttons)
        return keyboard
    executor.start_polling(dp, skip_updates=True)