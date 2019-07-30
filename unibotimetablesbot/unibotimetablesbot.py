import operator
import os
import collections
import sys
import traceback
import datetime
import logging
import json
import requests
import time
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from threading import Lock
from model import Course, Teaching, Mode, Plan, Lesson, Aula, Timetable

# token = os.environ['BOT_TOKEN']

token = "868250356:AAE2ZsD4zwgr6y3K4vboCA57CNaO3ZPMFrs"

bot = telepot.Bot(token)

donation_string = "Se ti è piacuto questo bot e vuoi sostenerlo puoi fare una donazione qui! -> https://www.paypal.me/lucaant"

current_dir = "./"
# current_dir = "/bot/unibotimetablesbot/"

logging.basicConfig(filename=current_dir + "unibotimetablesbot.log", level=logging.INFO)

dir_data_name = current_dir + 'data/'

writer_lock = Lock()

users_plans = dict()
all_courses = dict()
all_courses_group_by_area = collections.defaultdict(list)
accademic_year = "2018"

users_mode = collections.defaultdict(Mode)

ALL_COURSES = "ALL COURSES"
MY_TIMETABLE = "MY TIMETABLE"
MAKE_PLAN = "MAKE YOUR PLAN"
END_PLAN = "PLAN TERMINATE"
BACK_TO_AREAS = "BACK TO AREAS"
BACK_TO_MAIN_MENU = "BACK TO MAIN MENU"


def get_all_courses():
    url = "https://dati.unibo.it/api/action/datastore_search_sql?sql="
    corsi_table = "corsi_" + accademic_year + "_it"
    insegnamenti_table = "insegnamenti_" + accademic_year + "_it"
    #    sql_string = "SELECT "+ insegnamenti_table + ".docente_nome, "+ insegnamenti_table + ".materia_codice, "+ insegnamenti_table + ".materia_descrizione, " + corsi_table + ".corso_codice, "+ insegnamenti_table + ".url, "+ corsi_table + ".tipologia, "  + corsi_table+ ".corso_descrizione, "+ corsi_table+ ".sededidattica"+" FROM " + corsi_table + ", " + insegnamenti_table + " WHERE " + corsi_table + ".corso_codice=" + insegnamenti_table + ".corso_codice"
    sql_insegnamenti = "SELECT * FROM " + insegnamenti_table
    sql_corsi = "SELECT * FROM " + corsi_table

    json_corsi = requests.get(url + sql_corsi).text
    json_insegnamenti = requests.get(url + sql_insegnamenti).text

    corsi = json.loads(json_corsi)["result"]["records"]
    insegnamenti = json.loads(json_insegnamenti)["result"]["records"]
    for c in corsi:
        course = Course(c["corso_codice"], c["corso_descrizione"], c["tipologia"], c["sededidattica"], c["ambiti"])
        all_courses[course.corso_codice] = course
        all_courses_group_by_area[course.ambiti].append(course)

    for i in insegnamenti:
        teaching = Teaching(i["corso_codice"], i["materia_codice"], i["materia_descrizione"], i["docente_nome"],
                            i["componente_id"],
                            i["url"])

        try:
            all_courses[teaching.corso_codice].add_teaching(teaching)
        except KeyError:
            pass


#    for c in all_courses.values():
#        print("\n\n"+str(c))
#        for i in c.teachings:
#            print(i)


