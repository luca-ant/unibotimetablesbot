import os
import collections
import random
import schedule
import sys
import traceback
import datetime
import logging
import wget
import json
import requests
import time
import telepot
import csv
from telepot.loop import MessageLoop

from model import Course, Teaching, Mode, Plan, Lesson, Aula, Timetable, User
from keyboards import make_area_keyboard, make_courses_keyboard, make_inline_timetable_keyboard, make_inline_today_schedule_keyboard, make_main_keyboard, make_year_keyboard
from plan_manager import get_next_lesson, get_plan_timetable, load_user_plan, print_output_timetable, print_plan, print_plan_message, print_teachings_message
from user_manager import add_user, check_user, get_user, load_user, store_user, store_user_plan, get_all_users
from db_query import check_table, download_csv_orari, get_all_aule, get_all_courses
from utils import my_round
import config


config.current_dir = os.path.dirname(os.getcwd())
bot = telepot.Bot(config.token)

all_courses = dict()
all_aule = dict()
all_teachings = dict()
all_courses_group_by_area = collections.defaultdict(list)
orari = collections.defaultdict(list)


def on_callback_query(msg):
    query_id, chat_id, query_data = telepot.glance(
        msg, flavor='callback_query')
    try:
        msg_edited = (chat_id, msg['message']['message_id'])

        if (query_data.startswith("course")):

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

            timetable = get_plan_timetable(day, plan, orari)

            output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + \
                "/" + str(int(config.accademic_year) + 1) + "</code>\n"
            output_string += config.emo_calendar + " " + \
                day.strftime("%A %B %d, %Y") + "\n\n"

            output_string += config.emo_pin+" <b>"+str(course)+"</b>\n\n"

            output_string += config.emo_timetable + " <b>TIMETABLE</b>\n\n"

            output_string += print_output_timetable(timetable)

            try:
                bot.editMessageText(msg_edited, output_string, parse_mode='HTML',
                                    reply_markup=make_inline_today_schedule_keyboard(chat_id, day, course.corso_codice, year))
                # bot.answerCallbackQuery(query_id, text="")
            except telepot.exception.TelegramError:
                bot.answerCallbackQuery(query_id, text="SLOW DOWN!!")
                pass

        else:
            if query_data.endswith("today"):
                day = datetime.datetime.now()
            else:
                day = datetime.datetime.strptime(
                    query_data, "%d/%m/%YT%H:%M:%S")

            plan = load_user_plan(chat_id)

            if plan != None:

                timetable = get_plan_timetable(day, plan, orari)

                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + \
                    "/" + str(int(config.accademic_year) + 1) + "</code>\n"
                output_string += config.emo_calendar + " " + \
                    day.strftime("%A %B %d, %Y") + "\n\n"
                output_string += config.emo_timetable + " <b>YOUR TIMETABLE</b>\n\n"

                output_string += print_output_timetable(timetable)
                try:
                    bot.editMessageText(msg_edited, output_string, parse_mode='HTML',
                                        reply_markup=make_inline_timetable_keyboard(day))
                except telepot.exception.TelegramError:
                    bot.answerCallbackQuery(query_id, text="SLOW DOWN!!")

                    pass

    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime(
            "%b %d %Y %H:%M:%S") + " ### EXCEPTION from " + str(chat_id)+" = " + traceback.format_exc())

        output_string = config.emo_wrong + " Oh no! Something bad happend.."

        bot.sendMessage(chat_id, output_string,
                        reply_markup=make_main_keyboard(chat_id))


