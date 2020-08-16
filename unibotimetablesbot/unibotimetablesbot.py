import os
import collections
import random
import sys
import traceback
import datetime
import schedule
import logging
import wget
import json
import requests
import time
import csv
import threading


from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, Handler
from telegram import ParseMode, KeyboardButton, ReplyKeyboardMarkup

from model import Course, Teaching, Mode, Plan, Lesson, Aula, Timetable, User
from keyboards import make_area_keyboard, make_room_keyboard, make_location_room_keyboard, make_inline_see_room_schedule_keyboard, make_courses_keyboard, make_inline_room_schedule_keyboard, make_inline_timetable_keyboard, make_inline_course_schedule_keyboard, make_main_keyboard, make_year_keyboard
from plan_manager import get_lessons, get_plan_timetable, get_room_timetable, load_user_plan, print_output_timetable, print_plan, print_plan_message, print_teachings_message, store_user_plan, check_plans_consistency

from user_manager import UserManager
from db_query import check_table, download_csv_orari,get_all_orari, get_all_orari_from_file, get_all_aule, get_all_courses
from utils import my_round, distance

import config

all_courses = dict()
all_aule = dict()
all_teachings = dict()
all_courses_group_by_area = collections.defaultdict(list)
orari_group_by_aula = collections.defaultdict(list)
orari = collections.defaultdict(list)

um = UserManager.get_instance()


def callback_query(update, context):

    text = update.callback_query.message.text
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    query_data = update.callback_query.data
    print(query_data)
    try:

        if query_data.startswith("course_"):

            array = query_data.split("_")
            corso_codice = array[1]
            year = int(array[3])
            if query_data.endswith("today"):
                day = datetime.datetime.now()
            else:
                day_string = array[len(array) - 1]
                day = datetime.datetime.strptime(
                    day_string, "%d/%m/%YT%H:%M:%S")

            course = all_courses[corso_codice]
            plan = Plan()
            for t in course.teachings:
                if t.anno == None or int(t.anno) == year:
                    plan.add_teaching(t)

            timetable = get_plan_timetable(day, plan, orari, all_aule)

            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + \
                "/" + str(int(config.accademic_year) + 1) + "</code>\n"
            output_string += config.emo_calendar + " " + \
                day.strftime("%A %B %d, %Y") + "\n\n"

            output_string += config.emo_pin+" <b>"+str(course)+"</b>\n\n"

            output_string += config.emo_timetable + " <b>TIMETABLE</b>\n\n"

            output_string += print_output_timetable(timetable)

            try:
                update.callback_query.edit_message_text(output_string, parse_mode=ParseMode.HTML,
                                                        reply_markup=make_inline_course_schedule_keyboard(chat_id, day, course.corso_codice, year))
            except:
                traceback.print_exc()
                update.callback_query.answer(text="SLOW DOWN!!")
                pass
        elif query_data.startswith("room "):

            array = query_data.split(" ")
            aula_codice = array[1]

            if query_data.endswith("today"):
                day = datetime.datetime.now()
            else:
                day_string = array[len(array) - 1]
                day = datetime.datetime.strptime(
                    day_string, "%d/%m/%YT%H:%M:%S")

            room = all_aule[aula_codice]

            timetable = get_room_timetable(
                day, room, orari_group_by_aula, all_teachings)

            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                int(config.accademic_year) + 1) + "</code>\n"
            output_string += config.emo_calendar + " " + \
                day.strftime("%A %B %d, %Y") + "\n\n"

            output_string += config.emo_room + " <b>" + room.aula_nome+"</b>" + "\n\n"

            output_string += print_output_timetable(timetable)
            try:
                update.callback_query.edit_message_text(output_string, parse_mode=ParseMode.HTML,
                                                        reply_markup=make_inline_room_schedule_keyboard(chat_id, day, aula_codice))
            except:
                update.callback_query.answer(text="SLOW DOWN!!")
                traceback.print_exc()
                pass

        else:
            if query_data.endswith("today"):
                day = datetime.datetime.now()
            else:
                day = datetime.datetime.strptime(
                    query_data, "%d/%m/%YT%H:%M:%S")

            plan = load_user_plan(chat_id, all_teachings)

            if plan != None:

                timetable = get_plan_timetable(day, plan, orari, all_aule)

                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + \
                    "/" + str(int(config.accademic_year) + 1) + "</code>\n"
                output_string += config.emo_calendar + " " + \
                    day.strftime("%A %B %d, %Y") + "\n\n"
                output_string += config.emo_timetable + " <b>YOUR TIMETABLE</b>\n\n"

                output_string += print_output_timetable(timetable)
                try:
                    update.callback_query.edit_message_text(
                        output_string, parse_mode=ParseMode.HTML, reply_markup=make_inline_timetable_keyboard(day))
                except:
                    update.callback_query.answer(text="SLOW DOWN!!")
                    traceback.print_exc()

    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime(
            "%b %d %Y %H:%M:%S") + " ### EXCEPTION from " + str(chat_id)+" = " + traceback.format_exc())


