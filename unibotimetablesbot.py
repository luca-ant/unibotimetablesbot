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
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from threading import Lock
from model import Course, Teaching, Mode, Plan, Lesson, Aula, Timetable, User

token = os.environ['BOT_TOKEN']

bot = telepot.Bot(token)

emo_money = u'\U0001F4B5'
emo_clock = u'\U0001F552'
emo_arrow_back = u'\U00002B05'
emo_double_arrow_back = u'\U000023EA'
emo_arrow_forward = u'\U000027A1'
emo_double_arrow_forward = u'\U000023E9'
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
emo_404 = u'\U00000034' + u'\U000020E3' + u'\U00000030' + \
    u'\U000020E3' + u'\U00000034' + u'\U000020E3'
emo_not_on = u'\U0001F514'
emo_not_off = u'\U0001F515'
emo_wrong = u'\U0001F914'
emo_privacy = u'\U0001F50F'

ALL_COURSES = emo_courses + " " + "ALL COURSES"
MY_TIMETABLE = emo_timetable + " " + "MY TIMETABLE"
MY_PLAN = emo_plan + " " + "MY STUDY PLAN"
MAKE_PLAN = emo_make + " " + "UPDATE MY STUDY PLAN"
NOTIFY_ON = emo_not_on + " " + "ENABLE NOTIFICATIONS"
NOTIFY_OFF = emo_not_off + " " + "DISABLE NOTIFICATIONS"
DEL_PLAN = emo_del + " " + "DELETE STUDY PLAN"
END_PLAN = emo_end_plan + " " + "DONE!"
BACK_TO_AREAS = emo_back + " " + "BACK TO AREAS"
BACK_TO_MAIN = emo_back + " " + "BACK TO MAIN"
DONATION = emo_money + " " + "DONATION"
HELP = emo_help + " " + "HELP"
PRIVACY = emo_privacy + " " + "PRIVACY POLICY"

donation_string = emo_money + \
    " Do you like this bot? If you want to support it you can make a donation here!  -> https://www.paypal.me/lucaant"

important_string = "<b>IMPORTANT! All data (provided by https://dati.unibo.it) are updated once a day. For suddend changes or extra lessons please check on official Unibo site! (Especially for the first weeks)</b>"
help_string = "This bot helps you to get your personal timetable of Unibo lessons. First of all <b>you need to make your study plan</b> by pressing " + MAKE_PLAN+" and then you have to add your teachings. After that by simply pressing " + MY_TIMETABLE+" you get your personal  timetable for today!\n\n<b>USE:</b>\n\n" + ALL_COURSES + " to see today's schedule\n\n" + MAKE_PLAN + " to make your study plan\n\n" + MY_PLAN + " to see your study plan and remove teachings\n\n" + MY_TIMETABLE + " to get your personal lesson's schedule\n\n" + NOTIFY_ON + \
    " to receive a notification every morning\n\n" + DEL_PLAN + " to delete your plan" + \
    "\n\nFor issues send a mail to luca.ant96@libero.it describing the problem in detail.\n\n" + important_string

privacy_string = "<b>In order to provide you the service, this bot collects user data like your study plan and your preferences (ON/OFF notification...). \nUsing this bot you allow your data to be saved.</b>"


current_dir = os.getcwd() + "/"
logging.basicConfig(filename=current_dir +
                    "unibotimetablesbot.log", level=logging.INFO)

logging.info("### WORK DIR " + current_dir)

dir_plans_name = current_dir + 'plans/'
dir_users_name = current_dir + 'users/'


# writer_lock = Lock()

all_courses = dict()
all_aule = dict()
all_teachings = dict()
all_courses_group_by_area = collections.defaultdict(list)
users = dict()
accademic_year = ""

orari = collections.defaultdict(list)


def get_all_aule():
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " +
                 now.strftime("%b %d %Y %H:%M:%S") + " ### GETTING ALL AULE")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### GETTING ALL AULE")

    aule_table = "aule_" + accademic_year

    url = "https://dati.unibo.it/api/action/datastore_search_sql"

    sql_aule = "SELECT * FROM " + aule_table

    headers = {'Content-type': 'application/json',
               'Accept': 'application/json'}
    json_aule = requests.post(url, headers=headers,
                              data='{"sql":'+'"'+sql_aule+'"}').text

    all_aule.clear()

    try:
        aule = json.loads(json_aule)["result"]["records"]
    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### EXCEPTION = " + traceback.format_exc())
        return

    for aula in aule:
        a = Aula(aula["aula_codice"], aula["aula_nome"], aula["aula_indirizzo"], aula["aula_piano"],
                 aula["lat"],
                 aula["lon"])
        all_aule[a.aula_codice] = a