def on_chat_message(msg):
    try:

        content_type, chat_type, chat_id = telepot.glance(msg)
        msg.pop("chat", None)
        msg.pop("from", None)

        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### MESSAGE from " + str(chat_id)+" = " + str(msg))
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
              " ### MESSAGE from " + str(chat_id) + " = " + str(msg))

        if content_type == "text":

            if msg["text"] == '/start':
                get_user(chat_id).mode = Mode.NORMAL

                store_user(chat_id)

                output_string = "Hi! Thanks for trying this bot!\n\n" + config.help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif chat_id not in get_all_users().keys():
                check_user(chat_id)
                store_user(chat_id)

                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                    int(config.accademic_year) + 1) + "</code>\n"
                output_string += "Choose your action!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == '/help':

                output_string = config.help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.ALL_COURSES:
                u = get_user(chat_id)

                store_user(chat_id)

                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                    int(config.accademic_year) + 1) + "</code>\n"
                output_string += "Choose your area!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_area_keyboard(all_courses_group_by_area, u.mode))

            elif msg["text"] == config.MY_TIMETABLE:
                get_user(chat_id).mode = Mode.PLAN
                store_user(chat_id)

                now = datetime.datetime.now()

                ##### DEBUG #####
                #  now = datetime.datetime.strptime("29/05/2019", "%d/%m/%Y")
                #################
                plan = load_user_plan(chat_id)

                if plan != None:

                    timetable = get_plan_timetable(now, plan, orari)
                    output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                        int(config.accademic_year) + 1) + "</code>\n"
                    output_string += config.emo_calendar + " " + \
                        now.strftime("%A %B %d, %Y") + "\n\n"

                    output_string += config.emo_timetable + " <b>YOUR TIMETABLE</b>" + "\n\n"

                    output_string += print_output_timetable(timetable)

                    # bot.sendMessage(chat_id, important_string, parse_mode='HTML')
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_inline_timetable_keyboard(now))

                else:
                    output_string = "You haven't a study plan yet! Use " + \
                        config.MAKE_PLAN + " to make it"
                    get_user(chat_id).mode = Mode.NORMAL
                    store_user(chat_id)
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.MY_PLAN:
                get_user(chat_id).mode = Mode.PLAN
                store_user(chat_id)

                plan = load_user_plan(chat_id)
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
                            bot.sendMessage(chat_id, output_string,
                                            parse_mode='HTML', reply_markup=make_main_keyboard(chat_id))
                            output_string = ""
                    if output_string != "":
                        bot.sendMessage(chat_id, output_string,
                                        parse_mode='HTML', reply_markup=make_main_keyboard(chat_id))
                else:
                    output_string = "You haven't a study plan yet! Use " + \
                        config.MAKE_PLAN + " to make it"
                    get_user(chat_id).mode = Mode.NORMAL
                    store_user(chat_id)
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.DEL_PLAN:

                get_user(chat_id).mode = Mode.DEL

                output_string = "Are you sure? Send \"<b>YES</b>\" to confirm or \"<b>NO</b>\" to cancel (without quotes)"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML')

            elif msg["text"].upper() == "YES" and get_user(chat_id).mode == Mode.DEL:

                get_user(chat_id).mode = Mode.NORMAL
                store_user(chat_id)

                if os.path.isfile(config.dir_plans_name + str(chat_id)):
                    os.remove(config.dir_plans_name + str(chat_id))

                output_string = "Your study plan was deleted!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == "NO" and get_user(chat_id).mode == Mode.DEL:
                get_user(chat_id).mode = Mode.PLAN
                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                    int(config.accademic_year) + 1) + "</code>\n"
                output_string += "Choose your action!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.MAKE_PLAN:
                u = get_user(chat_id)
                u.mode = Mode.MAKE_PLAN
                store_user(chat_id)

                if not os.path.isfile(config.dir_plans_name + str(chat_id)):
                    plan = Plan()
                    store_user_plan(chat_id, plan)

                output_string = "Find your teachings and add them to your study plan. Send " + \
                    config.END_PLAN + " when you have finished!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_area_keyboard(all_courses_group_by_area, u.mode))

            elif msg["text"] == config.END_PLAN:
                u = get_user(chat_id)
                u.mode = Mode.PLAN
                store_user(chat_id)
                plan = load_user_plan(chat_id)
                store_user_plan(chat_id, plan)

                output_string = "Well done! Now you can use " + config.MY_PLAN + \
                    " to see your study plan and " + config.MY_TIMETABLE + \
                    " to get your lessons shedules!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.BACK_TO_MAIN:
                check_user(chat_id)
                store_user(chat_id)

                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                    int(config.accademic_year) + 1) + "</code>\n"
                output_string += "Choose your action!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.BACK_TO_AREAS:
                u = get_user(chat_id)
                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                    int(config.accademic_year) + 1) + "</code>\n"
                output_string += "Choose your area!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_area_keyboard(all_courses_group_by_area, u.mode))

            elif msg["text"] == config.NOTIFY_ON:
                u = get_user(chat_id)

                if os.path.isfile(config.dir_plans_name + str(chat_id)):
                    u.notification = True
                    store_user(chat_id)

                    output_string = "Notifications enabled!"

                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))
                else:
                    output_string = "You haven't a study plan yet! Use " + \
                        config.MAKE_PLAN + " to make it"
                    get_user(chat_id).mode = Mode.NORMAL
                    store_user(chat_id)
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.NOTIFY_OFF:
                u = get_user(chat_id)

                if u.notification:
                    u.notification = False
                    store_user(chat_id)

                    output_string = "Notifications disabled!"

                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))
                else:
                    output_string = "Notifications already disabled!"

                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.DONATION:
                check_user(chat_id)
                store_user(chat_id)

                bot.sendMessage(chat_id, config.donation_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.HELP:

                check_user(chat_id)
                store_user(chat_id)

                bot.sendMessage(chat_id, config.help_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == config.PRIVACY:
                check_user(chat_id)
                store_user(chat_id)

                bot.sendMessage(chat_id, config.privacy_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] in all_courses_group_by_area.keys():
                u = get_user(chat_id)

                output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                    int(config.accademic_year) + 1) + "</code>\n"
                output_string += "Choose your course!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_courses_keyboard(all_courses_group_by_area, msg["text"], u.mode))

            elif msg["text"].split()[0] in all_courses.keys():
                course = all_courses[msg["text"].split()[0]]
                u = get_user(chat_id)
                try:

                    year = int(msg["text"].split()[-1])
                    if u.mode == Mode.MAKE_PLAN:

                        string_list = print_teachings_message(
                            chat_id, all_courses, course.corso_codice, year)

                        i = 0

                        output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                            int(config.accademic_year) + 1) + "</code>\n\n"
                        output_string += config.emo_pin + \
                            " <b>"+str(course)+"</b>\n\n"
                        output_string += config.emo_plan + " <b>TEACHINGS " + \
                            str(year) + " YEAR</b> (sorted by name)\n\n"
                        for s in string_list:
                            output_string += s
                            i += 1
                            if i % 20 == 0:
                                bot.sendMessage(chat_id, output_string,
                                                parse_mode='HTML')
                                output_string = ""
                        if output_string != "":
                            bot.sendMessage(chat_id, output_string,
                                            parse_mode='HTML')

                    elif u.mode == Mode.NORMAL or u.mode == Mode.PLAN:

                        plan = Plan()
                        for t in course.teachings:
                            if t.anno == None or t.anno == "" or int(t.anno) == year:
                                plan.add_teaching(t)

                        now = datetime.datetime.now()

                        timetable = get_plan_timetable(now, plan, orari)

                        output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                            int(config.accademic_year) + 1) + "</code>\n"

                        output_string += config.emo_calendar + " " + \
                            now.strftime("%A %B %d, %Y") + "\n\n"

                        output_string += config.emo_pin + \
                            " <b>"+str(course)+"</b>\n\n"

                        output_string += config.emo_timetable + " <b>TIMETABLE</b>\n\n"

                        output_string += print_output_timetable(timetable)

                        # bot.sendMessage(chat_id, important_string, parse_mode='HTML')
                        bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                        reply_markup=make_inline_today_schedule_keyboard(chat_id, now, course.corso_codice, year))

                    else:
                        check_user(chat_id)
                        store_user(chat_id)

                except ValueError:

                    output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + \
                        "/" + str(int(config.accademic_year) + 1) + \
                        "</code>\n\n"
                    output_string += "<b>SELECTED COURSE:\n" + \
                        config.emo_pin+" " + str(course)+"</b>"

                    if course.url != "":
                        output_string += "\n" + config.emo_url + " " + course.url

                    output_string += "\n\nChoose your year!"

                    bot.sendMessage(chat_id, output_string, parse_mode='HTML', disable_web_page_preview=True,
                                    reply_markup=make_year_keyboard(all_courses, course.corso_codice, get_user(chat_id).mode))

            elif msg["text"].startswith("/add_") and get_user(chat_id).mode == Mode.MAKE_PLAN:

                array = msg["text"].split("_")
                componente_id = array[1]

                if componente_id in all_teachings.keys():
                    teaching = all_teachings[componente_id]
                    plan = load_user_plan(chat_id)
                    state = plan.add_teaching(teaching)
                    store_user_plan(chat_id, plan)

                    if state:
                        output_string = "ADDED " + teaching.materia_descrizione
                    else:
                        output_string = teaching.materia_descrizione + " ALREADY IN YOUR STUDY PLAN"

                    bot.sendMessage(chat_id, output_string,
                                    parse_mode='HTML', disable_notification=True)

            elif msg["text"].startswith("/remove_"):

                array = msg["text"].split("_")
                componente_id = array[1]

                teaching = all_teachings[componente_id]

                plan = load_user_plan(chat_id)

                state = plan.remove_teaching(teaching)
                store_user_plan(chat_id, plan)

                if state:
                    output_string = "REMOVED " + teaching.materia_descrizione
                else:
                    output_string = teaching.materia_descrizione + " NOT IN YOUR STUDY PLAN"

                bot.sendMessage(chat_id, output_string,
                                parse_mode='HTML', disable_notification=True)

            elif msg["text"].startswith(config.SET_NOT_TIME_CMD):
                u = get_user(chat_id)
                try:
                    u.notification_time = my_round(int(msg["text"].split()[1]))
                    store_user(chat_id)
                    output_string = "Great job! Now you should receive notifications " + \
                        str(u.notification_time)+" minutes before the lesson!"

                except:
                    output_string = config.command_help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"].startswith("/url_"):

                array = msg["text"].split("_")
                componente_id = array[1]

                if componente_id in all_teachings.keys():
                    output_string = config.emo_url + " " + \
                        all_teachings[componente_id].url

                    bot.sendMessage(
                        chat_id, output_string, disable_web_page_preview=True, parse_mode='HTML')

            else:
                check_user(chat_id)
                store_user(chat_id)

                output_string = config.emo_confused + " Sorry.. I don't understand.."
                output_string += "\n\n" + config.help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))
        else:

            check_user(chat_id)
            store_user(chat_id)

            output_string = config.emo_confused + " Sorry.. I don't understand.."
            output_string += "\n\n" + config.help_string
            bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                            reply_markup=make_main_keyboard(chat_id))
    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### EXCEPTION from " + str(chat_id)+" = " + traceback.format_exc())
        output_string = config.emo_wrong + " Oh no! Something bad happend.."
        bot.sendMessage(chat_id, output_string,
                        reply_markup=make_main_keyboard(chat_id))