def start(update, context):

    chat_id = update.message.chat_id
    text = update.message.text
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text)

    um.get_user(chat_id).mode = Mode.NORMAL

    um.store_user(chat_id)

    output_string = "Hi! Thanks for trying this bot!\n\n" + config.help_string

    update.message.reply_html(
        output_string, reply_markup=make_main_keyboard(chat_id))


def help(update, context):

    chat_id = update.message.chat_id
    text = update.message.text
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text)

    output_string = config.help_string

    update.message.reply_html(
        output_string, reply_markup=make_main_keyboard(chat_id))


def print_time(update, context):

    chat_id = update.message.chat_id
    text = update.message.text
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text)

    output_string = now.strftime(
        config.emo_calendar+" %A %B %d, %Y " + config.emo_clock+" %H:%M:%S")

    update.message.reply_html(
        output_string, reply_markup=make_main_keyboard(chat_id))


def add(update, context):
    chat_id = update.message.chat_id
    text = update.message.text

    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text)

    if um.get_user(chat_id).mode == Mode.MAKE_PLAN:
        array = text.split("_")
        componente_id = array[1]
        output_string = ""
        if componente_id in all_teachings.keys():
            plan = load_user_plan(chat_id, all_teachings)

            teaching = all_teachings[componente_id]

            for t in all_teachings.values():
                if t.componente_radice == teaching.componente_radice:
                    state = plan.add_teaching(t)
                    if state:
                        output_string += "ADDED " + "<b>"+t.materia_descrizione+"</b>\n"
                    else:
                        output_string += "<b>"+t.materia_descrizione + \
                            "</b> ALREADY IN YOUR STUDY PLAN\n"

            # state = plan.add_teaching(teaching)

            # if state:
            #     output_string += "ADDED " + "<b>"+teaching.materia_descrizione+"</b>\n"
            # else:
            #     output_string += "<b>"+teaching.materia_descrizione + \
            #         "</b> ALREADY IN YOUR STUDY PLAN\n"

            # while teaching.componente_padre != None and teaching.componente_padre != "":
            #     teaching = all_teachings[teaching.componente_padre]
            #     state = plan.add_teaching(teaching)

            #     if state:
            #         output_string += "ADDED " + "<b>"+teaching.materia_descrizione+"</b>\n"
            #     else:
            #         output_string += "<b>"+teaching.materia_descrizione + \
            #             "</b> ALREADY IN YOUR STUDY PLAN\n"

            # comp_padri = [componente_id]

            # while comp_padri:
            #     comp_padre = comp_padri.pop()

            #     for key in all_teachings.keys():
            #         t = all_teachings[key]
            #         if t.componente_padre == comp_padre:

            #             comp_padri.append(t.componente_id)
            #             state = plan.add_teaching(t)

            #             if state:
            #                 output_string += "ADDED " + "<b>"+t.materia_descrizione + "</b>\n"
            #             else:
            #                 output_string += "<b>"+t.materia_descrizione + \
            #                     "</b> ALREADY IN YOUR STUDY PLAN\n"

            store_user_plan(chat_id, plan)

            update.message.reply_html(
                output_string, disable_notification=True)


def remove(update, context):
    chat_id = update.message.chat_id
    text = update.message.text

    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text)

    array = text.split("_")
    componente_id = array[1]

    teaching = all_teachings[componente_id]

    plan = load_user_plan(chat_id, all_teachings)

    state = plan.remove_teaching(teaching)
    store_user_plan(chat_id, plan)

    if state:
        output_string = "REMOVED " + "<b>"+teaching.materia_descrizione+"</b>"
    else:
        output_string = "<b>"+teaching.materia_descrizione + "</b> NOT IN YOUR STUDY PLAN"

    update.message.reply_html(output_string, disable_notification=True)


def set_notify_time(update, context):
    chat_id = update.message.chat_id
    text = update.message.text

    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text)

    try:
        u = um.get_user(chat_id)
        u.notification_time = my_round(int(text.split()[1]))

        um.store_user(chat_id)
        output_string = "Great job! Now you should receive notifications " + \
            str(u.notification_time)+" minutes before each lesson!"

    except:
        traceback.print_exc()
        output_string = config.command_help_string

    update.message.reply_html(
        output_string, reply_markup=make_main_keyboard(chat_id))


def room_schedule(update, context):
    chat_id = update.message.chat_id
    text = update.message.text

    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text)

    array = text.split("_")
    aula_codice = "_".join(array[3:])
    room = all_aule[aula_codice]

    timetable = get_room_timetable(
        now, room, orari_group_by_aula, all_teachings)

    output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
        int(config.accademic_year) + 1) + "</code>\n"
    output_string += config.emo_calendar + " " + \
        now.strftime("%A %B %d, %Y") + "\n\n"

    output_string += config.emo_room + " <b>" + room.aula_nome+"</b>" + "\n\n"

    output_string += print_output_timetable(timetable)

    update.message.reply_html(
        output_string, reply_markup=make_inline_room_schedule_keyboard(chat_id, now, aula_codice))


