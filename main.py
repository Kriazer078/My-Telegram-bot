# -*- coding: utf-8 -*-
import logging
import os
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

# --- Конфигурация ---
# !!! ВАЖНО: ЗАМЕНИ "7632880638:AAG62txJ2_o3NIaMhHIcqyS9MTqBqAxb014" НА СВОЙ НАСТОЯЩИЙ ТОКЕН !!!
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7632880638:AAG62txJ2_o3NIaMhHIcqyS9MTqBqAxb014")

# --- Настройка логирования ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Если хочешь видеть сообщения "Сравнение:", измени INFO на DEBUG:
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
# )
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --- Данные для Реакций (РАСШИРЕННЫЙ СПИСОК) ---
# Ключ - кортеж реагентов (сортировка, стандартный регистр), значение - строка реакции
REACTIONS_DATA = {
    # === Реакции Соединения ===
    ('H2', 'O2'): "2H2 + O2 -> 2H2O",                      # Водород + Кислород
    ('Cl2', 'Na'): "2Na + Cl2 -> 2NaCl",                   # Натрий + Хлор
    ('Fe', 'S'): "Fe + S -> FeS",                          # Железо + Сера (при нагревании)
    ('CaO', 'H2O'): "CaO + H2O -> Ca(OH)2",               # Оксид кальция + Вода
    ('H2O', 'SO3'): "SO3 + H2O -> H2SO4",               # Оксид серы(VI) + Вода
    ('H2', 'N2'): "N2 + 3H2 -> 2NH3",                      # Азот + Водород (синтез аммиака)
    ('O2', 'P'): "4P + 5O2 -> 2P2O5",                      # Фосфор + Кислород
    ('Al', 'O2'): "4Al + 3O2 -> 2Al2O3",                  # Алюминий + Кислород
    ('H2', 'Cl2'): "H2 + Cl2 -> 2HCl",                     # Водород + Хлор (на свету)
    ('H2O', 'SO2'): "SO2 + H2O <=> H2SO3",              # Оксид серы(IV) + Вода
    ('K2O', 'H2O'): "K2O + H2O -> 2KOH",                  # Оксид калия + Вода
    ('Mg', 'O2'): "2Mg + O2 -> 2MgO",                     # Магний + Кислород

    # === Реакции Разложения ===
    ('CaCO3',): "CaCO3 -> CaO + CO2",                     # Карбонат кальция (при нагревании)
    ('KClO3',): "2KClO3 -> 2KCl + 3O2",                    # Хлорат калия (кат. MnO2, нагрев)
    ('H2O2',): "2H2O2 -> 2H2O + O2",                       # Пероксид водорода (кат. MnO2)
    ('H2O',): "2H2O -> 2H2 + O2",                          # Вода (электролиз)
    ('NH4NO3',): "NH4NO3 -> N2O + 2H2O",                   # Нитрат аммония (нагрев)
    ('Cu(OH)2',): "Cu(OH)2 -> CuO + H2O",                 # Гидроксид меди(II) (нагрев)
    ('NaHCO3',): "2NaHCO3 -> Na2CO3 + CO2 + H2O",         # Гидрокарбонат натрия (нагрев)
    ('HNO3',): "4HNO3 -> 4NO2 + O2 + 2H2O",                # Азотная кислота (на свету или нагрев)
    ('(CuOH)2CO3',): "(CuOH)2CO3 -> 2CuO + H2O + CO2",    # Гидроксокарбонат меди(II) (малахит, нагрев)

    # === Реакции Замещения ===
    ('CuSO4', 'Zn'): "Zn + CuSO4 -> ZnSO4 + Cu",           # Цинк + Сульфат меди(II)
    ('CuSO4', 'Fe'): "Fe + CuSO4 -> FeSO4 + Cu",           # Железо + Сульфат меди(II)
    ('HCl', 'Zn'): "Zn + 2HCl -> ZnCl2 + H2",              # Цинк + Соляная кислота
    ('HCl', 'Mg'): "Mg + 2HCl -> MgCl2 + H2",              # Магний + Соляная кислота
    ('KBr', 'Cl2'): "Cl2 + 2KBr -> 2KCl + Br2",            # Хлор + Бромид калия
    ('H2O', 'Na'): "2Na + 2H2O -> 2NaOH + H2",             # Натрий + Вода
    ('AgNO3', 'Cu'): "Cu + 2AgNO3 -> Cu(NO3)2 + 2Ag",      # Медь + Нитрат серебра
    ('CuO', 'H2'): "CuO + H2 -> Cu + H2O",                 # Оксид меди(II) + Водород (нагрев)
    ('Al', 'HCl'): "2Al + 6HCl -> 2AlCl3 + 3H2",           # Алюминий + Соляная кислота
    ('H2SO4', 'Zn'): "Zn + H2SO4 -> ZnSO4 + H2",           # Цинк + Серная кислота (разб.)

    # === Реакции Обмена (Нейтрализация) ===
    ('HCl', 'NaOH'): "HCl + NaOH -> NaCl + H2O",           # Соляная к-та + Гидроксид натрия
    ('H2SO4', 'KOH'): "H2SO4 + 2KOH -> K2SO4 + 2H2O",     # Серная к-та + Гидроксид калия
    ('Ca(OH)2', 'HNO3'): "Ca(OH)2 + 2HNO3 -> Ca(NO3)2 + 2H2O", # Гидроксид кальция + Азотная к-та
    ('H3PO4', 'NaOH'): "H3PO4 + 3NaOH -> Na3PO4 + 3H2O", # Фосфорная к-та + Гидроксид натрия

    # === Реакции Обмена (Выпадение Осадка) ===
    ('AgNO3', 'NaCl'): "AgNO3 + NaCl -> AgCl(s) + NaNO3",   # Нитрат серебра + Хлорид натрия
    ('BaCl2', 'Na2SO4'): "BaCl2 + Na2SO4 -> BaSO4(s) + 2NaCl",# Хлорид бария + Сульфат натрия
    ('KI', 'Pb(NO3)2'): "Pb(NO3)2 + 2KI -> PbI2(s) + 2KNO3", # Нитрат свинца(II) + Йодид калия
    ('CuSO4', 'NaOH'): "CuSO4 + 2NaOH -> Cu(OH)2(s) + Na2SO4",# Сульфат меди(II) + Гидроксид натрия
    ('FeCl3', 'NaOH'): "FeCl3 + 3NaOH -> Fe(OH)3(s) + 3NaCl",# Хлорид железа(III) + Гидроксид натрия
    ('CaCl2', 'Na2CO3'): "CaCl2 + Na2CO3 -> CaCO3(s) + 2NaCl",# Хлорид кальция + Карбонат натрия

    # === Реакции Обмена (Выделение Газа) ===
    ('HCl', 'Na2CO3'): "Na2CO3 + 2HCl -> 2NaCl + H2O + CO2(g)",# Карбонат натрия + Соляная к-та
    ('FeS', 'HCl'): "FeS + 2HCl -> FeCl2 + H2S(g)",           # Сульфид железа(II) + Соляная к-та
    ('NH4Cl', 'NaOH'): "NH4Cl + NaOH -> NaCl + NH3(g) + H2O", # Хлорид аммония + Гидроксид натрия (нагрев)
    ('HCl', 'NaHCO3'): "NaHCO3 + HCl -> NaCl + H2O + CO2(g)", # Гидрокарбонат натрия + Соляная к-та

    # === Реакции Горения ===
    ('CH4', 'O2'): "CH4 + 2O2 -> CO2 + 2H2O",              # Метан + Кислород
    ('C2H5OH', 'O2'): "C2H5OH + 3O2 -> 2CO2 + 3H2O",       # Этанол + Кислород
    ('C6H12O6', 'O2'): "C6H12O6 + 6O2 -> 6CO2 + 6H2O",     # Глюкоза + Кислород
    ('C3H8', 'O2'): "C3H8 + 5O2 -> 3CO2 + 4H2O",          # Пропан + Кислород
    ('O2', 'S'): "S + O2 -> SO2",                          # Сера + Кислород
    ('H2S', 'O2'): "2H2S + 3O2 -> 2SO2 + 2H2O",            # Сероводород + Кислород (избыток)
    ('C', 'O2'): "C + O2 -> CO2",                          # Углерод + Кислород (избыток)
    ('CO', 'O2'): "2CO + O2 -> 2CO2",                     # Угарный газ + Кислород

    # === Другие Важные Реакции ===
    ('CO', 'Fe2O3'): "Fe2O3 + 3CO -> 2Fe + 3CO2",          # Восстановление железа в домне
    ('HCl', 'MnO2'): "MnO2 + 4HCl -> MnCl2 + Cl2 + 2H2O",   # Получение хлора
    ('Cl2', 'H2O'): "Cl2 + H2O <=> HCl + HClO",            # Хлор + Вода
}