def get_all_courses():
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### GETTING ALL COURSES")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### GETTING ALL COURSES")
    url = "https://dati.unibo.it/api/action/datastore_search_sql"
    corsi_table = "corsi_" + accademic_year + "_it"
    insegnamenti_table = "insegnamenti_" + accademic_year + "_it"
    curricula_table = "curriculadettagli_"+accademic_year+"_it"

    # sql_insegnamenti = "SELECT " + insegnamenti_table + ".*, " + curricula_table + ".anno," + curricula_table+".insegnamento_crediti" + " FROM " + curricula_table + \
    #     ", " + insegnamenti_table + " WHERE " + curricula_table + \
    #     ".componente_id=" + insegnamenti_table + ".componente_id"

    sql_insegnamenti = "SELECT " + insegnamenti_table + ".*, " + curricula_table + ".anno," + curricula_table+".insegnamento_crediti" + " FROM " + curricula_table + \
        " RIGHT JOIN " + insegnamenti_table + " ON " + curricula_table + \
        ".componente_id=" + insegnamenti_table + ".componente_id"

    # sql_insegnamenti = "SELECT * FROM " + insegnamenti_table
    sql_corsi = "SELECT * FROM " + corsi_table

    headers = {'Content-type': 'application/json',
               'Accept': 'application/json'}

    json_corsi = requests.post(
        url, headers=headers, data='{"sql":'+'"'+sql_corsi+'"}').text
    json_insegnamenti = requests.post(
        url, headers=headers, data='{"sql":'+'"'+sql_insegnamenti+'"}').text

    all_courses.clear()
    all_teachings.clear()
    all_courses_group_by_area.clear()

    try:
        corsi = json.loads(json_corsi)["result"]["records"]
        insegnamenti = json.loads(json_insegnamenti)["result"]["records"]
    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### EXCEPTION = " + traceback.format_exc())
        return

    for c in corsi:
        course = Course(c["corso_codice"], c["corso_descrizione"], c["tipologia"], c["sededidattica"], c["ambiti"],
                        c["url"], c["durata"])
        all_courses[course.corso_codice] = course
        all_courses_group_by_area[course.ambiti].append(course)

    for i in insegnamenti:
        if "TIROCINIO" not in i['materia_descrizione'].upper():
            teaching = Teaching(i["corso_codice"], i["materia_codice"], i["materia_descrizione"], i["docente_nome"],
                                i["componente_id"],
                                i["url"], i["anno"], i["insegnamento_crediti"], i["componente_padre"])

            ##### DEBUG #####
            # if teaching.componente_id == '448379':
            #     print(teaching)
            #################

            if teaching.componente_id not in all_teachings.keys():
                all_teachings[i["componente_id"]] = teaching

                try:
                    all_courses[teaching.corso_codice].add_teaching(teaching)
                except KeyError:
                    pass

    for key in all_teachings.keys():
        t = all_teachings[key]
        if (t.anno == None or t.anno == "") and t.componente_padre != None and t.componente_padre != "":
            t.anno = all_teachings[t.componente_padre].anno
        if (t.crediti == None or t.crediti == "") and t.componente_padre != None and t.componente_padre != "":
            t.crediti = all_teachings[t.componente_padre].crediti

    for key in all_courses.keys():
        all_courses[key].teachings.sort(
            key=lambda x: x.materia_descrizione, reverse=False)


def get_plan_timetable(day, plan):
    timetable = Timetable()

    if plan.is_empty():
        return timetable

    start = datetime.datetime.strptime(day.strftime(
        "%Y-%m-%d") + "T00:00:00", "%Y-%m-%dT%H:%M:%S")
    stop = datetime.datetime.strptime(day.strftime(
        "%Y-%m-%d") + "T23:59:59", "%Y-%m-%dT%H:%M:%S")

    for t in plan.teachings:
        for o in orari[t.componente_id]:
            try:
                ##### DEBUG #####
                # if t.componente_id == '448380':
                #     print(t)
                #################
                inizio = datetime.datetime.strptime(
                    o["inizio"], "%Y-%m-%dT%H:%M:%S")

                if inizio > start and inizio < stop:
                    l = Lesson(t.corso_codice, t.materia_codice, t.materia_descrizione, t.docente_nome, t.componente_id,
                               t.url,
                               datetime.datetime.strptime(
                                   o["inizio"], "%Y-%m-%dT%H:%M:%S"),
                               datetime.datetime.strptime(o["fine"], "%Y-%m-%dT%H:%M:%S"), t.anno, t.crediti, t.componente_padre)
                    for code in o["aula_codici"].split():
                        try:
                            a = all_aule[code]
                            l.add_aula(a)
                        except:
                            l.add_aula(Aula("-", "UNKNOWN AULA",
                                            "UNKNOWN ADDRESS", "", "NO LAT", "NO LON"))

                    timetable.add_lesson(l)
            except:
                traceback.print_exc()
                now = datetime.datetime.now()
                logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                             " ### EXCEPTION = " + traceback.format_exc())

    timetable.lessons.sort(key=lambda x: x.inizio, reverse=False)
    return timetable