def url(update, context):
    chat_id = update.message.chat_id
    text = update.message.text

    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text)

    array = text.split("_")
    componente_id = array[1]

    if componente_id in all_teachings.keys():
        output_string = config.emo_url + " " + \
            all_teachings[componente_id].url

        update.message.reply_html(
            output_string, disable_web_page_preview=True)


def commands(update, context):
    try:

        text = update.message.text
        chat_id = update.message.chat_id
        if text.startswith("/add_"):
            add(update, context)
        elif text.startswith("/remove_"):
            remove(update, context)
        elif text.startswith("/url_"):
            url(update, context)
        elif text.startswith("/see_room_schedule_"):
            room_schedule(update, context)
        elif text.startswith(config.SET_NOT_TIME_CMD):
            set_notify_time(update, context)

    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### EXCEPTION from " + str(chat_id)+" = " + traceback.format_exc())
        output_string = config.emo_wrong + " Oh no! Something bad happend.."
        update.message.reply_html(output_string,
                                  reply_markup=make_main_keyboard(chat_id))


def error(update, context):
    now = datetime.datetime.now()
    logging.error("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                  " ### MESSAGE " + " = " + str(update.message) + "### ERROR = " + str(context.error))


def message(update, context):
    try:
        chat_id = update.message.chat_id
        text = update.message.text

        u = um.get_user(chat_id)

        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### MESSAGE from " + str(chat_id)+" = " + text)
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
              " ### MESSAGE from " + str(chat_id) + " = " + text)

        if chat_id not in um.get_all_users().keys():
            um.check_user(chat_id)
            um.store_user(chat_id)

            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                int(config.accademic_year) + 1) + "</code>\n"
            output_string += "Choose your action!"

            update.message.reply_html(
                output_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.ALL_COURSES:
            u = um.get_user(chat_id)

            um.store_user(chat_id)

            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                int(config.accademic_year) + 1) + "</code>\n"
            output_string += "Choose your area!"

            update.message.reply_html(output_string, reply_markup=make_area_keyboard(
                all_courses_group_by_area, u.mode))

        elif text == config.MY_TIMETABLE:
            um.get_user(chat_id).mode = Mode.PLAN
            um.store_user(chat_id)

            now = datetime.datetime.now()

            ##### DEBUG #####
            #  now = datetime.datetime.strptime("29/05/2019", "%d/%m/%Y")
            #################
            plan = load_user_plan(chat_id, all_teachings)

            if plan != None:

                timetable = get_plan_timetable(now, plan, orari, all_aule)
                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                    int(config.accademic_year) + 1) + "</code>\n"
                output_string += config.emo_calendar + " " + \
                    now.strftime("%A %B %d, %Y") + "\n\n"

                output_string += config.emo_timetable + " <b>YOUR TIMETABLE</b>" + "\n\n"

                output_string += print_output_timetable(timetable)

                update.message.reply_html(
                    output_string, reply_markup=make_inline_timetable_keyboard(now))

            else:
                output_string = "You haven't a study plan yet! Use " + \
                    config.MAKE_PLAN + " to make it"
                um.get_user(chat_id).mode = Mode.NORMAL
                um.store_user(chat_id)
                update.message.reply_html(
                    output_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.MY_PLAN:
            um.get_user(chat_id).mode = Mode.PLAN
            um.store_user(chat_id)

            plan = load_user_plan(chat_id, all_teachings)
            if plan != None:
                string_list = print_plan_message(chat_id, plan)

                i = 0
                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                    int(config.accademic_year) + 1) + "</code>\n\n"
                output_string += config.emo_plan + " <b>YOUR STUDY PLAN</b>" + "\n\n"

                for s in string_list:
                    output_string += s
                    i += 1
                    if i % 20 == 0:
                        update.message.reply_html(
                            output_string, reply_markup=make_main_keyboard(chat_id))
                        output_string = ""
                if output_string != "":
                    update.message.reply_html(
                        output_string, reply_markup=make_main_keyboard(chat_id))
            else:
                output_string = "You haven't a study plan yet! Use " + \
                    config.MAKE_PLAN + " to make it"
                um.get_user(chat_id).mode = Mode.NORMAL
                um.store_user(chat_id)
                update.message.reply_html(
                    output_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.DEL_PLAN:

            um.get_user(chat_id).mode = Mode.DEL

            output_string = "Are you sure? Send \"<b>YES</b>\" to confirm or \"<b>NO</b>\" to cancel (without quotes)"
            update.message.reply_html(output_string)

        elif text.upper() == "YES" and um.get_user(chat_id).mode == Mode.DEL:

            um.get_user(chat_id).mode = Mode.NORMAL
            um.store_user(chat_id)

            if os.path.isfile(config.dir_plans_name + str(chat_id)):
                os.remove(config.dir_plans_name + str(chat_id))

            output_string = "Your study plan was deleted!"
            update.message.reply_html(
                output_string, reply_markup=make_main_keyboard(chat_id))

        elif text == "NO" and um.get_user(chat_id).mode == Mode.DEL:
            um.get_user(chat_id).mode = Mode.PLAN
            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                int(config.accademic_year) + 1) + "</code>\n"
            output_string += "Choose your action!"
            update.message.reply_html(
                output_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.MAKE_PLAN:
            u = um.get_user(chat_id)
            u.mode = Mode.MAKE_PLAN
            um.store_user(chat_id)

            if not os.path.isfile(config.dir_plans_name + str(chat_id)):
                plan = Plan()
                store_user_plan(chat_id, plan)

            output_string = "Find your subjects and add them to your study plan. Send " + \
                config.END_PLAN + " when you have finished!"
            update.message.reply_html(output_string, reply_markup=make_area_keyboard(
                all_courses_group_by_area, u.mode))

        elif text == config.END_PLAN:
            u = um.get_user(chat_id)
            u.mode = Mode.PLAN
            um.store_user(chat_id)
            plan = load_user_plan(chat_id, all_teachings)
            store_user_plan(chat_id, plan)

            output_string = "Well done! Now you can use " + config.MY_PLAN + \
                " to see your study plan and " + config.MY_TIMETABLE + \
                " to get your lessons shedules!"
            update.message.reply_html(
                output_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.BACK_TO_MAIN:
            um.check_user(chat_id)
            um.store_user(chat_id)

            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                int(config.accademic_year) + 1) + "</code>\n"
            output_string += "Choose your action!"

            update.message.reply_html(
                output_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.BACK_TO_AREAS:
            u = um.get_user(chat_id)
            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                int(config.accademic_year) + 1) + "</code>\n"
            output_string += "Choose your area!"

            update.message.reply_html(output_string,
                                      reply_markup=make_area_keyboard(all_courses_group_by_area, u.mode))

        elif text == config.NOTIFY_ON:
            u = um.get_user(chat_id)

            if os.path.isfile(config.dir_plans_name + str(chat_id)):
                u.notification = True
                um.store_user(chat_id)

                output_string = "Notifications enabled!"

                update.message.reply_html(
                    output_string, reply_markup=make_main_keyboard(chat_id))
            else:
                output_string = "You haven't a study plan yet! Use " + \
                    config.MAKE_PLAN + " to make it"
                um.get_user(chat_id).mode = Mode.NORMAL
                um.store_user(chat_id)
                update.message.reply_html(
                    output_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.NOTIFY_OFF:
            u = um.get_user(chat_id)

            if u.notification:
                u.notification = False
                um.store_user(chat_id)

                output_string = "Notifications disabled!"

                update.message.reply_html(
                    output_string, reply_markup=make_main_keyboard(chat_id))
            else:
                output_string = "Notifications already disabled!"

                update.message.reply_html(
                    output_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.ROOMS:
            u = um.get_user(chat_id)

            output_string = config.location_string

            keyboard = make_room_keyboard(chat_id)
            update.message.reply_html(output_string, reply_markup=keyboard)

        elif text == config.ALL_ROOMS or text == config.EMPTY_ROOMS:
            u = um.get_user(chat_id)

            output_string = text

            keyboard = make_location_room_keyboard(chat_id)
            update.message.reply_html(output_string, reply_markup=keyboard)

        elif text == config.DONATION:
            um.check_user(chat_id)
            um.store_user(chat_id)

            update.message.reply_html(
                config.donation_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.HELP:

            um.check_user(chat_id)
            um.store_user(chat_id)

            update.message.reply_html(
                config.help_string, reply_markup=make_main_keyboard(chat_id))

        elif text == config.PRIVACY:
            um.check_user(chat_id)
            um.store_user(chat_id)

            update.message.reply_html(
                config.privacy_string, reply_markup=make_main_keyboard(chat_id))

        elif text in all_courses_group_by_area.keys():
            u = um.get_user(chat_id)

            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                int(config.accademic_year) + 1) + "</code>\n"
            output_string += "Choose your course!"

            update.message.reply_html(output_string, reply_markup=make_courses_keyboard(
                all_courses_group_by_area, text, u.mode))

        elif text.split()[0] in all_courses.keys():
            course = all_courses[text.split()[0]]
            u = um.get_user(chat_id)
            try:

                year = int(text.split()[-1])
                if u.mode == Mode.MAKE_PLAN:

                    string_list = print_teachings_message(
                        chat_id, all_courses, course.corso_codice, year)

                    i = 0

                    output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                        int(config.accademic_year) + 1) + "</code>\n\n"
                    output_string += config.emo_pin + \
                        " <b>"+str(course)+"</b>\n\n"
                    output_string += config.emo_plan + " <b>SUBJECTS " + \
                        str(year) + " YEAR</b> (sorted by name)\n\n"
                    for s in string_list:
                        output_string += s
                        i += 1
                        if i % 20 == 0:
                            update.message.reply_html(output_string)
                            output_string = ""
                    if output_string != "":
                        update.message.reply_html(output_string)

                elif u.mode == Mode.NORMAL or u.mode == Mode.PLAN:

                    plan = Plan()
                    for t in course.teachings:
                        if t.anno == None or t.anno == "" or int(t.anno) == year:
                            plan.add_teaching(t)

                    now = datetime.datetime.now()

                    timetable = get_plan_timetable(
                        now, plan, orari, all_aule)

                    output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                        int(config.accademic_year) + 1) + "</code>\n"

                    output_string += config.emo_calendar + " " + \
                        now.strftime("%A %B %d, %Y") + "\n\n"

                    output_string += config.emo_pin + \
                        " <b>"+str(course)+"</b>\n\n"

                    output_string += config.emo_timetable + " <b>TIMETABLE</b>\n\n"

                    output_string += print_output_timetable(timetable)

                    update.message.reply_html(output_string, reply_markup=make_inline_course_schedule_keyboard(
                        chat_id, now, course.corso_codice, year))

                else:
                    um.check_user(chat_id)
                    um.store_user(chat_id)

            except ValueError:

                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + \
                    "/" + str(int(config.accademic_year) + 1) + \
                    "</code>\n\n"
                output_string += "<b>SELECTED COURSE:\n" + \
                    config.emo_pin+" " + str(course)+"</b>"

                if course.url != "":
                    output_string += "\n" + config.emo_url + " " + course.url

                output_string += "\n\nChoose your year!"

                update.message.reply_html(output_string, disable_web_page_preview=True,
                                          reply_markup=make_year_keyboard(all_courses, course.corso_codice, um.get_user(chat_id).mode))

        else:
            um.check_user(chat_id)
            um.store_user(chat_id)

            output_string = config.emo_confused + " Sorry.. I don't understand.."
            output_string += "\n\n" + config.help_string

            update.message.reply_html(
                output_string, reply_markup=make_main_keyboard(chat_id))

    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### EXCEPTION from " + str(chat_id)+" = " + traceback.format_exc())
        output_string = config.emo_wrong + " Oh no! Something bad happend.."
        update.message.reply_html(output_string,
                                  reply_markup=make_main_keyboard(chat_id))


def location(update, context):
    try:

        chat_id = update.message.chat_id
        location = update.message.location
        now = datetime.datetime.now()

        text = None
        if update.message.reply_to_message != None:
            text = update.message.reply_to_message.text

        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### LOCATION from " + str(chat_id)+" = " + str(location.latitude) + ", " + str(location.longitude))
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
              " ### LOCATION from " + str(chat_id) + " = " + str(location.latitude) + ", " + str(location.longitude))

        if text != None and text == config.ALL_ROOMS:

            ##### DEBUG #####
            # now = datetime.datetime.strptime("2019-10-28T10:45:50", "%Y-%m-%dT%H:%M:%S")
            #################

            near_classrooms = []

            for key in all_aule.keys():
                a = all_aule[key]

                try:
                    if a.lat != None and a.lon != None:
                        lat = float(a.lat)
                        lon = float(a.lon)
                        if distance(location.latitude, location.longitude, lat, lon) <= 500:
                            near_classrooms.append(a)

                except:
                    traceback.print_exc()

            output_string = config.emo_room+" <b>ALL CLASSROOMS NEAR YOU</b>\n"

            update.message.reply_html(output_string)
            output_string = ""
            near_classrooms.sort(key=lambda x: x.aula_nome, reverse=False)

            # string_list = []

            # for a in empty_room:

            #     for m in (60, 30, 15):

            #         day = now + datetime.timedelta(minutes=m)
            #         free = a.is_empty(day, orari_group_by_aula)
            #         if free and m == 60:
            #             string_list.append(config.emo_blue_circle + " " +
            #                                str(a)+"\n/see_room_schedule_"+a.aula_codice+"\n\n")
            #             break
            #         elif free and m == 30:
            #             string_list.append(config.emo_yellow_square + " " +
            #                                str(a)+"\n/see_room_schedule_"+a.aula_codice+"\n\n")
            #             break
            #         elif free and m == 15:
            #             string_list.append(config.emo_red_circle + " " +
            #                                str(a)+"\n/see_room_schedule_"+a.aula_codice+"\n\n")
            #             break
            #     else:
            #         string_list.append(config.emo_black_circle + " " +
            #                            str(a)+"\n/see_room_schedule_"+a.aula_codice+"\n\n")

            # i = 0
            # for s in string_list:
            #     output_string += s
            #     i += 1
            #     if i % 20 == 0:
            #         update.message.reply_html(output_string)
            #         output_string = ""
            # if output_string != "":
            #     update.message.reply_html(output_string)

            for a in near_classrooms:

                output_string = config.emo_room + " " + str(a)
                update.message.reply_html(output_string, reply_markup=make_inline_see_room_schedule_keyboard(
                    chat_id, a.aula_nome, a.aula_codice))

        else:

            ##### DEBUG #####
            # now = datetime.datetime.strptime("2019-10-28T10:45:50", "%Y-%m-%dT%H:%M:%S")
            #################

            near_classrooms = []

            for key in all_aule.keys():
                a = all_aule[key]

                try:
                    if a.lat != None and a.lon != None:
                        lat = float(a.lat)
                        lon = float(a.lon)
                        if distance(location.latitude, location.longitude, lat, lon) <= 500:
                            near_classrooms.append(a)

                except:
                    traceback.print_exc()

            empty_room = []

            for a in near_classrooms:

                free = a.is_empty(now, orari_group_by_aula)

                if free:
                    empty_room.append(a)

            output_string = config.emo_room+" <b>EMPTY CLASSROOMS NEAR YOU</b>\n\nLEGEND:\n"
            output_string += config.emo_blue_circle + \
                " = Classroom empty for another 60 minutes\n"
            output_string += config.emo_yellow_square + \
                " = Classroom empty for another 30 minutes\n"
            output_string += config.emo_red_circle + \
                " = Classroom empty for another 15 minutes\n"
            output_string += config.emo_black_circle + \
                " = Classroom empty for less than 15 minutes\n\n"

            update.message.reply_html(output_string)
            output_string = ""
            empty_room.sort(key=lambda x: x.aula_nome, reverse=False)

            # string_list = []

            # for a in empty_room:

            #     for m in (60, 30, 15):

            #         day = now + datetime.timedelta(minutes=m)
            #         free = a.is_empty(day, orari_group_by_aula)
            #         if free and m == 60:
            #             string_list.append(config.emo_blue_circle + " " +
            #                                str(a)+"\n/see_room_schedule_"+a.aula_codice+"\n\n")
            #             break
            #         elif free and m == 30:
            #             string_list.append(config.emo_yellow_square + " " +
            #                                str(a)+"\n/see_room_schedule_"+a.aula_codice+"\n\n")
            #             break
            #         elif free and m == 15:
            #             string_list.append(config.emo_red_circle + " " +
            #                                str(a)+"\n/see_room_schedule_"+a.aula_codice+"\n\n")
            #             break
            #     else:
            #         string_list.append(config.emo_black_circle + " " +
            #                            str(a)+"\n/see_room_schedule_"+a.aula_codice+"\n\n")

            # i = 0
            # for s in string_list:
            #     output_string += s
            #     i += 1
            #     if i % 20 == 0:
            #         update.message.reply_html(output_string)
            #         output_string = ""
            # if output_string != "":
            #     update.message.reply_html(output_string)

            for a in empty_room:

                for m in (60, 30, 15):

                    day = now + datetime.timedelta(minutes=m)
                    free = a.is_empty(day, orari_group_by_aula)
                    if free and m == 60:
                        output_string = config.emo_blue_circle + " " + str(a)
                        update.message.reply_html(
                            output_string, reply_markup=make_inline_see_room_schedule_keyboard(chat_id, a.aula_nome, a.aula_codice))

                        break
                    elif free and m == 30:
                        output_string = config.emo_yellow_square + " " + str(a)
                        update.message.reply_html(
                            output_string, reply_markup=make_inline_see_room_schedule_keyboard(chat_id, a.aula_nome, a.aula_codice))

                        break
                    elif free and m == 15:
                        output_string = config.emo_red_circle + " " + str(a)
                        update.message.reply_html(
                            output_string, reply_markup=make_inline_see_room_schedule_keyboard(chat_id, a.aula_nome, a.aula_codice))

                        break
                else:
                    output_string = config.emo_black_circle + " " + str(a)
                    update.message.reply_html(
                        output_string, reply_markup=make_inline_see_room_schedule_keyboard(chat_id, a.aula_nome, a.aula_codice))

    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### EXCEPTION from " + str(chat_id)+" = " + traceback.format_exc())
        output_string = config.emo_wrong + " Oh no! Something bad happend.."
        update.message.reply_html(output_string,
                                  reply_markup=make_main_keyboard(chat_id))


