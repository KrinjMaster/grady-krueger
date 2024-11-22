import os
from pathlib import Path

import cv2 as cv
from django.conf import settings
from telebot import TeleBot
from telebot.types import BotCommand, MenuButtonCommands, Message

from .utils import *

bot = TeleBot(settings.BOT_TOKEN)
imgs_path = os.path.join(settings.BASE_DIR.__str__() + "/bot/imgs/")

# menu commands
start_command = BotCommand(command="start", description="Старт бота")
help_command = BotCommand(command="help", description="Помощь")
begin_checking_command = BotCommand(
    command="begin", description="Начать проверку работ"
)
create_template_command = BotCommand(
    command="create_template", description="Сделать шаблон теста"
)

bot.set_my_commands(
    [start_command, help_command, begin_checking_command, create_template_command]
)


# paper test config
class Config:
    is_multiple_answer = None
    columns = None
    rows = None
    n = None

    def set_multiple_answer(self, is_multiple_answer):
        self.is_multiple_answer = is_multiple_answer

    def set_columns(self, columns):
        self.columns = columns

    def set_rows(self, rows):
        self.rows = rows

    def set_n(self, n):
        self.n = n

    def clear(self):
        self.n = None
        self.rows = None
        self.is_multiple_answer = None
        self.columns = None


test_config = Config()


# message handlers
@bot.message_handler(commands=["start", "help"])
def send_welcome(message: Message):
    bot.set_chat_menu_button(message.chat.id, MenuButtonCommands("commands"))
    bot.send_message(
        message.chat.id,
        "Старт или помощь",
    )


@bot.message_handler(commands=["begin"])
def start_checking(message: Message):
    bot.send_message(
        message.chat.id,
        "Вопросы в тесте могут содержать несколько правильных ответов?\nОтвет засчитывается за 0,5 баллов, если пропущен только один ответ.(Да/Нет)",
    )

    bot.register_next_step_handler(message, choose_is_multiple_answer)


@bot.message_handler(commands=["create_template"])
def create_template(message: Message):
    bot.send_message(message.chat.id, "Выберите количество колон на листе.")

    bot.register_next_step_handler(message, choose_columns)


def choose_is_multiple_answer(message: Message):
    if str(message.text).lower() in ["да", "нет"]:
        test_config.set_multiple_answer(str(message.text).lower() == "да")

        msg = bot.send_message(message.chat.id, "Выберите количество колон на листе.")

        bot.register_next_step_handler(msg, choose_columns)
    else:
        msg = bot.send_message(
            message.chat.id,
            "Не понял вашего вопроса, попробуйте еще раз!\nОтветьте Да или Нет.",
        )

        bot.register_next_step_handler(msg, choose_is_multiple_answer)


def choose_columns(message: Message):
    if str(message.text).isnumeric() and int(str(message.text)) > 0:
        test_config.set_columns(int(str(message.text)))

        msg = bot.send_message(message.chat.id, "Выберите количество строк на листе.")

        bot.register_next_step_handler(
            msg,
            choose_rows,
        )
    else:
        msg = bot.send_message(
            message.chat.id,
            "Не понял вашего ответа, попробуйте еще раз!\nОтветьте числом или проверьте, что число неотрицательно.",
        )

        bot.register_next_step_handler(msg, choose_columns)


def choose_rows(message: Message):
    if str(message.text).isnumeric() and int(str(message.text)) > 0:
        test_config.set_rows(int(str(message.text)))

        msg = bot.send_message(
            message.chat.id, "Выберите количество ответов в одном вопросе."
        )

        bot.register_next_step_handler(
            msg,
            choose_answers_quantity,
        )
    else:
        msg = bot.send_message(
            message.chat.id,
            "Не понял вашего ответа, попробуйте еще раз!\nОтветьте числом или проверьте, что число неотрицательно.",
        )

        bot.register_next_step_handler(msg, choose_rows)