def get_plan_timetable_web_api(day, plan):
    timetable = Timetable()

    if plan.is_empty():
        return timetable

    orari_table = "orari_" + accademic_year
    aule_table = "aule_" + accademic_year
    url_o = "https://dati.unibo.it/api/action/datastore_search_sql"
    url_a = "https://dati.unibo.it/api/action/datastore_search?resource_id=" + \
        aule_table + "&q="

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

    headers = {'Content-type': 'application/json',
               'Accept': 'application/json'}
    json_orari = requests.post(
        url_o, headers=headers, data='{"sql":'+'"'+sql_orari+'"}').text

    try:
        ok = json.loads(json_orari)["success"]
    except:
        pass

    if ok:

        orari_dict = json.loads(json_orari)["result"]["records"]
        for o in orari_dict:
            try:
                componente_id = o["componente_id"]

                t = plan.find_teaching_by_componente_id(componente_id)
                if t != None:
                    ##### DEBUG #####
                    # if t.componente_id == '448380':
                    #     print(t)
                    #################
                    l = Lesson(t.corso_codice, t.materia_codice, t.materia_descrizione, t.docente_nome, t.componente_id,
                               t.url,
                               datetime.datetime.strptime(
                                   o["inizio"], "%Y-%m-%dT%H:%M:%S"),
                               datetime.datetime.strptime(o["fine"], "%Y-%m-%dT%H:%M:%S"), t.anno, t.crediti, t.componente_padre)
                    for code in o["aula_codici"].split():
                        try:
                            a = all_aule[code]
                            l.add_aula(a)
                        except:
                            l.add_aula(Aula("-", "UNKNOWN AULA",
                                            "UNKNOWN ADDRESS", "", "NO LAT", "NO LON"))

                    timetable.add_lesson(l)
            except:
                traceback.print_exc()
                now = datetime.datetime.now()
                logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                             " ### EXCEPTION = " + traceback.format_exc())
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
                                        t["docente_nome"], t["componente_id"], t["url"], t["anno"], t["crediti"], t["componente_padre"])
                    plan.add_teaching(teaching)

                # to recover plans from componente_id
                except KeyError:
                    try:
                        teaching = all_teachings[t["componente_id"]]
                        plan.add_teaching(teaching)
                    except:
                        pass

                #####

                except:
                    traceback.print_exc()
                    now = datetime.datetime.now()
                    logging.info("TIMESTAMP = " + now.strftime(
                        "%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())
        return plan

    else:
        return None


def get_user(chat_id):
    if chat_id in users.keys():
        return users[chat_id]
    else:
        u = User(chat_id)
        users[chat_id] = u
        return u


def store_user(chat_id):
    if not os.path.isdir(dir_users_name):
        os.makedirs(dir_users_name)

    u = get_user(chat_id)

    with open(dir_users_name + str(chat_id), 'w') as outfile:
        user_dict = {}
        user_dict["chat_id"] = u.chat_id
        user_dict["mode"] = u.mode.name
        user_dict["notification"] = u.notificated
        outfile.write(json.dumps(user_dict))


def check_user(chat_id):
    u = get_user(chat_id)
    if os.path.isfile(dir_plans_name + str(chat_id)):
        u.mode = Mode.PLAN
    else:
        u.mode = Mode.NORMAL


def load_user(chat_id):
    if os.path.isfile(dir_users_name+str(chat_id)):
        with open(dir_users_name + str(chat_id), 'r') as f:
            user_dict = json.load(f)

    u = User(chat_id)
    for key in user_dict.keys():
        if key == 'chat_id':
            pass
        elif key == 'mode':
            u.mode = Mode[user_dict["mode"]]

        elif key == 'notification':
            u.notificated = user_dict["notification"]

    return u


def store_user_plan(chat_id, plan):
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### STORE PLAN OF USER " + str(chat_id))
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### STORE PLAN OF USER " + str(chat_id))
    if not os.path.isdir(dir_plans_name):
        os.mkdir(dir_plans_name)

    with open(dir_plans_name + str(chat_id), 'w') as outfile:
        outfile.write(json.dumps(plan, default=lambda x: x.__dict__))


def make_main_keyboard(chat_id):

    u = get_user(chat_id)

    buttonLists = list()
    for i in range(8):
        buttonLists.append(list())

    buttonLists[0].append(ALL_COURSES)
    buttonLists[1].append(MAKE_PLAN)
    if u.mode != Mode.NORMAL:
        if u.notificated:
            buttonLists[2].append(NOTIFY_OFF)
        else:
            buttonLists[2].append(NOTIFY_ON)
        buttonLists[3].append(MY_TIMETABLE)
        buttonLists[4].append(MY_PLAN)
        buttonLists[5].append(DEL_PLAN)

    buttonLists[6].append(HELP)
    buttonLists[6].append(DONATION)
    buttonLists[7].append(PRIVACY)

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
        c = all_courses_group_by_area[area][i]
        buttonLists[i + 1].append(c.corso_codice + " - " + c.corso_descrizione[:50] +
                                  " (" + c.sededidattica + ") - " + c.tipologia)

    buttonLists[len(all_courses_group_by_area[area]) + 1].append(BACK_TO_AREAS)
    buttonLists[len(all_courses_group_by_area[area]) + 1].append(BACK_TO_MAIN)
    if mode == Mode.MAKE_PLAN:
        buttonLists[0].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_year_keyboard(corso_codice, mode):
    buttonLists = list()
    c = all_courses[corso_codice]

    for i in range(0, c.durata + 2, 1):
        buttonLists.append(list())

    for i in range(0, c.durata, 1):
        buttonLists[i + 1].append(c.corso_codice + " - " + c.corso_descrizione[:50] +
                                  " (" + c.sededidattica + ")" + " - YEAR " + str(i+1))

    buttonLists[c.durata + 1].append(BACK_TO_AREAS)
    buttonLists[c.durata + 1].append(BACK_TO_MAIN)
    if mode == Mode.MAKE_PLAN:
        buttonLists[0].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def print_plan(chat_id, plan):
    result = emo_plan + " YOUR STUDY PLAN" + "\n\n"
    for t in plan.teachings:
        result += t.materia_codice + " - <b>" + t.materia_descrizione + "</b>"
        if t.docente_nome != "":
            result += " (<i>" + t.docente_nome + "</i>)"
        if t.crediti != None and t.crediti != "":
            result += " - "+t.crediti + " CFU "

        result += " [ /remove_" + t.componente_id + " ]"
        if t.url != "":
            result += " [ /url_" + t.componente_id + " ]"

        result += "\n\n"

    return result


def print_plan_message(chat_id, plan):
    result = list()
    for t in plan.teachings:
        t_string = t.materia_codice + " - <b>" + t.materia_descrizione + "</b>"
        if t.docente_nome != "":
            t_string += " (<i>" + t.docente_nome + "</i>)"
        if t.crediti != None and t.crediti != "":
            t_string += " - "+t.crediti + " CFU "

        t_string += " [ /remove_" + t.componente_id + " ]"
        if t.url != "":
            t_string += " [ /url_" + t.componente_id + " ]"
        t_string += "\n\n"

        result.append(t_string)

    return result


def print_teachings_message(chat_id, corso_codice, year):
    result = list()
    mode = get_user(chat_id).mode
    # if mode == Mode.NORMAL or mode == Mode.PLAN:

    #     for t in all_courses[corso_codice].teachings:
    #         if t.anno == year:
    #             t_string = t.materia_codice + " - <b>" + t.materia_descrizione + "</b>"
    #             if t.docente_nome != "":
    #                 t_string += " (<i>" + t.docente_nome + "</i>)"
    #             if t.crediti != None and t.crediti != "":
    #                 t_string += " - " + t.crediti + " CFU "

    #             t_string += " [ /schedule_" + t.componente_id + " ]"
    #             if t.url != "":
    #                 t_string += " [ /url_" + t.componente_id + " ]"

    #             t_string += "\n\n"
    #             result.append(t_string)

    if mode == Mode.MAKE_PLAN:

        for t in all_courses[corso_codice].teachings:
            if t.anno == None or int(t.anno) == year:

                t_string = t.materia_codice + " - <b>" + t.materia_descrizione + "</b>"
                if t.docente_nome != "":
                    t_string += " (<i>" + t.docente_nome + "</i>)"
                if t.crediti != None and t.crediti != "":
                    t_string += " - "+t.crediti + " CFU "

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
    next_week = day + datetime.timedelta(days=7)
    prec_week = day - datetime.timedelta(days=7)
    # keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #     [InlineKeyboardButton(text=emo_arrow_back + " " + 'Back', callback_data=prec_day.strftime("%d/%m/%YT%H:%M:%S")),
    #      InlineKeyboardButton(text='Next ' + emo_arrow_forward,
    #                           callback_data=next_day.strftime("%d/%m/%YT%H:%M:%S"))],
    #     [InlineKeyboardButton(text=emo_double_arrow_back + " " + 'Previous week',
    #                           callback_data=prec_week.strftime(
    #                               "%d/%m/%YT%H:%M:%S")),
    #      InlineKeyboardButton(text='Next week ' + emo_double_arrow_forward,
    #                           callback_data=next_week.strftime(
    #                               "%d/%m/%YT%H:%M:%S"))]
    # ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=emo_double_arrow_back,
                              callback_data=prec_week.strftime("%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(
             text=emo_arrow_back, callback_data=prec_day.strftime("%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(
             text=emo_arrow_forward, callback_data=next_day.strftime("%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text=emo_double_arrow_forward, callback_data=next_week.strftime("%d/%m/%YT%H:%M:%S"))]
    ])

    return keyboard


def make_inline_today_schedule_keyboard(chat_id, day, corso_codice, year):
    next_day = day + datetime.timedelta(days=1)
    prec_day = day - datetime.timedelta(days=1)
    next_week = day + datetime.timedelta(days=7)
    prec_week = day - datetime.timedelta(days=7)
    # keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #     [InlineKeyboardButton(text=emo_arrow_back + " " + 'Previous day',
    #                           callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + prec_day.strftime(
    #                               "%d/%m/%YT%H:%M:%S")),
    #      InlineKeyboardButton(text='Next day ' + emo_arrow_forward,
    #                           callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + next_day.strftime(
    #                               "%d/%m/%YT%H:%M:%S"))],
    #     [InlineKeyboardButton(text=emo_double_arrow_back + " " + 'Previous week',
    #                           callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + prec_week.strftime(
    #                               "%d/%m/%YT%H:%M:%S")),
    #         InlineKeyboardButton(text='Next week ' + emo_double_arrow_forward,
    #                              callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + next_week.strftime(
    #                                  "%d/%m/%YT%H:%M:%S"))]
    # ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=emo_double_arrow_back,
                              callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + prec_week.strftime(
                                  "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(
             text=emo_arrow_back,  callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + prec_day.strftime(
                 "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(
             text=emo_arrow_forward, callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + next_day.strftime(
                 "%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text=emo_double_arrow_forward, callback_data="course_" + corso_codice + "_year_"+str(year)+"_" + next_week.strftime(
             "%d/%m/%YT%H:%M:%S"))]
    ])

    return keyboard


# def make_inline_teaching_schedule_keyboard(chat_id, day, componente_id):
#     next_day = day + datetime.timedelta(days=1)
#     prec_day = day - datetime.timedelta(days=1)
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=emo_arrow_back + " " + 'Back',
#                               callback_data="schedule_" + componente_id + "_" + prec_day.strftime(
#                                   "%d/%m/%YT%H:%M:%S")),
#          InlineKeyboardButton(text='Next ' + emo_arrow_forward,
#                               callback_data="schedule_" + componente_id + "_" + next_day.strftime(
#                                   "%d/%m/%YT%H:%M:%S"))]
#     ])

#     return keyboard


def on_callback_query(msg):
    query_id, chat_id, query_data = telepot.glance(
        msg, flavor='callback_query')
    try:
        msg_edited = (chat_id, msg['message']['message_id'])

        # if (query_data.startswith("schedule")):

        #     array = query_data.split("_")
        #     componente_id = array[1]
        #     day_string = array[len(array) - 1]

        #     day = datetime.datetime.strptime(day_string, "%d/%m/%YT%H:%M:%S")

        #     plan = Plan()
        #     teaching = all_teachings[componente_id]

        #     plan.add_teaching(teaching)

        #     timetable = get_plan_timetable(day, plan)

        #     output_string = emo_ay + " A.Y. <code>" + accademic_year + \
        #         "/" + str(int(accademic_year) + 1) + "</code>\n"
        #     output_string += emo_calendar + " " + \
        #         day.strftime("%A %B %d, %Y") + "\n\n"
        #     output_string += print_output_timetable(timetable)

        #     try:
        #         bot.editMessageText(msg_edited, output_string, parse_mode='HTML',
        #                             reply_markup=make_inline_teaching_schedule_keyboard(chat_id, day, teaching.componente_id))
        #         # bot.answerCallbackQuery(query_id, text="")
        #     except telepot.exception.TelegramError:
        #         bot.answerCallbackQuery(query_id, text="SLOW DOWN!!")
        #         pass

        if (query_data.startswith("course")):

            array = query_data.split("_")
            corso_codice = array[1]
            year = int(array[3])
            day_string = array[len(array) - 1]

            day = datetime.datetime.strptime(day_string, "%d/%m/%YT%H:%M:%S")

            course = all_courses[corso_codice]
            plan = Plan()
            for t in course.teachings:
                if t.anno == None or int(t.anno) == year:
                    plan.add_teaching(t)

            timetable = get_plan_timetable(day, plan)

            output_string = emo_ay + " A.Y. <code>" + accademic_year + \
                "/" + str(int(accademic_year) + 1) + "</code>\n"
            output_string += emo_calendar + " " + \
                day.strftime("%A %B %d, %Y") + "\n\n"
            output_string += print_output_timetable(timetable)

            try:
                bot.editMessageText(msg_edited, output_string, parse_mode='HTML',
                                    reply_markup=make_inline_today_schedule_keyboard(chat_id, day, course.corso_codice, year))
                # bot.answerCallbackQuery(query_id, text="")
            except telepot.exception.TelegramError:
                bot.answerCallbackQuery(query_id, text="SLOW DOWN!!")
                pass

        else:
            day = datetime.datetime.strptime(query_data, "%d/%m/%YT%H:%M:%S")
            plan = load_user_plan(chat_id)

            if plan != None:

                timetable = get_plan_timetable(day, plan)

                output_string = emo_ay + " A.Y. <code>" + accademic_year + \
                    "/" + str(int(accademic_year) + 1) + "</code>\n"
                output_string += emo_calendar + " " + \
                    day.strftime("%A %B %d, %Y") + "\n\n"
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

        output_string = emo_wrong + " Oh no! Something bad happend.."

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

                output_string = "Hi! Thanks for trying this bot!\n\n" + help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif chat_id not in users.keys():
                check_user(chat_id)
                store_user(chat_id)

                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your action!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == '/help':

                output_string = help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == ALL_COURSES:
                u = get_user(chat_id)

                store_user(chat_id)

                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your area!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_area_keyboard(u.mode))

            elif msg["text"] == MY_TIMETABLE:
                get_user(chat_id).mode = Mode.PLAN
                store_user(chat_id)

                now = datetime.datetime.now()

                ##### DEBUG #####
                #  now = datetime.datetime.strptime("29/05/2019", "%d/%m/%Y")
                #################
                plan = load_user_plan(chat_id)

                if plan != None:

                    timetable = get_plan_timetable(now, plan)
                    output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                        int(accademic_year) + 1) + "</code>\n"
                    output_string += emo_calendar + " " + \
                        now.strftime("%A %B %d, %Y") + "\n\n"

                    output_string += print_output_timetable(timetable)

                    bot.sendMessage(chat_id, important_string,
                                    parse_mode='HTML')
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_inline_timetable_keyboard(now))

                else:
                    output_string = "You haven't a study plan yet! Use " + MAKE_PLAN + " to make it"
                    get_user(chat_id).mode = Mode.NORMAL
                    store_user(chat_id)
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == MY_PLAN:
                get_user(chat_id).mode = Mode.PLAN
                store_user(chat_id)

                plan = load_user_plan(chat_id)
                if plan != None:
                    string_list = print_plan_message(chat_id, plan)

                    i = 0
                    output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                        int(accademic_year) + 1) + "</code>\n"
                    output_string += emo_plan + " YOUR STUDY PLAN" + "\n\n"

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
                    output_string = "You haven't a study plan yet! Use " + MAKE_PLAN + " to make it"
                    get_user(chat_id).mode = Mode.NORMAL
                    store_user(chat_id)
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == DEL_PLAN:

                get_user(chat_id).mode = Mode.DEL

                output_string = "Are you sure? Send \"<b>YES</b>\" to confirm or \"<b>NO</b>\" to cancel (without quotes)"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML')

            elif msg["text"].upper() == "YES" and get_user(chat_id).mode == Mode.DEL:

                get_user(chat_id).mode = Mode.NORMAL
                store_user(chat_id)

                if os.path.isfile(dir_plans_name + str(chat_id)):
                    os.remove(dir_plans_name + str(chat_id))

                output_string = "Your study plan was deleted!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == "NO" and get_user(chat_id).mode == Mode.DEL:
                get_user(chat_id).mode = Mode.PLAN
                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your action!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == MAKE_PLAN:
                u = get_user(chat_id)
                u.mode = Mode.MAKE_PLAN
                store_user(chat_id)

                if not os.path.isfile(dir_plans_name + str(chat_id)):
                    plan = Plan()
                    store_user_plan(chat_id, plan)

                output_string = "Find your teachings and add them to your study plan. Send " + \
                    END_PLAN + " when you have finished!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_area_keyboard(u.mode))

            elif msg["text"] == END_PLAN:
                u = get_user(chat_id)
                u.mode = Mode.PLAN
                store_user(chat_id)
                plan = load_user_plan(chat_id)
                store_user_plan(chat_id, plan)

                output_string = "Well done! Now you can use " + MY_PLAN + \
                    " to see your study plan and " + MY_TIMETABLE + " to get your lessons shedules!"
                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == BACK_TO_MAIN:
                check_user(chat_id)
                store_user(chat_id)

                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your action!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == BACK_TO_AREAS:
                u = get_user(chat_id)
                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your area!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_area_keyboard(u.mode))

            elif msg["text"] == NOTIFY_ON:
                u = get_user(chat_id)

                if os.path.isfile(dir_plans_name + str(chat_id)):
                    u.notificated = True
                    store_user(chat_id)

                    output_string = "Notifications enabled!"

                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))
                else:
                    output_string = "You haven't a study plan yet! Use " + MAKE_PLAN + " to make it"
                    get_user(chat_id).mode = Mode.NORMAL
                    store_user(chat_id)
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == NOTIFY_OFF:
                u = get_user(chat_id)

                if u.notificated:
                    u.notificated = False
                    store_user(chat_id)

                    output_string = "Notifications disabled!"

                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))
                else:
                    output_string = "Notifications already disabled!"

                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == DONATION:
                check_user(chat_id)
                store_user(chat_id)

                bot.sendMessage(chat_id, donation_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == HELP:

                check_user(chat_id)
                store_user(chat_id)

                bot.sendMessage(chat_id, help_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] == PRIVACY:
                check_user(chat_id)
                store_user(chat_id)

                bot.sendMessage(chat_id, privacy_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))

            elif msg["text"] in all_courses_group_by_area.keys():
                u = get_user(chat_id)

                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += "Choose your course!"

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_courses_keyboard(msg["text"], u.mode))

            elif msg["text"].split()[0] in all_courses.keys():
                course = all_courses[msg["text"].split()[0]]
                u = get_user(chat_id)
                try:

                    year = int(msg["text"].split()[-1])
                    if u.mode == Mode.MAKE_PLAN:

                        string_list = print_teachings_message(
                            chat_id, course.corso_codice, year)

                        i = 0
                        output_string = "<b>TEACHINGS " + \
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

                        timetable = get_plan_timetable(now, plan)

                        output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                            int(accademic_year) + 1) + "</code>\n"
                        output_string += emo_calendar + " " + \
                            now.strftime("%A %B %d, %Y") + "\n\n"

                        output_string += print_output_timetable(timetable)

                        bot.sendMessage(chat_id, important_string,
                                        parse_mode='HTML')
                        bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                        reply_markup=make_inline_today_schedule_keyboard(chat_id, now, course.corso_codice, year))

                    else:
                        check_user(chat_id)
                        store_user(chat_id)

                except ValueError:

                    output_string = emo_ay + " A.Y. <code>" + accademic_year + \
                        "/" + str(int(accademic_year) + 1) + "</code>\n"
                    output_string += "<b>SELECTED COURSE:\n" + \
                        str(course)+"</b>\n\n"

                    if course.url != "":
                        output_string += "WEB SITE -> " + emo_url + " " + course.url+"\n\n"

                    output_string += "Choose your year!"

                    bot.sendMessage(chat_id, output_string, parse_mode='HTML', disable_web_page_preview=True, reply_markup=make_year_keyboard(
                        course.corso_codice, get_user(chat_id).mode))

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

            # elif msg["text"].startswith("/schedule_"):

            #     array = msg["text"].split("_")
            #     componente_id = array[1]

            #     if componente_id in all_teachings.keys():
            #         plan = Plan()
            #         teaching = all_teachings[componente_id]

            #         plan.add_teaching(teaching)

            #         now = datetime.datetime.now()

            #         ##### DEBUG #####
            #         # now = datetime.datetime.strptime("29/05/2019", "%d/%m/%Y")
            #         #################

            #         timetable = get_plan_timetable(now, plan)

            #         output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
            #             int(accademic_year) + 1) + "</code>\n"
            #         output_string += emo_calendar + " " + \
            #             now.strftime("%A %B %d, %Y") + "\n\n"

            #         output_string += print_output_timetable(timetable)

            #         # bot.sendMessage(chat_id, donation_string, parse_mode='HTML')
            #         bot.sendMessage(chat_id, output_string, parse_mode='HTML',
            #                         reply_markup=make_inline_teaching_schedule_keyboard(chat_id, now, teaching.componente_id))

            elif msg["text"].startswith("/url_"):

                array = msg["text"].split("_")
                componente_id = array[1]

                if componente_id in all_teachings.keys():
                    output_string = emo_url + " " + \
                        all_teachings[componente_id].url

                    bot.sendMessage(
                        chat_id, output_string, disable_web_page_preview=True, parse_mode='HTML')

            else:
                check_user(chat_id)
                store_user(chat_id)

                output_string = emo_confused + " Sorry.. I don't understand.."
                output_string += "\n\n" + help_string

                bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                reply_markup=make_main_keyboard(chat_id))
        else:

            check_user(chat_id)
            store_user(chat_id)

            output_string = emo_confused + " Sorry.. I don't understand.."
            output_string += "\n\n" + help_string
            bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                            reply_markup=make_main_keyboard(chat_id))
    except:
        traceback.print_exc()
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### EXCEPTION from " + str(chat_id)+" = " + traceback.format_exc())
        output_string = emo_wrong + " Oh no! Something bad happend.."
        bot.sendMessage(chat_id, output_string,
                        reply_markup=make_main_keyboard(chat_id))


