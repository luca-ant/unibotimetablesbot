import os
import collections
import random
import schedule
import sys
import traceback
import datetime
import logging
import json
import requests
import time
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from threading import Lock
from model import Course, Teaching, Mode, Plan, Lesson, Aula, Timetable

token = os.environ['BOT_TOKEN']

bot = telepot.Bot(token)

emo_money = u'\U0001F4B5'
emo_clock = u'\U0001F552'
emo_arrow_back = u'\U00002B05'
emo_arrow_forward = u'\U000027A1'
emo_courses = u'\U0001F4CE'
emo_plan = u'\U0001F4D8'
emo_end_plan = u'\U00002705'
emo_make = u'\U0001F4DD'
emo_timetable = u'\U0000231B'
emo_back = u'\U0001F519'
emo_del = u'\U0000274C'
emo_calendar = u'\U0001F4C5'
emo_room = u'\U0001F3C1'
emo_address = u'\U0001F3EB'
emo_gps = u'\U0001F4CD'
emo_help = u'\U00002139'
emo_no_less = u'\U0001F389'
emo_url = u'\U0001F517'
emo_confused = u'\U0001F615'
emo_ay = u'\U00002712'
emo_404 = u'\U00000034' + u'\U000020E3' + u'\U00000030' + u'\U000020E3' + u'\U00000034' + u'\U000020E3'

ALL_COURSES = emo_courses + " " + "ALL COURSES"
MY_TIMETABLE = emo_timetable + " " + "MY TIMETABLE"
MY_PLAN = emo_plan + " " + "MY STUDY PLAN"
MAKE_PLAN = emo_make + " " + "UPDATE MY STUDY PLAN"
DEL_PLAN = emo_del + " " + "DELETE STUDY PLAN"
END_PLAN = emo_end_plan + " " + "DONE!"
BACK_TO_AREAS = emo_back + " " + "BACK TO AREAS"
BACK_TO_MAIN = emo_back + " " + "BACK TO MAIN"

donation_string = emo_money + " Do you like this bot? If you want to support it you can make a donation here!  -> https://www.paypal.me/lucaant"
help_string = "USE:\n\n" + ALL_COURSES + " to see all teachings' timetables\n\n" + MAKE_PLAN + " to build your study plan\n\nThen you can use:\n\n" + MY_PLAN + " to see your study plan\n\n" + MY_TIMETABLE + " to get your personal lesson's schedules\n\n" + DEL_PLAN + " to delete your plan" + "\n\nFor issues send a mail to luca.ant96@libero.it describing the problem in detail."

current_dir = "./"
# current_dir = "/bot/unibotimetablesbot/"

logging.basicConfig(filename=current_dir + "unibotimetablesbot.log", level=logging.INFO)

dir_plans_name = current_dir + 'plans/'
users_file = current_dir + 'users'

writer_lock = Lock()

all_courses = dict()
all_aule = dict()
all_teachings = dict()
all_courses_group_by_area = collections.defaultdict(list)
users_mode = collections.defaultdict(Mode)

accademic_year = ""


def get_all_aule():
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### GETTING ALL AULE")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### GETTING ALL AULE")

    aule_table = "aule_" + accademic_year

    url = "https://dati.unibo.it/api/action/datastore_search_sql?sql="

    sql_aule = "SELECT * FROM " + aule_table

    json_aule = requests.get(url + sql_aule).text

    all_aule.clear()

    try:
        aule = json.loads(json_aule)["result"]["records"]
    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())
        return

    for aula in aule:
        a = Aula(aula["aula_codice"], aula["aula_nome"], aula["aula_indirizzo"], aula["aula_piano"],
                 aula["lat"],
                 aula["lon"])
        all_aule[a.aula_codice] = a


