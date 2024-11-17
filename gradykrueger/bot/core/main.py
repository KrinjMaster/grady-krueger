import time

import cv2 as cv
import helpers

# start = time.time()

# answers_image = cv.imread("test12 sample.jpg")
#
# assert answers_image is not None, "No image found!"

rows = 10
columns = 2
n = 3
is_multiple_answers = True

answers_image = cv.imread("test12 sample2.jpeg")

(answers_by_groups, answers_thresh, answers_transformed) = helpers.proccess_image(
    answers_image,
    rows,
    columns,
    n,
)

(transformed_correct, marked_correct_answers) = helpers.define_correct_answers(
    answers_by_groups,
    answers_thresh,
    answers_transformed,
    rows,
    columns,
    n,
)


cv.imshow("correct", transformed_correct)
cv.waitKey(0)
cv.destroyAllWindows()

# (answers_by_groups, answers_thresh, answers_transformed) = helpers.proccess_image(
#     answers_image, rows, columns, n
# )
#
# marked_correct_answers = helpers.define_correct_answers(
#     answers_by_groups, answers_thresh, answers_transformed, rows, columns, n
# )
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
