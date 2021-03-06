
import datetime
import config


from model import Mode
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from user_manager import UserManager

um = UserManager.get_instance()


def make_main_keyboard(chat_id):

    u = um.get_user(chat_id)

    buttonLists = list()
    for i in range(9):
        buttonLists.append(list())

    buttonLists[0].append(config.ALL_COURSES)
    buttonLists[3].append(config.ROOMS)

    buttonLists[5].append(config.MAKE_PLAN)

    if u.mode != Mode.NORMAL:
        if u.notification:
            buttonLists[4].append(config.NOTIFY_OFF)
        else:
            buttonLists[4].append(config.NOTIFY_ON)
        buttonLists[1].append(config.MY_TIMETABLE)
        buttonLists[2].append(config.MY_PLAN)
        buttonLists[6].append(config.DEL_PLAN)

    buttonLists[7].append(config.HELP)
    buttonLists[7].append(config.DONATION)
    buttonLists[8].append(config.PRIVACY)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_area_keyboard(all_courses_group_by_area, mode):
    buttonLists = list()

    for i in range(0, len(all_courses_group_by_area.keys()) + 2, 1):
        buttonLists.append(list())

    for i, key in enumerate(sorted(all_courses_group_by_area.keys())):
        buttonLists[i + 1].append(key)

    buttonLists[len(all_courses_group_by_area.keys()) +
                1].append(config.BACK_TO_MAIN)
    if mode == Mode.MAKE_PLAN:
        buttonLists[0].append(config.END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_courses_keyboard(all_courses_group_by_area, area, mode):
    buttonLists = list()

    for i in range(0, len(all_courses_group_by_area[area]) + 2, 1):
        buttonLists.append(list())

    for i in range(0, len(all_courses_group_by_area[area]), 1):
        c = all_courses_group_by_area[area][i]
        buttonLists[i + 1].append(c.corso_codice + " - " + c.corso_descrizione[:50] +
                                  " (" + c.sededidattica + ") - " + c.tipologia)

    buttonLists[len(all_courses_group_by_area[area]) +
                1].append(config.BACK_TO_AREAS)
    buttonLists[len(all_courses_group_by_area[area]) +
                1].append(config.BACK_TO_MAIN)
    if mode == Mode.MAKE_PLAN:
        buttonLists[0].append(config.END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_year_keyboard(all_courses, corso_codice, mode):
    buttonLists = list()
    c = all_courses[corso_codice]

    for i in range(0, c.durata + 2, 1):
        buttonLists.append(list())

    for i in range(0, c.durata, 1):
        buttonLists[i + 1].append(c.corso_codice + " - " + c.corso_descrizione[:50] +
                                  " (" + c.sededidattica + ")" + " - YEAR " + str(i+1))

    buttonLists[c.durata + 1].append(config.BACK_TO_AREAS)
    buttonLists[c.durata + 1].append(config.BACK_TO_MAIN)
    if mode == Mode.MAKE_PLAN:
        buttonLists[0].append(config.END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_inline_timetable_keyboard(day):
    next_day = day + datetime.timedelta(days=1)
    prec_day = day - datetime.timedelta(days=1)
    next_week = day + datetime.timedelta(days=7)
    prec_week = day - datetime.timedelta(days=7)
    # keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #     [InlineKeyboardButton(text=config.emo_arrow_back + " " + 'Back', callback_data=prec_day.strftime("%d/%m/%YT%H:%M:%S")),
    #      InlineKeyboardButton(text='Next ' + config.emo_arrow_forward,
    #                           callback_data=next_day.strftime("%d/%m/%YT%H:%M:%S"))],
    #     [InlineKeyboardButton(text=config.emo_double_arrow_back + " " + 'Previous week',
    #                           callback_data=prec_week.strftime(
    #                               "%d/%m/%YT%H:%M:%S")),
    #      InlineKeyboardButton(text='Next week ' + config.emo_double_arrow_forward,
    #                           callback_data=next_week.strftime(
    #                               "%d/%m/%YT%H:%M:%S"))]
    # ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=config.emo_double_arrow_back,
                              callback_data=prec_week.strftime("%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(
             text=config.emo_arrow_back, callback_data=prec_day.strftime("%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text="TODAY", callback_data="today"),
         InlineKeyboardButton(
             text=config.emo_arrow_forward, callback_data=next_day.strftime("%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text=config.emo_double_arrow_forward, callback_data=next_week.strftime("%d/%m/%YT%H:%M:%S"))]
    ])

    return keyboard


def make_inline_course_schedule_keyboard(chat_id, day, corso_codice, year):
    next_day = day + datetime.timedelta(days=1)
    prec_day = day - datetime.timedelta(days=1)
    next_week = day + datetime.timedelta(days=7)
    prec_week = day - datetime.timedelta(days=7)
    # keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #     [InlineKeyboardButton(text=config.emo_arrow_back + " " + 'Previous day',
    #                           callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + prec_day.strftime(
    #                               "%d/%m/%YT%H:%M:%S")),
    #      InlineKeyboardButton(text='Next day ' + config.emo_arrow_forward,
    #                           callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + next_day.strftime(
    #                               "%d/%m/%YT%H:%M:%S"))],
    #     [InlineKeyboardButton(text=config.emo_double_arrow_back + " " + 'Previous week',
    #                           callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + prec_week.strftime(
    #                               "%d/%m/%YT%H:%M:%S")),
    #         InlineKeyboardButton(text='Next week ' + config.emo_double_arrow_forward,
    #                              callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + next_week.strftime(
    #                                  "%d/%m/%YT%H:%M:%S"))]
    # ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=config.emo_double_arrow_back,
                              callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + prec_week.strftime(
                                  "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(
             text=config.emo_arrow_back,  callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + prec_day.strftime(
                 "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text="TODAY", callback_data="course_" +
                              corso_codice + "_year_"+str(year)+"_" + "today"),
         InlineKeyboardButton(
             text=config.emo_arrow_forward, callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + next_day.strftime(
                 "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text=config.emo_double_arrow_forward, callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + next_week.strftime(
             "%d/%m/%YT%H:%M:%S"))]
    ])

    return keyboard


def make_inline_room_schedule_keyboard(chat_id, day, aula_codice):

    next_day = day + datetime.timedelta(days=1)
    prec_day = day - datetime.timedelta(days=1)
    next_week = day + datetime.timedelta(days=7)
    prec_week = day - datetime.timedelta(days=7)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=config.emo_double_arrow_back,
                              callback_data="room " + aula_codice + " " + prec_week.strftime(
                                  "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(
             text=config.emo_arrow_back,  callback_data="room " + aula_codice + " " + prec_day.strftime(
                 "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text="TODAY", callback_data="room " +
                              aula_codice + " " + "today"),
         InlineKeyboardButton(
             text=config.emo_arrow_forward, callback_data="room " + aula_codice + " " + next_day.strftime(
                 "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text=config.emo_double_arrow_forward, callback_data="room " + aula_codice + " " + next_week.strftime(
             "%d/%m/%YT%H:%M:%S"))]
    ])

    return keyboard


def make_room_keyboard(chat_id):
    empty_rooms_button = KeyboardButton(
        text=config.EMPTY_ROOMS)
    all_rooms_button = KeyboardButton(
        text=config.ALL_ROOMS)
    back_button = KeyboardButton(text=config.BACK_TO_MAIN)

    custom_keyboard = [[all_rooms_button], [empty_rooms_button], [back_button]]

    keyboard = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

    return keyboard


def make_location_room_keyboard(chat_id):
    location_button = KeyboardButton(
        text=config.SEND_LOCATION, request_location=True)

    back_button = KeyboardButton(text=config.BACK_TO_MAIN)

    custom_keyboard = [[location_button], [back_button]]

    keyboard = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

    return keyboard


def make_inline_see_room_schedule_keyboard(chat_id, aula_nome, aula_codice):

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=config.emo_tap + " SEE ROOM SCHEDULE for " + aula_nome, callback_data="room " +
                              aula_codice + " " + "today")]
    ])

    return keyboard