def get_all_courses():
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### GETTING ALL COURSES")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### GETTING ALL COURSES")
    url = "https://dati.unibo.it/api/action/datastore_search_sql?sql="
    corsi_table = "corsi_" + accademic_year + "_it"
    insegnamenti_table = "insegnamenti_" + accademic_year + "_it"
    #    sql_string = "SELECT "+ insegnamenti_table + ".docente_nome, "+ insegnamenti_table + ".materia_codice, "+ insegnamenti_table + ".materia_descrizione, " + corsi_table + ".corso_codice, "+ insegnamenti_table + ".url, "+ corsi_table + ".tipologia, "  + corsi_table+ ".corso_descrizione, "+ corsi_table+ ".sededidattica"+" FROM " + corsi_table + ", " + insegnamenti_table + " WHERE " + corsi_table + ".corso_codice=" + insegnamenti_table + ".corso_codice"
    sql_insegnamenti = "SELECT * FROM " + insegnamenti_table
    sql_corsi = "SELECT * FROM " + corsi_table

    json_corsi = requests.get(url + sql_corsi).text
    json_insegnamenti = requests.get(url + sql_insegnamenti).text

    all_courses.clear()
    all_teachings.clear()
    all_courses_group_by_area.clear()

    try:
        corsi = json.loads(json_corsi)["result"]["records"]
        insegnamenti = json.loads(json_insegnamenti)["result"]["records"]
    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())
        return

    for c in corsi:
        course = Course(c["corso_codice"], c["corso_descrizione"], c["tipologia"], c["sededidattica"], c["ambiti"],
                        c["url"])
        all_courses[course.corso_codice] = course
        all_courses_group_by_area[course.ambiti].append(course)

    for i in insegnamenti:
        teaching = Teaching(i["corso_codice"], i["materia_codice"], i["materia_descrizione"], i["docente_nome"],
                            i["componente_id"],
                            i["url"])
        all_teachings[i["componente_id"]] = teaching
        try:
            all_courses[teaching.corso_codice].add_teaching(teaching)
        except KeyError:
            pass


def get_plan_timetable(day, plan):
    timetable = Timetable()

    if plan.is_empty():
        return timetable

    orari_table = "orari_" + accademic_year
    aule_table = "aule_" + accademic_year
    url_o = "https://dati.unibo.it/api/action/datastore_search_sql?sql="
    url_a = "https://dati.unibo.it/api/action/datastore_search?resource_id=" + aule_table + "&q="

    sql_orari = "SELECT " + orari_table + ".inizio, " \
                + orari_table + ".fine, " \
                + orari_table + ".aula_codici, " \
                + orari_table + ".componente_id " \
                + " FROM " + orari_table \
                + " WHERE " + orari_table + ".inizio between \'" + day.strftime(
        "%Y/%m/%d") + " 00:00:00\' and " + "\'" + day.strftime("%Y/%m/%d") + " 23:59:59\' AND ("

    for i in range(0, len(plan.teachings), 1):
        t = plan.teachings[i]
        if i == 0:
            sql_orari += orari_table + ".componente_id=" + t.componente_id
        else:
            sql_orari += " OR " + orari_table + ".componente_id=" + t.componente_id
    sql_orari += " )"

    json_orari = requests.get(url_o + sql_orari).text
    ok = json.loads(json_orari)["success"]

    if ok:

        orari = json.loads(json_orari)["result"]["records"]

        for o in orari:
            componente_id = o["componente_id"]

            t = plan.find_teaching_by_componente_id(componente_id)
            if t != None:
                l = Lesson(t.corso_codice, t.materia_codice, t.materia_descrizione, t.docente_nome, t.componente_id,
                           t.url,
                           datetime.datetime.strptime(o["inizio"], "%Y-%m-%dT%H:%M:%S"),
                           datetime.datetime.strptime(o["fine"], "%Y-%m-%dT%H:%M:%S"))
                for code in o["aula_codici"].split():
                    a = all_aule[code]
                    l.add_aula(a)

                timetable.add_lesson(l)
        timetable.lessons.sort(key=lambda x: x.inizio, reverse=False)
        return timetable
    else:
        return None