def send_notifications(bot):
    now = datetime.datetime.now()

    fix_now = datetime.datetime.strptime(
        str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "T" + str(now.hour) + ":" + "%02d" % my_round(now.minute) + ":00", "%Y-%m-%dT%H:%M:%S")

    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### SENDING NOTIFICATION")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### SENDING NOTIFICATION")
    ##### DEBUG #####
    #fix_now = datetime.datetime.strptime("2020-02-28T08:45:00", "%Y-%m-%dT%H:%M:%S")
    #################

    for chat_id in um.get_all_users().keys():
        try:
            u = um.get_user(chat_id)

            if u.notification:
    
                plan = load_user_plan(
                    chat_id, all_teachings)
                timetable = get_lessons(
                    chat_id, fix_now, plan, orari, all_aule)

                # output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                #     int(config.accademic_year) + 1) + "</code>\n"
                # output_string += config.emo_calendar + " " + \
                #     now.strftime("%A %B %d, %Y") + "\n\n"
                # output_string += config.emo_less+"<b>YOUR NEXT LESSON</b>\n\n"

                # output_string += print_output_timetable(timetable)

                output_string = ""
                for l in timetable.lessons:
                    for a in l.lista_aule:
                        output_string += config.emo_room + " <b>" + a.aula_nome+"</b> - "

                    output_string += "IS GOING TO START <b>" + l.materia_descrizione + "</b>"
                    if l.docente_nome != "":
                        output_string += " (<i>" + l.docente_nome + "</i>)"
                    if l.crediti != None and l.crediti != "":
                        output_string += " - " + l.crediti + " CFU"

                    output_string += "\n"

                    output_string += config.emo_clock + \
                        " " + l.inizio.strftime("%H:%M")
                    output_string += " - "
                    output_string += l.fine.strftime("%H:%M")

                    output_string += " "+config.emo_calendar + \
                        " " + l.inizio.strftime("%d/%m/%Y")
                    output_string += "\n\n"

                if output_string:

                    logging.info(
                        "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### SENDING NOTIFICATION TO " + str(chat_id))
                    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### SENDING NOTIFICATION TO " + str(
                        chat_id))

                    bot.send_message(chat_id, output_string,
                                     parse_mode=ParseMode.HTML)

        except:
            traceback.print_exc()
            now = datetime.datetime.now()
            logging.info(
                "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())


def scheduler_function(bot):

    # for i in range(0, 24, 1):
    #     h = "%02d" % i

    for j in range(0, 60, 5):
        m = "%02d" % j
        job = schedule.every().hours.at(":"+m).do(send_notifications, bot)

        # job = schedule.every().day.at(h+":"+m).do(send_notifications, bot)

    while True:

        schedule.run_pending()
        time.sleep(30)

def set_ay(update, context):

    chat_id = update.message.chat_id
    text = update.message.text
    now = datetime.datetime.now()


    if is_admin(chat_id):

        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text +" -> ALLOWED")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text+ " -> ALLOWED")

        try:
            new_ay = int(text.split()[1])
            config.accademic_year = str(new_ay)

            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                         " ### SET ACCADEMIC YEAR TO " + config.accademic_year)
            print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                  " ### SET ACCADEMIC YEAR TO " + config.accademic_year)

            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(int(config.accademic_year) + 1) + "</code>"
        except:
            traceback.print_exc()
            output_string = config.command_help_string

        update.message.reply_html(output_string, reply_markup=make_main_keyboard(chat_id))

    else:
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text +" -> FORBIDDEN!")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text +" -> FORBIDDEN!")
        output_string = config.emo_red_circle + " FORBIDDEN!"
        update.message.reply_html(output_string, reply_markup=make_main_keyboard(chat_id))


