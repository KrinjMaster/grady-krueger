import os
import time
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


configs = {}


# message handlers
@bot.message_handler(commands=["start", "help"])
def send_welcome(message: Message):
    bot.set_chat_menu_button(message.chat.id, MenuButtonCommands("commands"))
    bot.send_message(
        message.chat.id,
        "Для старта проверки тестов напишите /begin, для создания шаблона - /create_template",
    )


@bot.message_handler(commands=["begin"])
def start_checking(message: Message):
    configs[message.chat.id] = Test_Config()
    bot.send_message(
        message.chat.id,
        "Вопросы в тесте могут содержать несколько правильных ответов?\nОтвет засчитывается за 0,5 баллов, если пропущен только один ответ.(Да/Нет)",
    )

    bot.register_next_step_handler(message, choose_is_multiple_answer)


@bot.message_handler(commands=["create_template"])
def create_template(message: Message):
    configs[message.chat.id] = Test_Config()

    bot.send_message(message.chat.id, "Выберите количество колон на листе.")

    bot.register_next_step_handler(message, choose_columns)


def choose_is_multiple_answer(message: Message):
    if str(message.text).lower() in ["да", "нет"]:

        configs[message.chat.id].set_multiple_answer(str(message.text).lower() == "да")

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
        configs[message.chat.id].set_columns(int(str(message.text)))

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
        configs[message.chat.id].set_rows(int(str(message.text)))

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
        configs[message.chat.id].set_n(int(str(message.text)))

        # if is_multiple_answer is None, then user is creating test template and not checking tests
        if configs[message.chat.id].is_multiple_answer is None:
            try:
                test_template = create_test_template(configs[message.chat.id])

                cv.imwrite(
                    imgs_path + str(message.chat.id) + "test_template.jpg",
                    test_template,
                )

                bot.send_photo(
                    message.chat.id,
                    open(imgs_path + str(message.chat.id) + "test_template.jpg", "rb"),
                    "Вот ваш шаблон для тестов!",
                )

            except cv.error as error:
                bot.send_message(
                    message.chat.id,
                    "Во время генерации шаблона произошла ошибка! Попробуйте создать его снова.",
                )
                print("Something went wrong during creating template!", error)

            if Path(
                os.path.join(imgs_path + str(message.chat.id) + "test_template.jpg")
            ).is_file():
                os.remove(imgs_path + str(message.chat.id) + "test_template.jpg")

            del configs[message.chat.id]
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

            f = open(
                imgs_path + str(message.chat.id) + "test_correct_received.jpg", "wb"
            )
            f.write(downloaded_file)

            answers_image = cv.imread(
                imgs_path + str(message.chat.id) + "test_correct_received.jpg"
            )

            (answers_by_groups, answers_thresh, answers_transformed) = proccess_image(
                answers_image, configs[message.chat.id]
            )

            (transformed_correct, correct_answers) = define_correct_answers(
                answers_by_groups,
                answers_thresh,
                answers_transformed,
                configs[message.chat.id],
            )

            cv.imwrite(
                imgs_path + str(message.chat.id) + "test_correct.jpg",
                transformed_correct,
            )

            configs[message.chat.id].set_correct_answers(correct_answers)

            msg = bot.send_photo(
                message.chat.id,
                open(imgs_path + str(message.chat.id) + "test_correct.jpg", "rb"),
                "Вот правильные ответы на ваш тест! Правильные ли ответы, выделенные зеленым ? (Да/Нет)",
            )

            bot.register_next_step_handler(msg, confirm_test_answers)
        except:
            bot.send_message(
                message.chat.id,
                "Во время обработки изображения произошла ошибка! Попробуйте снова.",
            )
            print("Error during image proccesing!")

        if Path(
            os.path.join(imgs_path + str(message.chat.id) + "test_correct.jpg")
        ).is_file():
            os.remove(imgs_path + str(message.chat.id) + "test_correct.jpg")

        if Path(
            os.path.join(imgs_path + str(message.chat.id) + "test_correct_received.jpg")
        ).is_file():
            os.remove(imgs_path + str(message.chat.id) + "test_correct_received.jpg")

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
            "Пришлите сюда фотографии заполненных тестов по одному !",
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
    if (
        message.photo is not None
        and configs[message.chat.id].rows is not None
        and configs[message.chat.id].columns is not None
    ):
        try:
            if len(configs[message.chat.id].correct_answers) > 0:
                file_info = bot.get_file(message.photo[-1].file_id)
                file = bot.download_file(file_info.file_path)

                f = open(
                    imgs_path + str(message.chat.id) + "test_marked_received.jpg", "wb"
                )
                f.write(file)

                marked_answers_image = cv.imread(
                    imgs_path + str(message.chat.id) + "test_marked_received.jpg"
                )

                (
                    marked_answers_by_groups,
                    marked_answered_thresh,
                    marked_answered_transformed,
                ) = proccess_image(marked_answers_image, configs[message.chat.id])

                (
                    correct_answers_count,
                    partially_correct_answers_count,
                    wrong_answers_count,
                    checked_transformed,
                ) = check_answers(
                    marked_answered_thresh,
                    marked_answered_transformed,
                    marked_answers_by_groups,
                    configs[message.chat.id],
                )

                cv.imwrite(
                    imgs_path + str(message.chat.id) + "test_checked.jpg",
                    checked_transformed,
                )

                bot.send_photo(
                    message.chat.id,
                    open(imgs_path + str(message.chat.id) + "test_checked.jpg", "rb"),
                    f"Вот проверенный тест!\nВсего правильных баллов: {correct_answers_count + partially_correct_answers_count * 0.5}/{configs[message.chat.id].columns * configs[message.chat.id].rows}\nКоличество полностью правильных ответов: {correct_answers_count}\nКоличество частисно правильных ответов: {partially_correct_answers_count}\nКоличество неправильных ответов: {wrong_answers_count}\nЗелёным отмечены те ответы, которые были отвечены правильно. Синим отмечены те ответы, которые являются правильными, но ученик пропустил. Красным отмечены ответы, которые ученик отметил неправильно.",
                )

                if Path(
                    os.path.join(imgs_path + str(message.chat.id) + "test_checked.jpg")
                ).is_file():
                    os.remove(imgs_path + str(message.chat.id) + "test_checked.jpg")

                if Path(
                    os.path.join(
                        imgs_path + str(message.chat.id) + "test_marked_received.jpg"
                    )
                ).is_file():
                    os.remove(
                        imgs_path + str(message.chat.id) + "test_marked_received.jpg"
                    )

                msg = bot.send_message(
                    message.chat.id,
                    "Вы хотите отправить ещё фотографии тестов ? (Да/Нет)",
                )

                bot.register_next_step_handler(msg, proced_to_check_tests)
        except Exception as err:
            print("Photo could not be proccessed!", err)

    else:
        msg = bot.send_message(
            message.chat.id,
            "Не понял вашего ответа, попробуйте еще раз!\nОтправьте фотографии тестов c заполненными ответами, отправьте только одну фотографию.",
        )

        bot.register_next_step_handler(msg, check_tests)


def proced_to_check_tests(message: Message):
    if str(message.text).lower() == "да":
        msg = bot.send_message(
            message.chat.id,
            "Пришлите сюда фотографии заполненных тестов по одному !",
        )

        bot.register_next_step_handler(msg, check_tests)
    elif str(message.text).lower() == "нет":
        del configs[message.chat.id]
        bot.send_message(
            message.chat.id, "Это все проверенные тесты, которые вы прислали!"
        )
    else:
        msg = bot.send_message(
            message.chat.id,
            "Не понял вашего ответа, ответьте да или нет.",
        )


print("bot started")
bot.infinity_polling()