def load_user_plan(chat_id):
    if os.path.isfile(dir_plans_name + str(chat_id)):
        with open(dir_plans_name + str(chat_id)) as f:
            plan_dict = json.load(f)
            plan = Plan()
            for t in plan_dict["teachings"]:
                try:
                    teaching = Teaching(t["corso_codice"], t["materia_codice"], t["materia_descrizione"],
                                        t["docente_nome"], t["componente_id"], t["url"])
                    plan.add_teaching(teaching)

                except:
                    traceback.print_exc()
                    now = datetime.datetime.now()
                    logging.info("TIMESTAMP = " + now.strftime(
                        "%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())
        return plan

    else:
        return None


# NOT USED
def load_users_plans():
    users_plans = collections.defaultdict(Plan)  # RAM mode

    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### LOADING USERS PLANS")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### LOADING USERS PLANS")
    if os.path.isfile(users_file):
        with open(users_file) as f:
            chat_id = int(f.readline().replace("'", " ").strip())
            users_mode[chat_id] = Mode.NORMAL

    if os.path.isdir(dir_plans_name):
        for filename in os.listdir(dir_plans_name):
            with open(dir_plans_name + filename) as f:
                plan_dict = json.load(f)
                plan = Plan()
                for t in plan_dict["teachings"]:
                    try:
                        teaching = Teaching(t["corso_codice"], t["materia_codice"], t["materia_descrizione"],
                                            t["docente_nome"], t["componente_id"], t["url"])
                        plan.add_teaching(teaching)

                    except:
                        traceback.print_exc()
                        now = datetime.datetime.now()
                        logging.info("TIMESTAMP = " + now.strftime(
                            "%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())
                users_plans[int(filename)] = plan
    return users_plans


def store_user_plan(chat_id, plan):
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### STORE PLAN OF USER " + str(chat_id))
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### STORE PLAN OF USER " + str(chat_id))
    if not os.path.isdir(dir_plans_name):
        os.mkdir(dir_plans_name)

    with open(dir_plans_name + str(chat_id), 'w') as outfile:
        outfile.write(json.dumps(plan, default=lambda x: x.__dict__))


def make_main_keyboard(chat_id, mode):
    buttonLists = list()

    buttonLists.append(list())
    buttonLists.append(list())
    buttonLists.append(list())
    buttonLists.append(list())
    buttonLists.append(list())

    buttonLists[0].append(ALL_COURSES)
    buttonLists[1].append(MAKE_PLAN)
    if users_mode[chat_id] == Mode.PLAN:
        buttonLists[2].append(MY_TIMETABLE)
        buttonLists[3].append(MY_PLAN)
        buttonLists[4].append(DEL_PLAN)
    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_area_keyboard(mode):
    buttonLists = list()

    for i in range(0, len(all_courses_group_by_area.keys()) + 2, 1):
        buttonLists.append(list())

    for i in range(0, len(all_courses_group_by_area.keys()), 1):
        buttonLists[i + 1].append(list(all_courses_group_by_area.keys())[i])

    buttonLists[len(all_courses_group_by_area.keys()) + 1].append(BACK_TO_MAIN)
    if mode == Mode.MAKE_PLAN:
        buttonLists[0].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_courses_keyboard(area, mode):
    buttonLists = list()

    for i in range(0, len(all_courses_group_by_area[area]) + 2, 1):
        buttonLists.append(list())

    for i in range(0, len(all_courses_group_by_area[area]), 1):
        buttonLists[i + 1].append(str(all_courses_group_by_area[area][i]))

    buttonLists[len(all_courses_group_by_area[area]) + 1].append(BACK_TO_AREAS)
    buttonLists[len(all_courses_group_by_area[area]) + 1].append(BACK_TO_MAIN)
    if mode == Mode.MAKE_PLAN:
        buttonLists[0].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def print_plan(chat_id, plan):
    result = emo_plan + " YOUR STUDY PLAN" + "\n\n"
    for t in plan.teachings:
        result += t.materia_codice + " - <b>" + t.materia_descrizione +"</b>"
        if t.docente_nome != "":
            result += " (<i>" + t.docente_nome + "</i>)"
        result += " [ /remove_" + t.componente_id + " ]"
        if t.url != "":
            result += " [ /url_" + t.componente_id + " ]"

        result += "\n\n"

    return result


def print_teachings_message(chat_id, corso_codice):
    result = list()
    mode = users_mode[chat_id]
    if mode == Mode.NORMAL or mode == Mode.PLAN:

        for t in all_courses[corso_codice].teachings:
            t_string = t.materia_codice + " - <b>" + t.materia_descrizione + "</b>"
            if t.docente_nome != "":
                t_string += " (<i>" + t.docente_nome + "</i>)"
            t_string += " [ /schedule_" + t.componente_id + " ]"
            if t.url != "":
                t_string += " [ /url_" + t.componente_id + " ]"

            t_string += "\n\n"
            result.append(t_string)

    elif mode == Mode.MAKE_PLAN:

        for t in all_courses[corso_codice].teachings:
            t_string = t.materia_codice + " - " + t.materia_descrizione + ""
            if t.docente_nome != "":
                t_string += " (" + t.docente_nome + ")"

            t_string += " [ /add_" + t.componente_id + " ]"
            if t.url != "":
                t_string += " [ /url_" + t.componente_id + " ]"

            t_string += "\n\n"
            result.append(t_string)


    else:
        result.clear()

    return result


def make_teachings_keyboard(code, mode):
    buttonLists = list()

    for i in range(0, len(all_courses[code].teachings) + 2, 1):
        buttonLists.append(list())

    for i in range(0, len(all_courses[code].teachings), 1):
        buttonLists[i + 1].append(str(all_courses[code].teachings[i]))

    buttonLists[len(all_courses[code].teachings) + 1].append(BACK_TO_AREAS)
    buttonLists[len(all_courses[code].teachings) + 1].append(BACK_TO_MAIN)

    if mode == Mode.MAKE_PLAN:
        buttonLists[0].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def print_output_timetable(timetable):
    if timetable != None:

        output_string = str(timetable)
        if output_string == "":
            output_string = emo_no_less + " <b>NO LESSONS FOR TODAY</b>"
    else:
        output_string = emo_404 + " SCHEDULES DATA NOT FOUND!"

    return output_string


def make_inline_timetable_keyboard(day):
    next_day = day + datetime.timedelta(days=1)
    prec_day = day - datetime.timedelta(days=1)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=emo_arrow_back + " " + 'Back', callback_data=prec_day.strftime("%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text='Next ' + emo_arrow_forward,
                              callback_data=next_day.strftime("%d/%m/%YT%H:%M:%S"))]
    ])
    return keyboard


def make_inline_keyboard(chat_id, day, componente_id):
    next_day = day + datetime.timedelta(days=1)
    prec_day = day - datetime.timedelta(days=1)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=emo_arrow_back + " " + 'Back',
                              callback_data="schedule_" + componente_id + "_" + prec_day.strftime(
                                  "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text='Next ' + emo_arrow_forward,
                              callback_data="schedule_" + componente_id + "_" + next_day.strftime(
                                  "%d/%m/%YT%H:%M:%S"))]
    ])

    return keyboard