def download_csv_orari():
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### DOWNLOADING CSV ORARI")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          "  ### DOWNLOADING CSV ORARI")

    if os.path.isfile(current_dir+"orari_"+accademic_year+".csv"):
        os.remove(current_dir+"orari_"+accademic_year+".csv")

    url_orari_csv = "https://dati.unibo.it/dataset/course-timetable-"+accademic_year + \
        "/resource/orari_"+accademic_year+"/download/orari_"+accademic_year+".csv"

    csv_orari_filename = wget.download(
        url_orari_csv, current_dir+"orari_"+accademic_year+".csv")

    orari.clear()

    with open(csv_orari_filename) as f:
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            o = {}
            o["componente_id"] = row[0]
            o["inizio"] = ''.join(row[1].split("+")[0])
            o["fine"] = ''.join(row[2].split("+")[0])
            o["aula_codici"] = row[3]
            orari[o["componente_id"]].append(o)


def check_table(table):
    url = "https://dati.unibo.it/api/action/datastore_search_sql?sql="

    sql = "SELECT * FROM " + table + " limit 1"

    json_response = requests.get(url + sql).text
    ok = json.loads(json_response)["success"]

    now = datetime.datetime.now()
    if ok:
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### TABLE " + table + " PRESENT")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
              " ### TABLE " + table + " PRESENT")
        return True
    else:
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                     " ### TABLE " + table + " NOT PRESENT")
        print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
              " ### TABLE " + table + " NOT PRESENT")
        return False