def update():
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " +
                 now.strftime("%b %d %Y %H:%M:%S") + " ### RUNNING UPDATE")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### RUNNING UPDATE")

    year = now.strftime("%Y")
    update_day = datetime.datetime.strptime(
        year + "-08-01T00:00:00", "%Y-%m-%dT%H:%M:%S")

    ##### DEBUG #####
    update_day = datetime.datetime.strptime(year + "-08-30T00:00:00", "%Y-%m-%dT%H:%M:%S")
    #################

    if now > update_day:
        config.accademic_year = year
    else:
        config.accademic_year = str(int(year) - 1)

    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### SET ACCADEMIC YEAR TO " + config.accademic_year)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### SET ACCADEMIC YEAR TO " + config.accademic_year)

    # check existence table

    corsi_table = "corsi_" + config.accademic_year + "_it"
    insegnamenti_table = "insegnamenti_" + config.accademic_year + "_it"
    orari_table = "orari_" + config.accademic_year
    aule_table = "aule_" + config.accademic_year


    global all_courses, all_teachings, all_courses_group_by_area, all_aule, orari, orari_group_by_aula

    orari_group_by_aula = collections.defaultdict(list)
    orari = collections.defaultdict(list)

    if check_table(corsi_table) and check_table(insegnamenti_table):

        all_courses, all_teachings, all_courses_group_by_area = get_all_courses()

    if check_table(aule_table):
        all_aule = get_all_aule()

    if check_table(orari_table):