def on_callback_query(msg):
    query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
    try:
        msg_edited = (chat_id, msg['message']['message_id'])

        if (query_data.startswith("schedule")):

            array = query_data.split("_")
            componente_id = array[1]
            day_string = array[len(array) - 1]

            day = datetime.datetime.strptime(day_string, "%d/%m/%YT%H:%M:%S")

            plan = Plan()
            teaching = all_teachings[componente_id]

            plan.add_teaching(teaching)

            timetable = get_plan_timetable(day, plan)

            output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(int(accademic_year) + 1) + "</code>\n"
            output_string += emo_calendar + " " + day.strftime("%A %B %d, %Y") + "\n\n"
            output_string += print_output_timetable(timetable)

            try:
                bot.editMessageText(msg_edited, output_string, parse_mode='HTML',
                                    reply_markup=make_inline_keyboard(chat_id, day, teaching.componente_id))
                # bot.answerCallbackQuery(query_id, text="")
            except telepot.exception.TelegramError:
                pass


        else:
            day = datetime.datetime.strptime(query_data, "%d/%m/%YT%H:%M:%S")
            plan = load_user_plan(chat_id)
            timetable = get_plan_timetable(day, plan)

            output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(int(accademic_year) + 1) + "</code>\n"
            output_string += emo_calendar + " " + day.strftime("%A %B %d, %Y") + "\n\n"
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
            "%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())
        output_string = traceback.format_exc()
        bot.sendMessage(chat_id, output_string,
                        reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))