def update():
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " +
                 now.strftime("%b %d %Y %H:%M:%S") + " ### RUNNING UPDATE")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### RUNNING UPDATE")

    year = now.strftime("%Y")
    update_day = datetime.datetime.strptime(
        year + "-08-15T00:00:00", "%Y-%m-%dT%H:%M:%S")

    ##### DEBUG #####
    # update_day = datetime.datetime.strptime(year + "-08-30T00:00:00", "%Y-%m-%dT%H:%M:%S")
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

    global all_courses, all_teachings, all_courses_group_by_area, all_aule, orari

    if check_table(corsi_table) and check_table(insegnamenti_table):

        all_courses, all_teachings, all_courses_group_by_area = get_all_courses()

    if check_table(aule_table):
        all_aule = get_all_aule()

    if check_table(orari_table):
        orari = download_csv_orari()


def send_notifications():
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### START SENDING NOTIFICATIONS")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### START SENDING NOTIFICATIONS")

    fix_now = datetime.datetime.strptime(
        str(now.year)+"-"+str(now.month) + "-"+str(now.day)+"T"+str(now.hour)+":"+str(now.minute)+":00", "%Y-%m-%dT%H:%M:%S")

    ##### DEBUG #####
    # fix_now = datetime.datetime.strptime("2019-10-08T13:45:00", "%Y-%m-%dT%H:%M:%S")
    #################

    for chat_id in get_all_users().keys():
        try:
            u = get_user(chat_id)

            if u.notification:

                plan = load_user_plan(chat_id)

                timetable = get_next_lesson(chat_id, fix_now, plan, orari)

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

                    output_string += config.emo_clock + " " + \
                        l.inizio.strftime("%H:%M")
                    output_string += " - "
                    output_string += l.fine.strftime("%H:%M")

                    output_string += " "+config.emo_calendar + \
                        " " + l.inizio.strftime("%d/%m/%Y")
                    output_string += "\n\n"

                if output_string:

                    logging.info(
                        "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### SENDING NOTIFICATION TO " + str(chat_id))
                    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + "  ### SENDING NOTIFICATION TO " + str(
                        chat_id))

                    # bot.sendMessage(chat_id, output_string, parse_mode='HTML',reply_markup=make_inline_timetable_keyboard(now))
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML')

            now = datetime.datetime.now()
            logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                         " ### END SENDING NOTIFICATIONS")
            print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                  " ### END SENDING NOTIFICATIONS")

        except:
            traceback.print_exc()
            now = datetime.datetime.now()
            logging.info(
                "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())


if __name__ == "__main__":

    if os.path.isdir(config.dir_users_name):
        for f in os.listdir(config.dir_users_name):
            filename = os.fsdecode(f)
            u = load_user(int(filename))
            add_user(u)

    update()
    schedule.every().day.at("07:00").do(update)

    for i in range(8, 20, 1):

        h = "%02d" % i

        for j in range(0, 60, 5):
            m = "%02d" % j

            schedule.every().monday.at(h+":"+m).do(send_notifications)
            schedule.every().tuesday.at(h+":"+m).do(send_notifications)
            schedule.every().wednesday.at(h+":"+m).do(send_notifications)
            schedule.every().thursday.at(h+":"+m).do(send_notifications)
            schedule.every().friday.at(h+":"+m).do(send_notifications)

    MessageLoop(bot, {'chat': on_chat_message,
                      'callback_query': on_callback_query}).run_as_thread()

    print('Listening ...')
    # Keep the program running.
    while 1:
        schedule.run_pending()
        time.sleep(1)
