import os
from pathlib import Path

import cv2 as cv
from utils2 import Test_Config, check_answers, define_correct_answers, proccess_image

BASE_DIR = Path(__file__).resolve().parent.parent
imgs_path = os.path.join(BASE_DIR.__str__() + "/bot/imgs/")

file = cv.imread("test1.jpeg")

config = Test_Config(False, 3, 8, 3)

(answers_by_groups, answers_thresh, answers_transformed) = proccess_image(file, config)
#
#
# (transformed_correct, correct_answers) = define_correct_answers(
#     answers_by_groups, answers_thresh, answers_transformed, config
# )
#
# config.set_correct_answers(correct_answers)
#
# (
#     correct_answers_count,
#     partially_correct_answers_count,
#     wrong_answers_count,
#     checked_transformed,
# ) = check_answers(
#     answers_thresh,
#     answers_transformed,
#     answers_by_groups,
#     config,
# )

# cv.imshow("thresh", answers_thresh)
# cv.imshow("transformed", checked_transformed)
# cv.waitKey(0)