def on_chat_message(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### MESSAGE = " + str(msg))
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### MESSAGE = " + str(msg))
        if content_type == "text":
            if msg["text"] == '/start':
                users_mode[chat_id] = Mode.NORMAL

                writer_lock.acquire()
                with open(users_file, "w") as f:
                    for u in users_mode.keys():
                        f.writelines(str(u) + "\n")
                writer_lock.release()

                output_string = "Hi! Thanks for trying this bot!\n" + help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))


            elif msg["text"] == '/help':

                output_string = help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))

            elif msg["text"] == ALL_COURSES:

                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your area!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_area_keyboard(users_mode[chat_id]))

            elif msg["text"] == MY_TIMETABLE:
                users_mode[chat_id] = Mode.PLAN

                now = datetime.datetime.now()

                ##### DEBUG #####
                #  now = datetime.datetime.strptime("29/05/2019", "%d/%m/%Y")
                #################
                plan = load_user_plan(chat_id)

                timetable = get_plan_timetable(now, plan)
                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += emo_calendar + " " + now.strftime("%A %B %d, %Y") + "\n\n"

                output_string += print_output_timetable(timetable)

                bot.sendMessage(chat_id, donation_string, parse_mode='HTML')
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_inline_timetable_keyboard(now))



            elif msg["text"] == MY_PLAN:
                users_mode[chat_id] = Mode.PLAN

                plan = load_user_plan(chat_id)
                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"

                output_string += print_plan(chat_id, plan)
                bot.sendMessage(chat_id, donation_string, parse_mode='HTML')
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))


            elif msg["text"] == DEL_PLAN:

                users_mode[chat_id] = Mode.DEL

                output_string = "Are you sure? Send \"<b>YES</b>\" to confirm or \"<b>NO</b>\" to cancel (without quotes)"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML')

            elif msg["text"] == "YES" and users_mode[chat_id] == Mode.DEL:

                users_mode[chat_id] = Mode.NORMAL

                if os.path.isfile(dir_plans_name + str(chat_id)):
                    os.remove(dir_plans_name + str(chat_id))

                output_string = "Your study plan was deleted!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))

            elif msg["text"] == "NO" and users_mode[chat_id] == Mode.DEL:
                users_mode[chat_id] = Mode.PLAN
                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your action!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))


            elif msg["text"] == MAKE_PLAN:
                users_mode[chat_id] = Mode.MAKE_PLAN

                plan = Plan()
                store_user_plan(chat_id, plan)

                output_string = "Find your teachings and add them to your study plan. Send " + END_PLAN + " when you have finished!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_area_keyboard(users_mode[chat_id]))

            elif msg["text"] == END_PLAN:
                users_mode[chat_id] = Mode.PLAN

                output_string = "Well done! Now you can use " + MY_PLAN + " to see your study plan and " + MY_TIMETABLE + " to get your lessons shedules!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))

            elif msg["text"] == BACK_TO_MAIN:

                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your action!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))
            elif msg["text"] == BACK_TO_AREAS:

                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your area!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_area_keyboard(users_mode[chat_id]))
            elif msg["text"] in all_courses_group_by_area.keys():

                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your course!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_courses_keyboard(msg["text"], users_mode[chat_id]))

            elif msg["text"].split()[0] in all_courses.keys():

                course = all_courses[msg["text"].split()[0]]
                if course.url != "":
                    output_string = emo_url + " " + course.url
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML')

                string_list = print_teachings_message(chat_id, course.corso_codice)

                i = 0
                output_string = ""
                for s in string_list:
                    output_string += s
                    i += 1
                    if i % 20 == 0:
                        bot.sendMessage(chat_id, output_string, parse_mode='HTML')
                        output_string = ""
                if output_string != "":
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML')



            elif msg["text"].startswith("/add_") and users_mode[chat_id] == Mode.MAKE_PLAN:

                array = msg["text"].split("_")
                componente_id = array[1]

                if componente_id in all_teachings.keys():
                    teaching = all_teachings[componente_id]
                    plan = load_user_plan(chat_id)
                    state = plan.add_teaching(teaching)
                    store_user_plan(chat_id, plan)

                    if state:
                        output_string = "ADDED " + str(teaching)
                    else:
                        output_string = str(teaching) + " ALREADY IN YOUR STUDY PLAN"
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML')


            elif msg["text"].startswith("/remove_"):

                array = msg["text"].split("_")
                componente_id = array[1]

                teaching = all_teachings[componente_id]

                plan = load_user_plan(chat_id)

                state = plan.remove_teaching(teaching)
                store_user_plan(chat_id, plan)

                if state:
                    output_string = "REMOVED " + str(teaching)
                else:
                    output_string = str(teaching) + " NOT IN YOUR STUDY PLAN"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML')

            elif msg["text"].startswith("/schedule_"):

                array = msg["text"].split("_")
                componente_id = array[1]

                if componente_id in all_teachings.keys():
                    plan = Plan()
                    teaching = all_teachings[componente_id]

                    plan.add_teaching(teaching)

                    now = datetime.datetime.now()

                    ##### DEBUG #####
                    # now = datetime.datetime.strptime("29/05/2019", "%d/%m/%Y")
                    #################

                    timetable = get_plan_timetable(now, plan)

                    output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                        int(accademic_year) + 1) + "</code>\n"
                    output_string += emo_calendar + " " + now.strftime("%A %B %d, %Y") + "\n\n"

                    output_string += print_output_timetable(timetable)

                    bot.sendMessage(chat_id, donation_string, parse_mode='HTML')
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_inline_keyboard(chat_id, now, teaching.componente_id))


            elif msg["text"].startswith("/url_"):

                array = msg["text"].split("_")
                componente_id = array[1]

                if componente_id in all_teachings.keys():
                    output_string = emo_url + " " + all_teachings[componente_id].url

                    bot.sendMessage(chat_id, output_string, parse_mode='HTML')


            else:

                if users_mode[chat_id] != Mode.PLAN and users_mode[chat_id] != Mode.NORMAL:
                    if os.path.isfile(dir_plans_name + str(chat_id)):
                        users_mode[chat_id] = Mode.PLAN
                    else:
                        users_mode[chat_id] = Mode.NORMAL

                output_string = emo_confused + " Sorry.. I don't understand.."
                output_string += "\n\n" + help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))
        else:

            if users_mode[chat_id] != Mode.PLAN and users_mode[chat_id] != Mode.NORMAL:
                if os.path.isfile(dir_plans_name + str(chat_id)):
                    users_mode[chat_id] = Mode.PLAN
                else:
                    users_mode[chat_id] = Mode.NORMAL

            output_string = emo_confused + " Sorry.. I don't understand.."
            output_string += "\n\n" + help_string
            bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                            reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))
    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())
        output_string = traceback.format_exc()
        bot.sendMessage(chat_id, output_string,
                        reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))