TRUE_FALSE_QUIZ_QUESTIONS = [
    # --- Старые вопросы ---
    ("Реакция NaOH + HCl -> NaCl + H2O является реакцией нейтрализации.", True),
    ("Формула серной кислоты - H2SO4.", True),
    ("При горении метана (CH4) образуется угарный газ и вода.", False), # Образуется CO2 (углекислый газ)
    ("Реакция 2H2 + O2 -> 2H2O правильно сбалансирована.", True),
    ("Реакция H2 + O2 -> H2O правильно сбалансирована.", False), # Не хватает коэффициентов
    ("Цинк (Zn) вытесняет медь (Cu) из раствора CuSO4.", True), # Т.к. цинк активнее меди
    ("Золото (Au) реагирует с соляной кислотой (HCl).", False), # Золото - малоактивный металл
    ("Вода является кислотой.", False), # Вода амфотерна (может быть и кислотой, и основанием в разных реакциях)
    ("Лакмус в щелочной среде становится синим.", True),
    ("Атомный номер Кислорода (O) - 16.", False), # Номер 8, атомная масса около 16

    # --- Новые вопросы ---
    ("Молярная масса показывает массу одного моля вещества в граммах (г/моль).", True),
    ("Номер периода в таблице Менделеева показывает число валентных электронов.", False), # Номер группы (для главных подгрупп)
    ("Оксиды - это сложные вещества, состоящие из двух элементов, один из которых кислород в степени окисления -2.", True),
    ("Все вещества, содержащие водород, являются кислотами.", False), # Пример: метан (CH4), аммиак (NH3) - не кислоты
    ("Скорость химической реакции обычно увеличивается при повышении температуры.", True),
    ("Ингибиторы - это вещества, ускоряющие химическую реакцию.", False), # Замедляют
    ("Фенолфталеин в щелочной среде становится малиновым.", True),
    ("Атом состоит только из протонов и электронов.", False), # Есть еще нейтроны (кроме основного изотопа водорода)
    ("Изотопы - это атомы одного и того же элемента с разным числом нейтронов.", True),
    ("Реакция соединения - это реакция, при которой из одного сложного вещества образуется несколько других.", False), # Это реакция разложения
    ("Моль - это единица измерения количества вещества.", True),
    ("При смешивании раствора кислоты и раствора щелочи всегда выпадает осадок.", False), # Образуется соль и вода, соль может быть растворимой
    ("Электролиты - это вещества, растворы или расплавы которых проводят электрический ток.", True),
    ("Кремний (Si) - это типичный металл.", False), # Это неметалл (или металлоид)
    ("Ковалентная связь образуется за счет общих электронных пар.", True),
    ("В молекуле азота N2 тройная ковалентная связь.", True),
    ("Щелочи - это растворимые в воде основания.", True),
    ("Реакция 'серебряного зеркала' используется для обнаружения альдегидов.", True),
    ("Нефть является индивидуальным химическим веществом.", False), # Это сложная смесь веществ
    ("Алмаз и графит состоят из атомов разных химических элементов.", False), # Оба состоят из углерода (аллотропные модификации)
]
# --- Вспомогательные функции ---
# (build_main_menu - без изменений)
def build_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("⚖️ Найти Реакцию", callback_data='find_reaction')],
        [InlineKeyboardButton("✔️ Викторина: Верно/Неверно", callback_data='quiz_true_false')],
        [InlineKeyboardButton("🖼️ Таблица Менделеева", callback_data='periodic_table_image')],
        [InlineKeyboardButton("📚 Лекции", callback_data='lectures')],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Обработчики команд ---