#        csv_orari_filename = download_csv_orari()
#        orari, orari_group_by_aula = get_all_orari_from_file(csv_orari_filename)
#        if len(orari) < 10:
        orari, orari_group_by_aula = get_all_orari()



    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### UPDATE DONE!")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### UPDATE DONE!")

def update_data(update, context):

    chat_id = update.message.chat_id
    text = update.message.text
    now = datetime.datetime.now()

    if is_admin(chat_id):
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text +" -> ALLOWED")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text+ " -> ALLOWED")

        output_string = config.emo_yellow_square + " RUNNING UPDATE"
        update.message.reply_html(output_string, reply_markup=make_main_keyboard(chat_id))

        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " +
                     now.strftime("%b %d %Y %H:%M:%S") + " ### RUNNING MANUAL UPDATE")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### RUNNING MANUAL UPDATE")

#        year = now.strftime("%Y")
#        update_day = datetime.datetime.strptime(year + "-08-01T00:00:00", "%Y-%m-%dT%H:%M:%S")

        ##### DEBUG #####
        # update_day = datetime.datetime.strptime(year + "-08-30T00:00:00", "%Y-%m-%dT%H:%M:%S")
        #################

#        if now > update_day:
#            config.accademic_year = year
#        else:
#            config.accademic_year = str(int(year) - 1)

        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### SET ACCADEMIC YEAR TO " + config.accademic_year)
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
              " ### SET ACCADEMIC YEAR TO " + config.accademic_year)

        # check existence table

        corsi_table = "corsi_" + config.accademic_year + "_it"
        insegnamenti_table = "insegnamenti_" + config.accademic_year + "_it"
        orari_table = "orari_" + config.accademic_year
        aule_table = "aule_" + config.accademic_year

        global all_courses, all_teachings, all_courses_group_by_area, all_aule, orari, orari_group_by_aula

        orari_group_by_aula = collections.defaultdict(list)
        orari = collections.defaultdict(list)

        if check_table(corsi_table) and check_table(insegnamenti_table):

            all_courses, all_teachings, all_courses_group_by_area = get_all_courses()

        if check_table(aule_table):
            all_aule = get_all_aule()

        if check_table(orari_table):
    #        csv_orari_filename = download_csv_orari()
    #        orari, orari_group_by_aula = get_all_orari_from_file(csv_orari_filename)
    #        if len(orari) < 10:
            orari, orari_group_by_aula = get_all_orari()

        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### UPDATE DONE!")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### UPDATE DONE!")

        n_corsi = len(all_courses)
        n_orari = len(orari)
        n_aule = len(all_aule)
        n_insegnamenti = len(all_teachings)

        output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(int(config.accademic_year) + 1) + "</code>\n" + config.emo_end_plan + " UPDATE DONE!\n\n" + config.emo_courses + " Corsi: {}\n".format(n_corsi) + config.emo_plan + " Insegnamenti: {}\n".format(n_insegnamenti) + config.emo_room +" Aule: {}\n".format(n_aule) + config.emo_clock+" Orari: {}".format(n_orari)
        update.message.reply_html(output_string, reply_markup=make_main_keyboard(chat_id))

    else:
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### MESSAGE from " + str(chat_id)+" = " + text +" -> FORBIDDEN!")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### MESSAGE from " + str(chat_id) + " = " + text +" -> FORBIDDEN!")
        output_string = config.emo_red_circle + " FORBIDDEN!"
        update.message.reply_html(output_string, reply_markup=make_main_keyboard(chat_id))


def is_admin(chat_id):
    admins = [ -404582227 ]
    return chat_id in admins

def main():
    logging.info("### WORKING DIR " + config.current_dir)
    print("### WORKING DIR " + config.current_dir)

    if os.path.isdir(config.dir_users_name):
        for f in os.listdir(config.dir_users_name):
            filename = os.fsdecode(f)
            u = um.load_user(int(filename))
            um.add_user(u)

    update()

    updater = Updater(config.token, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help))
    updater.dispatcher.add_handler(CommandHandler("time", print_time))
    updater.dispatcher.add_handler(CommandHandler("update_data", update_data))
    updater.dispatcher.add_handler(CommandHandler("set_ay", set_ay))

    updater.dispatcher.add_handler(MessageHandler(Filters.command, commands))

    updater.dispatcher.add_handler(MessageHandler(Filters.text, message))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback_query))

    updater.dispatcher.add_handler(MessageHandler(
        Filters.location, location))

    updater.dispatcher.add_error_handler(error)

    schedule.every().day.at("07:00").do(update)

    # check_plans_consistency(all_teachings)

    scheduler_thread = threading.Thread(
        target=scheduler_function, args=(updater.bot,))
    scheduler_thread.start()

    # Start the Bot
    print('Listening ...')

    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
