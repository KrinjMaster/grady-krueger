import os
import time

import cv2 as cv
from django.conf import settings

from .utils import Test_Config, check_answers, define_correct_answers, proccess_image


def run():
    # start = time.time()
    imgs_path = os.path.join(settings.BASE_DIR.__str__() + "/bot/scripts/")
    answers_image = cv.imread(imgs_path + "template.jpeg")

    assert answers_image is not None, "No image found!"

    test_config = Test_Config(rows=10, columns=2, n=3, is_multiple_answer=False)

    (answers_by_groups, answers_thresh, answers_transformed) = proccess_image(
        answers_image, test_config
    )

    (transformed_correct, marked_correct_answers) = define_correct_answers(
        answers_by_groups, answers_thresh, answers_transformed, test_config
    )

    test_config.set_correct_answers(marked_correct_answers)

    (
        marked_answers_by_groups,
        marked_answered_thresh,
        marked_answered_transformed,
    ) = proccess_image(answers_image, test_config)

    (
        correct_answers_count,
        partially_correct_answers_count,
        wrong_answers_count,
        checked_transformed,
    ) = check_answers(
        marked_answered_thresh,
        marked_answered_transformed,
        marked_answers_by_groups,
        test_config,
    )

    print(
        correct_answers_count,
        partially_correct_answers_count,
        wrong_answers_count,
    )

    cv.imshow("checked", checked_transformed)
    cv.imshow("checked1", transformed_correct)
    cv.waitKey(0)
    cv.destroyAllWindows()
    #
    # checked_transformed_list = []
    #
    #
    # for i in range(1, 6):
    #     answered_questions = cv.imread("test12 work" + str(i) + ".jpg")
    #
    #     (answered_answers_by_groups, answered_thresh, answered_transformed) = (
    #         helpers.proccess_image(answered_questions, rows, columns, n)
    #     )
    #
    #     (
    #         correct_answers_count,
    #         partially_correct_answers_count,
    #         wrong_answers_count,
    #         checked_transformed,
    #     ) = helpers.check_answers(
    #         answered_thresh,
    #         answered_transformed,
    #         answered_answers_by_groups,
    #         marked_correct_answers,
    #         rows,
    #         columns,
    #         n,
    #         is_multiple_answers,
    #     )
    #
    #     checked_transformed_list.append(checked_transformed)
    #
    # end = time.time()
    #
    # print(end - start)
    #
    # cv.imshow("transformed correct", answers_transformed)
    #
    # for i in range(len(checked_transformed_list)):
    #     cv.imshow("transformed answered " + str(i), checked_transformed_list[i])

    # cv.imshow("template", template)
    # cv.waitKey(0)
    # cv.destroyAllWindows()