def update():
    now = datetime.datetime.now()
    global accademic_year
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
        accademic_year = year
    else:
        accademic_year = str(int(year) - 1)

    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### SET ACCADEMIC YEAR TO " + accademic_year)
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### SET ACCADEMIC YEAR TO " + accademic_year)

    # check existence table

    corsi_table = "corsi_" + accademic_year + "_it"
    insegnamenti_table = "insegnamenti_" + accademic_year + "_it"
    orari_table = "orari_" + accademic_year
    aule_table = "aule_" + accademic_year

    if check_table(corsi_table) and check_table(insegnamenti_table):
        get_all_courses()

    if check_table(aule_table):
        get_all_aule()

    if check_table(orari_table):
        download_csv_orari()


def send_good_morning():
    for chat_id in users.keys():
        try:
            u = get_user(chat_id)

            if u.notificated:
                now = datetime.datetime.now()

                plan = load_user_plan(chat_id)

                timetable = get_plan_timetable(now, plan)
                output_string = emo_ay + " A.Y. <code>" + accademic_year + "/" + str(
                    int(accademic_year) + 1) + "</code>\n"
                output_string += emo_calendar + " " + \
                    now.strftime("%A %B %d, %Y") + "\n\n"

                output_string += print_output_timetable(timetable)
                if "NO LESSONS FOR TODAY" not in output_string:
                    logging.info(
                        "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### SENDING GOOD MORNING TO " + str(chat_id))
                    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + "  ### SENDING GOOD MORNING TO " + str(
                        chat_id))

                    # bot.sendMessage(chat_id, donation_string, parse_mode='HTML')
                    bot.sendMessage(chat_id, output_string, parse_mode='HTML',
                                    reply_markup=make_inline_timetable_keyboard(now))

        except:
            traceback.print_exc()
            now = datetime.datetime.now()
            logging.info(
                "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())


if os.path.isdir(dir_users_name):
    for f in os.listdir(dir_users_name):
        filename = os.fsdecode(f)
        u = load_user(int(filename))
        users[u.chat_id] = u


update()
schedule.every().day.at("06:30").do(update)
schedule.every().monday.at("08:45").do(send_good_morning)
schedule.every().thursday.at("08:45").do(send_good_morning)
schedule.every().wednesday.at("08:45").do(send_good_morning)
schedule.every().thursday.at("08:45").do(send_good_morning)
schedule.every().friday.at("08:45").do(send_good_morning)
MessageLoop(bot, {'chat': on_chat_message,
                  'callback_query': on_callback_query}).run_as_thread()

print('Listening ...')
# Keep the program running.
while 1:
    schedule.run_pending()
    time.sleep(1)