def check_table(table):
    url = "https://dati.unibo.it/api/action/datastore_search_sql?sql="

    sql = "SELECT * FROM " + table + " limit 1"

    json_response = requests.get(url + sql).text
    ok = json.loads(json_response)["success"]

    now = datetime.datetime.now()
    if ok:
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### TABLE " + table + " PRESENT")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### TABLE " + table + " PRESENT")
        return True
    else:
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### TABLE " + table + " NOT PRESENT")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### TABLE " + table + " NOT PRESENT")
        return False


def update():
    now = datetime.datetime.now()
    global accademic_year
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### RUNNING UPDATE")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### RUNNING UPDATE")

    year = now.strftime("%Y")
    update_day = datetime.datetime.strptime(year + "-08-15T00:00:00", "%Y-%m-%dT%H:%M:%S")

    ##### DEBUG #####
    # update_day = datetime.datetime.strptime(year + "-08-30T00:00:00", "%Y-%m-%dT%H:%M:%S")
    #################
    if now > update_day:
        accademic_year = year
    else:
        accademic_year = str(int(year) - 1)

    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### SET ACCADEMIC YEAR TO " + accademic_year)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### SET ACCADEMIC YEAR TO " + accademic_year)

    # check existence table

    corsi_table = "corsi_" + accademic_year + "_it"
    insegnamenti_table = "insegnamenti_" + accademic_year + "_it"
    orari_table = "orari_" + accademic_year
    aule_table = "aule_" + accademic_year

    if check_table(corsi_table) and check_table(insegnamenti_table):
        get_all_courses()

    if check_table(aule_table):
        get_all_aule()

    check_table(orari_table)

    writer_lock.acquire()
    with open(users_file, "w") as f:
        for u in users_mode.keys():
            f.writelines(str(u) + "\n")
    writer_lock.release()



if os.path.isfile(users_file):
    with open(users_file) as f:
        chat_id = int(f.readline().replace("'", " ").strip())
        if os.path.isfile(dir_plans_name + str(chat_id)):
            users_mode[chat_id] = Mode.PLAN
        else:
            users_mode[chat_id] = Mode.NORMAL

update()
schedule.every().day.at("04:00").do(update)
MessageLoop(bot, {'chat': on_chat_message, 'callback_query': on_callback_query}).run_as_thread()

print('Listening ...')
# Keep the program running.
while 1:
    schedule.run_pending()
    time.sleep(10)