def choose_answers_quantity(
    message,
):
    if str(message.text).isnumeric() and int(str(message.text)) > 0:
        test_config.set_n(int(str(message.text)))

        # if is_multiple_answer is None, then user is creating test template and not checking tests
        if test_config.is_multiple_answer is None:
            try:
                test_template = create_test_template(
                    test_config.columns, test_config.rows, test_config.n
                )
                cv.imwrite(imgs_path + "test_template.jpg", test_template)

                bot.send_photo(
                    message.chat.id,
                    open(imgs_path + "test_template.jpg", "rb"),
                    "Вот ваш шаблон для тестов!",
                )
            except:
                bot.send_message(
                    message.chat.id,
                    "Во время генерации шаблона произошла ошибка! Попробуйте создать его снова.",
                )
                print("Something went wrong during creating template!")

            if Path(os.path.join(imgs_path + "test_template.jpg")).is_file():
                os.remove(imgs_path + "test_template.jpg")

            test_config.clear()
        else:
            msg = bot.send_message(
                message.chat.id,
                "Отправьте фотографию с правильными ответами! Если у вас нет шаблона, то воспользуйтесь командой /create_template",
            )

            bot.register_next_step_handler(msg, proccess_correct_answers)
    else:
        msg = bot.send_message(
            message.chat.id,
            "Не понял вашего ответа, попробуйте еще раз!\nОтветьте числом.",
        )

        bot.register_next_step_handler(
            msg,
            choose_answers_quantity,
        )


def proccess_correct_answers(message: Message):
    if message.photo is not None:
        # user send a message
        try:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            f = open(imgs_path + "test_correct_received.jpg", "wb")
            f.write(downloaded_file)

            answers_image = cv.imread(imgs_path + "test_correct_received.jpg")

            (answers_by_groups, answers_thresh, answers_transformed) = proccess_image(
                answers_image,
                test_config.rows,
                test_config.columns,
                test_config.n,
            )

            (transformed_correct, _) = define_correct_answers(
                answers_by_groups,
                answers_thresh,
                answers_transformed,
                test_config.rows,
                test_config.columns,
                test_config.n,
            )

            cv.imwrite(imgs_path + "test_correct.jpg", transformed_correct)

            msg = bot.send_photo(
                message.chat.id,
                open(imgs_path + "test_correct.jpg", "rb"),
                "Вот правильные ответы на ваш тест! Правильные ли ответы, выделенные зеленым ? (Да/Нет)",
            )

            bot.register_next_step_handler(msg, confirm_test_answers)
        except:
            bot.send_message(
                message.chat.id,
                "Во время обработки изображения произошла ошибка! Попробуйте снова.",
            )
            print("Error during image proccesing!")

        if Path(os.path.join(imgs_path + "test_correct.jpg")).is_file():
            os.remove(imgs_path + "test_correct.jpg")

        if Path(os.path.join(imgs_path + "test_correct_received.jpg")).is_file():
            os.remove(imgs_path + "test_correct_received.jpg")

    else:
        bot.send_message(
            message.chat.id,
            "Не понял вашего ответа, попробуйте еще раз!\nОтправьте фотографию шаблона c заполненными ответами, отправьте только одну фотографию.",
        )

        bot.register_next_step_handler(
            message,
            proccess_correct_answers,
        )


def confirm_test_answers(message: Message):
    if str(message.text).lower() == "да":
        msg = bot.send_message(
            message.chat.id,
            "Пришлите сюда фотографии заполненных тестов, которые нужно проверить !",
        )

        bot.register_next_step_handler(msg, check_tests)
    elif str(message.text).lower() == "нет":
        msg = bot.send_message(
            message.chat.id,
            "Отправьте фотографию с правильными ответами! Если у вас нет шаблона, то воспользуйтесь командой /create_template",
        )

        bot.register_next_step_handler(msg, proccess_correct_answers)
    else:
        msg = bot.send_message(
            message.chat.id,
            "Не понял вашего вопроса, попробуйте еще раз!\nОтветьте Да или Нет.",
        )

        bot.register_next_step_handler(
            msg,
            confirm_test_answers,
        )


def check_tests(message: Message):
    if message.photo is not None:
        # interate over all received photos
        for photo in message.photo[1:]:
            try:
                file_id = photo.file_id
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                f = open(imgs_path + "test_marked_received.jpg", "wb")
                f.write(downloaded_file)

                marked_answers_image = cv.imread(imgs_path + "test_marked_received.jpg")
            except:
                print("Photo could not be proccessed!")

        test_config.clear()
    else:
        msg = bot.send_message(
            message.chat.id,
            "Не понял вашего ответа, попробуйте еще раз!\nОтправьте фотографии тестов c заполненными ответами, отправьте только одну фотографию.",
        )

        bot.register_next_step_handler(msg, check_tests)


bot.infinity_polling()