def get_plan_timetable(plan):
    timetable = Timetable()
    orari_table = "orari_" + accademic_year
    aule_table = "aule_" + accademic_year
    url_o = "https://dati.unibo.it/api/action/datastore_search_sql?sql="
    url_a = "https://dati.unibo.it/api/action/datastore_search?resource_id=" + aule_table + "&q="

    dt = datetime.datetime.now()

    # debug
    dt = datetime.datetime.strptime("2019-05-29T09:00:00", "%Y-%m-%dT%H:%M:%S")

    sql_orari = "SELECT " + orari_table + ".inizio, " \
                + orari_table + ".fine, " \
                + orari_table + ".aula_codici, " \
                + orari_table + ".componente_id " \
                + " FROM " + orari_table \
                + " WHERE " + orari_table + ".inizio between \'" + dt.strftime(
        "%Y/%m/%d") + " 00:00:00\' and " + "\'" + dt.strftime("%Y/%m/%d") + " 23:59:59\' AND ("

    for i in range(0, len(plan.teachings), 1):
        t = plan.teachings[i]
        if i == 0:
            sql_orari += orari_table + ".componente_id=" + t.componente_id
        else:
            sql_orari += " OR " + orari_table + ".componente_id=" + t.componente_id
    sql_orari += " )"
    json_orari = requests.get(url_o + sql_orari).text
    orari = json.loads(json_orari)["result"]["records"]
    for o in orari:
        componente_id = o["componente_id"]

        t = plan.find_teaching_by_componente_id(componente_id)
        if t != None:
            l = Lesson(t.corso_codice, t.materia_codice, t.materia_descrizione, t.docente_nome, t.componente_id, t.url,
                       datetime.datetime.strptime(o["inizio"], "%Y-%m-%dT%H:%M:%S"),
                       datetime.datetime.strptime(o["fine"], "%Y-%m-%dT%H:%M:%S"))
            for code in o["aula_codici"].split():
                json_aula = requests.get(url_a + code).text
                aula = json.loads(json_aula)["result"]["records"][0]
                a = Aula(aula["aula_codice"], aula["aula_nome"], aula["aula_indirizzo"], aula["aula_piano"],
                         aula["lat"],
                         aula["lot"])
                l.add_aula(a)
            timetable.add_lesson(l)
    return timetable


# return a json as a dict
def load_users_plans():
    if os.path.isdir(dir_data_name):
        for filename in os.listdir(dir_data_name):
            with open(filename) as f:
                plan = json.load(f)
                users_plans["filename"] = plan


def store_user_plan(chat_id, plan):
    if not os.path.isdir(dir_data_name):
        os.mkdir(dir_data_name)

    with open(dir_data_name + chat_id, 'w') as outfile:
        outfile.write(json.dumps(plan.__dict__))