# (start_command, menu_command - без изменений)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет, {user.mention_html()}! 👋 Я твой помощник по химии."
        "\n\nИспользуй /menu для доступа к функциям.",
        reply_markup=build_main_menu()
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('📌 Главное меню:', reply_markup=build_main_menu())

# --- Логика для Викторины "Верно/Неверно" ---
# (start_true_false_quiz, handle_quiz_answer - без изменений)
async def start_true_false_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not TRUE_FALSE_QUIZ_QUESTIONS:
        text = "Извините, вопросы для викторины еще не добавлены."
        reply_markup = build_main_menu() if query else None # Показываем меню, если нет вопросов
        if query: await query.edit_message_text(text, reply_markup=reply_markup)
        else: await update.message.reply_text(text, reply_markup=reply_markup)
        return

    question_text, correct_answer_bool = random.choice(TRUE_FALSE_QUIZ_QUESTIONS)
    context.user_data['quiz_correct_answer'] = correct_answer_bool
    context.user_data['quiz_question_text'] = question_text
    logger.info(f"Задан вопрос: '{question_text}', правильный ответ: {correct_answer_bool}")

    keyboard = [
        [
            InlineKeyboardButton("✔️ Верно", callback_data='quiz_answer_true'),
            InlineKeyboardButton("❌ Неверно", callback_data='quiz_answer_false')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text_to_send = f"❓ **Вопрос:**\n\n{question_text}"

    try:
        if query:
            await query.edit_message_text(text_to_send, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_html(text_to_send, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка при отправке вопроса викторины: {e}")
        if query:
             await context.bot.send_message(chat_id=query.message.chat_id, text="Не удалось обновить предыдущее сообщение. Новый вопрос:")
             await context.bot.send_message(chat_id=query.message.chat_id, text=text_to_send, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    user_answer_bool = (data == 'quiz_answer_true')
    correct_answer_bool = context.user_data.get('quiz_correct_answer')
    original_question_text = context.user_data.get('quiz_question_text', "Вопрос")

    if correct_answer_bool is None:
        await query.edit_message_text("🤔 Ой, я не помню, какой был вопрос...", reply_markup=build_main_menu())
        return

    if user_answer_bool == correct_answer_bool:
        feedback = "✅ Правильно!"
    else:
        feedback = f"❌ Неверно. Правильный ответ был бы: **{'Верно' if correct_answer_bool else 'Неверно'}**."

    keyboard = [
         [InlineKeyboardButton("🔄 Следующий вопрос", callback_data='quiz_true_false')],
         [InlineKeyboardButton("« Назад в меню", callback_data='main_menu')] # Кнопка "Назад"
     ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"❓ **Вопрос:**\n\n{original_question_text}\n\n{feedback}", reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    context.user_data.pop('quiz_correct_answer', None)
    context.user_data.pop('quiz_question_text', None)


# --- Обработчик кнопок ---
# (button_handler - без изменений, использует 'periodic_table_image')
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Нажата кнопка: {data}")

    if data in ['quiz_answer_true', 'quiz_answer_false']:
        await handle_quiz_answer(update, context)
        return

    context.user_data.pop('next_action', None)

    if data == 'find_reaction':
        await query.edit_message_text(
            text="Введите реагенты через '+' (например, `Na + Cl2` или `CaCO3`). Я поищу реакцию."
        )
        context.user_data['next_action'] = 'find_reaction_in_dict'
    elif data == 'quiz_true_false':
        await start_true_false_quiz(update, context)
    elif data == 'periodic_table_image':
        image_path = 'periodic_table.jpg' # Имя файла с картинкой таблицы
        # Убедись, что файл periodic_table.jpg лежит в той же папке, что и скрипт бота
        message_to_edit = query.message
        try:
            # Отправляем фото как новое сообщение
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=open(image_path, 'rb'),
                caption="Таблица Менделеева"
            )
            # Убираем кнопки из старого сообщения (где нажали "Таблица Менделеева")
            await query.edit_message_reply_markup(reply_markup=None)
            # Сразу отправляем новое сообщение с главным меню
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="📌 Главное меню:", # Возвращаем текст меню
                reply_markup=build_main_menu()
            )
        except FileNotFoundError:
            logger.error(f"Файл картинки не найден: {image_path}")
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Ошибка: Не могу найти файл '{image_path}'.")
            # Возвращаем главное меню в любом случае
            await context.bot.send_message(chat_id=query.message.chat_id, text="📌 Главное меню:", reply_markup=build_main_menu())
        except Exception as e:
            logger.error(f"Ошибка при отправке фото: {e}", exc_info=True)
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Произошла ошибка при отправке изображения.")
            await context.bot.send_message(chat_id=query.message.chat_id, text="📌 Главное меню:", reply_markup=build_main_menu())

    elif data == 'lectures':
        await query.edit_message_text(text="📚 Раздел лекций (в разработке).")
    elif data == 'main_menu':
         try:
              await query.edit_message_text('📌 Главное меню:', reply_markup=build_main_menu())
         except Exception as e:
              logger.warning(f"Не удалось отредактировать сообщение для main_menu: {e}. Отправляю новое.")
              await context.bot.send_message(chat_id=query.message.chat_id, text='📌 Главное меню:', reply_markup=build_main_menu())
    else:
        try:
            await query.edit_message_text(text="🤔 Неизвестная опция.")
        except Exception as e:
            logger.warning(f"Не удалось отредактировать сообщение для опции {data}: {e}")


# --- Обработчик текстовых сообщений ---
# (message_handler - ИЗМЕНЕН только для поиска реакции)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    next_action = context.user_data.get('next_action')
    text = update.message.text.strip()

    # Этот обработчик теперь ТОЛЬКО для поиска реакций
    if next_action == 'find_reaction_in_dict':
        context.user_data['next_action'] = None # Сбрасываем состояние сразу
        message_to_reply = update.message # Запоминаем сообщение пользователя для ответа

        try:
            # Логика поиска реакции (регистронезависимая)
            if '->' in text: text = text.split('->')[0].strip()
            reactants_raw = text.split('+')
            reactants = sorted([r.strip() for r in reactants_raw if r.strip()])

            if not reactants:
                 await message_to_reply.reply_text("Не удалось распознать реагенты...")
                 # Отправляем меню после неудачного поиска
                 await message_to_reply.reply_text("Что делаем дальше?", reply_markup=build_main_menu())
                 return
            if len(reactants) > 2:
                 await message_to_reply.reply_text("Пока ищу только реакции с 1-2 реагентами.")
                 # Отправляем меню после неудачного поиска
                 await message_to_reply.reply_text("Что делаем дальше?", reply_markup=build_main_menu())
                 return

            reactants_key_input = tuple(reactants)
            reactants_key_input_lower = tuple(r.lower() for r in reactants_key_input)
            logger.info(f"Ищем реакцию: {reactants_key_input} (регистр игнорируется)")

            found_equation = None
            for dict_key, equation_str in REACTIONS_DATA.items():
                dict_key_lower = tuple(k.lower() for k in dict_key)
                logger.debug(f"Сравнение: Ввод={reactants_key_input_lower} | Словарь={dict_key_lower}")
                if dict_key_lower == reactants_key_input_lower:
                    found_equation = equation_str
                    logger.info(f"Найдено совпадение! Ключ: {dict_key}")
                    break

            if found_equation:
                await message_to_reply.reply_html(f"✅ Найдена реакция:\n<code>{found_equation}</code>")
            else:
                user_input_str = ' + '.join(reactants_key_input)
                await message_to_reply.reply_text(f"❌ Реакция для '{user_input_str}' не найдена в списке. Проверьте правильность формул.")

            # Отправляем меню после результата поиска (успешного или нет)
            await message_to_reply.reply_text("Что делаем дальше?", reply_markup=build_main_menu())

        except Exception as e:
            logger.error(f"Произошла ошибка при поиске реакции для '{text}'", exc_info=True)
            await message_to_reply.reply_text("Произошла ошибка при обработке. Убедитесь, что реагенты разделены '+'.")
            # Отправляем меню после ошибки
            await message_to_reply.reply_text("Попробуйте еще раз или выберите другое действие:", reply_markup=build_main_menu())
    else:
        # Если состояние не для поиска реакции, можем ничего не делать
        # или отправить подсказку
        # await update.message.reply_text("Используйте /menu для выбора действия.")
        pass


# --- Основная функция ---
# (main - без изменений)
def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
        logging.critical("!!! BOT_TOKEN не установлен или используется значение по умолчанию!")
        print("!!! Ошибка: BOT_TOKEN не найден или не изменен. Установите его в коде.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logging.info("Запуск бота...")
    print("Запуск бота...")
    application.run_polling()

if __name__ == "__main__":
    main()