import os

import cv2 as cv
import numpy as np
from cv2.typing import MatLike
from django.conf import settings
from imutils import perspective
from PIL import Image, ImageDraw, ImageFont

font_path = os.path.join(settings.BASE_DIR.__str__() + "/bot/fonts/Arial Unicode.ttf")


# func to proccess image and return all of the answers circle countors and transformed image of test sheet
def proccess_image(image, rows, columns, n) -> tuple[list[int], MatLike, MatLike]:
    # basic image manipulation
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, (5, 5), 0)
    edged = cv.Canny(blurred, 5, 100)

    # countors
    cnts, _ = cv.findContours(edged.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cv.drawContours(edged, cnts, -1, (255, 255, 255), 3)
    cnts, _ = cv.findContours(edged.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    countor = None
    max_perimeter = 0

    # determining countor of a sheet of paper
    for c in cnts:
        perimeter = cv.arcLength(c, True)
        approx = cv.approxPolyDP(c, 0.04 * perimeter, True)

        if len(approx) == 4 and max_perimeter < perimeter:
            max_perimeter = perimeter
            countor = approx

    assert countor is not None, "No paper found!"

    # four point transformation
    transformed = perspective.four_point_transform(image, countor.reshape(4, 2))
    transformed_gray = cv.cvtColor(transformed, cv.COLOR_BGR2GRAY)
    transformed_blurred = cv.GaussianBlur(transformed_gray, (9, 5), 0)

    # to black and white
    threshold = np.average(transformed_blurred)

    _, thresh = cv.threshold(transformed_blurred, threshold, 255, cv.THRESH_BINARY)

    # contors again
    paper_cnts, paper_hier = cv.findContours(
        thresh.copy(), cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE
    )

    filtered_cnts = []

    threshold = 0
    most_occuring_count = 0

    occurence_frequency = {}

    # get the most occuring outer contor
    for i in range(len(paper_hier)):
        if occurence_frequency.get(paper_hier[:, i][0][3]) is not None:
            occurence_frequency[paper_hier[:, i][0][3]] += 1
        else:
            occurence_frequency[paper_hier[:, i][0][3]] = 0

        if occurence_frequency[paper_hier[:, i][0][3]] > most_occuring_count:
            threshold = paper_hier[:, i][0][3]
            most_occuring_count = occurence_frequency[paper_hier[:, i][0][3]]

    # get all of the outer contors
    for index in range(len(paper_cnts)):
        if paper_hier[:, index][0][3] > threshold - 1:
            filtered_cnts.append(paper_cnts[index])

    # define answer question radius
    row_spacing = 10
    columns_spacing = max(210 / columns, 35)
    circle_spacing = 25

    width = (2337 - columns_spacing * columns) // columns
    height = (3107 - rows * row_spacing) // rows

    font_nums = ImageFont.truetype(font_path, max(height / (columns + 1), 50))

    pil_img = Image.fromarray(transformed)

    draw = ImageDraw.Draw(pil_img)

    length = draw.textlength(
        str(columns * rows),
        font=font_nums,
    )

    circle_radius = (width - (length + circle_spacing * (n - 1))) / (2 * n)

    if 2 * circle_radius > height:
        circle_radius = height / 2

    question_cnts = []

    # filter to keep only the answer circles contors
    for i in range(len(filtered_cnts)):
        c = filtered_cnts[i]
        M = cv.moments(c)
        (_, _, w, h) = cv.boundingRect(c)
        ar = w / float(h)

        if (
            w >= circle_radius / 2
            and h >= circle_radius / 2
            and ar >= 0.9
            and ar <= 1.1
            and M["m00"] != 0
        ):
            question_cnts.append(c)

    # sort answer circles from top-to-bottom left-to-right
    question_cnts = sorted(
        question_cnts,
        key=lambda ctr: cv.boundingRect(ctr)[0] * 450
        + cv.boundingRect(ctr)[1] * image.shape[1],
    )

    assert rows * columns * n == len(question_cnts), "Wrong number of questions found!"

    # iterate and group circle contors by questions
    answers_by_groups = []

    cur_row = 0
    factor = 0
    cur_n = 0
    cur_group = []

    for i in range(len(question_cnts) + 1):
        if cur_row <= rows - 1:
            cur_group.append(question_cnts[columns * n * cur_row + cur_n + factor * 3])

            if cur_n + 1 == 3:
                answers_by_groups.append(cur_group)
                cur_group = []
                cur_n = 0
                cur_row += 1
            else:
                cur_n += 1

        else:
            cur_n = 0
            cur_row = 0
            factor += 1

    return (answers_by_groups, thresh, transformed)


# defines correct answer for the test
def define_correct_answers(
    answers_by_groups, thresh, transformed, rows, columns, n
) -> tuple[MatLike, list[int]]:
    correct_answers = []

    # iterate over contours, check if content inside is filled or not (black and white ratio)
    for group_i in range(rows * columns):
        marked_answer = 0

        for cnt_i in range(n):
            x, y, w, h = cv.boundingRect(answers_by_groups[group_i][cnt_i])
            ROI = thresh[y : y + h, x : x + w]
            bw_ratio = np.sum(ROI == 255) / np.sum(ROI == 0)

            if bw_ratio < 2.25:
                # circle is marked
                marked_answer |= 1 << (n - 1 - cnt_i)

                cv.drawContours(
                    transformed,
                    [answers_by_groups[group_i][cnt_i]],
                    -1,
                    (0, 255, 0),
                    5,
                )

        correct_answers.append(marked_answer)

    return (transformed, correct_answers)


# check the test occording to given answers
def check_answers(
    thresh,
    transformed,
    answers_by_groups,
    correct_answers,
    rows,
    columns,
    n,
    is_multiple_answers,
) -> tuple[int, int, int, MatLike]:
    correct_answers_count = 0
    partially_correct_answers_count = 0
    wrong_answers_count = 0

    # this loop only for drawing correct, incorrect and partially correct answers contors
    for group_i in range(rows * columns):
        marked_answer = 0

        for cnt_i in range(n):
            x, y, w, h = cv.boundingRect(answers_by_groups[group_i][cnt_i])
            ROI = thresh[y : y + h, x : x + w]
            bw_ratio = np.sum(ROI == 255) / np.sum(ROI == 0)

            if bw_ratio < 2.1:
                # circle is marked
                marked_answer |= 1 << (n - 1 - cnt_i)

                if 1 << (n - 1 - cnt_i) & correct_answers[group_i] != 0:
                    # circle is marked correctly
                    cv.drawContours(
                        transformed,
                        [answers_by_groups[group_i][cnt_i]],
                        -1,
                        (0, 255, 0),
                        5,
                    )
                else:
                    # circle is marked incorrectly
                    cv.drawContours(
                        transformed,
                        [answers_by_groups[group_i][cnt_i]],
                        -1,
                        (0, 0, 255),
                        5,
                    )
            elif 1 << (n - 1 - cnt_i) & correct_answers[group_i] != 0:
                # circle is not marked, but correct
                cv.drawContours(
                    transformed, [answers_by_groups[group_i][cnt_i]], -1, (255, 0, 0), 5
                )

            # on last contor in the group check answered circles
            if cnt_i == n - 1:
                if correct_answers[group_i] & marked_answer != 0 and marked_answer != 0:
                    if (
                        correct_answers[group_i] & marked_answer
                        == correct_answers[group_i]
                        and marked_answer.bit_count()
                        == correct_answers[group_i].bit_count()
                    ):
                        # all answers are correct
                        correct_answers_count += 1
                    elif (
                        (
                            (correct_answers[group_i] & marked_answer)
                            ^ correct_answers[group_i]
                        ).bit_count()
                        == 1
                        or (
                            (correct_answers[group_i] & marked_answer) ^ marked_answer
                        ).bit_count()
                        == 1
                    ) and (
                        correct_answers[group_i].bit_count() > 1 and is_multiple_answers
                    ):
                        # only one answer is missing, if only multiple answers are possible and there is more than one correct answer
                        partially_correct_answers_count += 1
                    else:
                        wrong_answers_count += 1
                else:
                    wrong_answers_count += 1

    # drawing results on the sheet of paper
    font = cv.FONT_ITALIC

    (x, y, w, h) = cv.boundingRect(thresh)

    pil_img = Image.fromarray(transformed)

    font = ImageFont.truetype(font_path, 45)
    draw = ImageDraw.Draw(pil_img)

    draw.text((50, h - 220), "Правильные: " + str(correct_answers_count), font=font)
    draw.text(
        (50, h - 160),
        "Частично правильные: " + str(partially_correct_answers_count),
        font=font,
    )
    draw.text((50, h - 100), "Неправильные: " + str(wrong_answers_count), font=font)
    draw.text(
        (750, h - 160),
        "Результат: "
        + str(correct_answers_count + 0.5 * partially_correct_answers_count)
        + "/"
        + str(columns * rows),
        font=font,
    )

    draw.text((w - 350, h - 220), "Правильные", fill=(0, 255, 0), font=font)
    draw.text(
        (w - 350, h - 160),
        "Пропущенные",
        fill=(255, 0, 0),
        font=font,
    )
    draw.text((w - 350, h - 100), "Неправильныe", fill=(0, 0, 255), font=font)

    transformed = np.asarray(pil_img)

    return (
        correct_answers_count,
        partially_correct_answers_count,
        wrong_answers_count,
        transformed,
    )


def create_test_template(columns, rows, n):
    # create russian alphabet
    a = ord("а")
    alphabet = (
        [chr(i).upper() for i in range(a, a + 6)]
        + [chr(a + 33).upper()]
        + [chr(i).upper() for i in range(a + 6, a + 32)]
    )

    # equal to A4 piece of paper
    result = np.zeros([3507, 2481, 3], dtype=np.uint8)

    # underlining next to name and class text
    result.fill(255)
    result[200:205, 350:1500] = 0
    result[200:205, 1850:2100] = 0

    # frame
    cv.rectangle(result, (35, 35), (2446, 3472), 0, 20)

    # placing circles and answer number
    row_spacing = 20
    columns_spacing = max(210 / columns, 35)
    circle_spacing = 25

    offset_x = 90
    offset_y = 300

    width = (2337 - columns_spacing * columns) // columns
    height = (3107 - rows * row_spacing) // rows

    font = ImageFont.truetype(font_path, 80)
    font_nums = ImageFont.truetype(font_path, max(height / (columns + 1), 50))

    pil_img = Image.fromarray(result)

    draw = ImageDraw.Draw(pil_img)

    length = draw.textlength(
        str(columns * rows),
        font=font_nums,
    )
    circle_radius = (width - (length + circle_spacing * (n - 1))) / (2 * n)

    if 2 * circle_radius > height:
        circle_radius = height / 2

    font_circle_letters = ImageFont.truetype(font_path, circle_radius)

    for col_count in range(columns):
        for row_count in range(rows):
            for i in range(n):
                draw.circle(
                    (
                        offset_x
                        + length
                        + width * col_count
                        + columns_spacing * col_count
                        + circle_radius * ((i + 1) * 2 - 1)
                        + circle_spacing * i,
                        offset_y
                        + height * row_count
                        + row_spacing * row_count
                        + height / 2,
                    ),
                    int(circle_radius),
                    outline=(0),
                    width=int(circle_radius * 0.10),
                )

                draw.text(
                    (
                        offset_x
                        + length
                        + width * col_count
                        + columns_spacing * col_count
                        + circle_radius * ((i + 1) * 2 - 1)
                        + circle_spacing * i,
                        offset_y
                        + height * row_count
                        + row_spacing * row_count
                        + height / 2,
                    ),
                    alphabet[i],
                    fill=(0),
                    anchor="mm",
                    font=font_circle_letters,
                )

            draw.text(
                (
                    offset_x
                    + width * col_count
                    + columns_spacing * col_count
                    + row_spacing,
                    offset_y
                    + height * row_count
                    + row_spacing * row_count
                    + height / 2,
                ),
                str(col_count * rows + row_count + 1),
                fill=(0),
                anchor="mm",
                font=font_nums,
            )

    draw.text((100, 100), "Ф.И.О:", fill=(0), font=font)
    draw.text((1600, 100), "Класс:", fill=(0), font=font)

    result = np.asarray(pil_img)

    return result