def make_main_keyboard(mode):
    buttonLists = list()

    buttonLists.append(list())
    buttonLists.append(list())
    buttonLists.append(list())

    buttonLists[0].append(ALL_COURSES)
    buttonLists[1].append(MY_TIMETABLE)
    buttonLists[2].append(MAKE_PLAN)
    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_area_keyboard(mode):
    buttonLists = list()

    for i in range(0, len(all_courses_group_by_area.keys()) + 2, 1):
        buttonLists.append(list())

    for i in range(0, len(all_courses_group_by_area.keys()), 1):
        buttonLists[i].append(list(all_courses_group_by_area.keys())[i])

    buttonLists[len(all_courses_group_by_area.keys())].append(BACK_TO_MAIN_MENU)
    if mode == Mode.MAKE_PLAN:
        buttonLists[len(all_courses_group_by_area.keys())].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_courses_keyboard(area, mode):
    buttonLists = list()

    for i in range(0, len(all_courses_group_by_area[area]) + 2, 1):
        buttonLists.append(list())

    for i in range(0, len(all_courses_group_by_area[area]), 1):
        buttonLists[i].append(str(all_courses_group_by_area[area][i]))

    buttonLists[len(all_courses_group_by_area[area])].append(BACK_TO_AREAS)
    if mode == Mode.MAKE_PLAN:
        buttonLists[len(all_courses_group_by_area[area])].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_teachings_keyboard(code, mode):
    buttonLists = list()

    for i in range(0, len(all_courses[code].teachings) + 2, 1):
        buttonLists.append(list())

    for i in range(0, len(all_courses[code].teachings), 1):
        buttonLists[i].append(str(all_courses[code].teachings[i]))

    buttonLists[len(all_courses[code].teachings)].append(BACK_TO_AREAS)

    if mode == Mode.MAKE_PLAN:
        buttonLists[len(all_courses[code].teachings) + 1].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def on_chat_message(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(msg)
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### MESSAGGIO = " + repr(msg))

        if content_type == "text":
            if msg["text"] == '/start':
                users_mode[chat_id] = Mode.NORMAL
                output_string = "Benvenuto! Puoi usare questo bot per visualizzare velocemente le tue prossime lezioni presso l'Unibo"

                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(users_mode[chat_id]))


            elif msg["text"] == '/help':
                users_mode[chat_id] = Mode.NORMAL

                output_string = "Scegli la tua facoltà dal menù qui sotto. Poi scegli il tuo corso e riceverai in risposta dal bot le tue lezioniper le prissime 24 ore!\nPer problemi e malfunzionamenti inviare una mail a luca.ant96@libero.it descrivendo dettagliatamente il problema."

                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(users_mode[chat_id]))

            elif msg["text"] == ALL_COURSES:
                users_mode[chat_id] = Mode.NORMAL

                output_string = "Scegli l'orario da visualizzare"

                bot.sendMessage(chat_id, donation_string)
                bot.sendMessage(chat_id, output_string, reply_markup=make_area_keyboard(users_mode[chat_id]))
            elif msg["text"] == MY_TIMETABLE:
                users_mode[chat_id] = Mode.NORMAL

                timetable = get_plan_timetable(users_plans[chat_id])
                output_string = str(timetable)
                bot.sendMessage(chat_id, donation_string)
                bot.sendMessage(chat_id, output_string, reply_markup=make_area_keyboard(users_mode[chat_id]))


            elif msg["text"] == MAKE_PLAN:
                users_mode[chat_id] = Mode.MAKE_PLAN

                output_string = "Choose your teachings and make your study plan. Send " + END_PLAN + "when you have finisched!"
                bot.sendMessage(chat_id, output_string)
                bot.sendMessage(chat_id, output_string, reply_markup=make_area_keyboard(users_mode[chat_id]))

            elif msg["text"] == END_PLAN:
                users_mode[chat_id] = Mode.NORMAL
                output_string = "Well done! Now you can use \"" + MY_TIMETABLE + "\" to see your shedules."
                bot.sendMessage(chat_id, output_string)
                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(users_mode[chat_id]))

            elif msg["text"] == BACK_TO_MAIN_MENU:

                output_string = "Choose"

                bot.sendMessage(chat_id, donation_string)
                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(users_mode[chat_id]))
            elif msg["text"] == BACK_TO_AREAS:

                output_string = "Choose your area"

                bot.sendMessage(chat_id, donation_string)
                bot.sendMessage(chat_id, output_string, reply_markup=make_area_keyboard(users_mode[chat_id]))
            elif msg["text"] in all_courses_group_by_area.keys():

                output_string = "Choose your course"

                bot.sendMessage(chat_id, donation_string)
                bot.sendMessage(chat_id, output_string,
                                reply_markup=make_courses_keyboard(msg["text"], users_mode[chat_id]))

            elif msg["text"].split()[0] in all_courses.keys():

                if users_mode[chat_id] == Mode.NORMAL:

                    course = all_courses[msg["text"].split()[0]]
                    plan = Plan()
                    plan.set_teachings(course.teachings)
                    timetable = get_plan_timetable(plan)
                    timetable.lessons.sort(key=lambda x: x.inizio, reverse=False)
                    output_string = str(timetable)
                    bot.sendMessage(chat_id, output_string, reply_markup=make_area_keyboard(users_mode[chat_id]))

                elif users_mode[chat_id] == Mode.MAKE_PLAN:

                    output_string = "Choose a teaching to add to your plan."
                    bot.sendMessage(chat_id, output_string,
                                    reply_markup=make_teachings_keyboard(msg["text"].split()[0], users_mode[chat_id]))

            else:
                output_string = "Choose"

                bot.sendMessage(chat_id, donation_string)
                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(users_mode[chat_id]))
        else:

            output_string = "Non ho capito...\nScegli la tua facoltà"

            bot.sendMessage(chat_id, donation_string)
            bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(users_mode[chat_id]))
    except:
        traceback.print_exc()
        output_string = traceback.format_exc()
        bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(users_mode[chat_id]))


get_all_courses()
load_users_plans()
MessageLoop(bot, {'chat': on_chat_message}).run_as_thread()

print('Listening ...')
# Keep the program running.
while 1:
    time.sleep(10)
