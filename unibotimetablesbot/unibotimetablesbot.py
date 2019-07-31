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
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from threading import Lock
from model import Course, Teaching, Mode, Plan, Lesson, Aula, Timetable

# token = os.environ['BOT_TOKEN']

token = "868250356:AAE2ZsD4zwgr6y3K4vboCA57CNaO3ZPMFrs"

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

ALL_COURSES = emo_courses + " " + "ALL COURSES"
MY_TIMETABLE = emo_timetable + " " + "MY TIMETABLE"
MY_PLAN = emo_plan + " " + "MY STUDY PLAN"
MAKE_PLAN = emo_make + " " + "MAKE MY STUDY PLAN"
DEL_PLAN = emo_del + " " + "DELETE MY STUDY PLAN"
END_PLAN = emo_end_plan + " " + "SAVE STUDY PLAN"
BACK_TO_AREAS = emo_back + " " + "BACK TO AREAS"
BACK_TO_MAIN = emo_back + " " + "BACK TO MAIN"

donation_string =  emo_money +" Do you like this bot? If you want to support it you can make a donation here!  -> https://www.paypal.me/lucaant"
help_string = "Use:\n\n" + ALL_COURSES + " to see all teachings' timetables\n\n" + MAKE_PLAN + " to build your study plan\n\nThen you can use:\n\n" + MY_PLAN + " to see your study plan\n\n" + MY_TIMETABLE + " to get your personal lesson's schedules\n\n" + DEL_PLAN + " to delete your plan" + "\n\nFor issues send a mail to luca.ant96@libero.it describing the problem in detail."

current_dir = "./"
# current_dir = "/bot/unibotimetablesbot/"

logging.basicConfig(filename=current_dir + "unibotimetablesbot.log", level=logging.INFO)

dir_plans_name = current_dir + 'plans/'
users_file = current_dir + 'users'

writer_lock = Lock()

users_plans = collections.defaultdict(Plan)
all_courses = dict()
all_teachings = dict()
all_courses_group_by_area = collections.defaultdict(list)
users_mode = collections.defaultdict(Mode)

accademic_year = "2018"


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


#    for c in all_courses.values():
#        print("\n\n"+str(c))
#        for i in c.teachings:
#            print(i)


def get_plan_timetable(day, plan):
    timetable = Timetable()
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
    try:
        json_orari = requests.get(url_o + sql_orari).text
        orari = json.loads(json_orari)["result"]["records"]
    except:
        return timetable

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
    timetable.lessons.sort(key=lambda x: x.inizio, reverse=False)
    return timetable


def load_users_plans():
    if os.path.isfile(users_file):
        with open(users_file) as f:
            chat_id = int(f.readline().replace("'", " ").strip())
            users_mode[chat_id] = Mode.NORMAL

    if os.path.isdir(dir_plans_name):
        for filename in os.listdir(dir_plans_name):
            with open(dir_plans_name + filename) as f:
                try:
                    plan_dict = json.load(f)
                    plan = Plan()
                    for t in plan_dict["teachings"]:
                        teaching = collections.namedtuple("Teaching", t.keys())(*t.values())
                        plan.add_teaching(teaching)
                    users_plans[int(filename)] = plan
                except:
                    traceback.print_exc()
                    now = datetime.datetime.now()
                    logging.info("TIMESTAMP = " + now.strftime(
                        "%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())


def store_user_plan(chat_id, plan):
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

    buttonLists[0].append(ALL_COURSES)
    if chat_id in users_plans.keys():
        buttonLists[1].append(MY_TIMETABLE)
        buttonLists[2].append(MY_PLAN)
        buttonLists[3].append(DEL_PLAN)
    else:
        buttonLists[1].append(MAKE_PLAN)
    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_area_keyboard(mode):
    buttonLists = list()

    for i in range(0, len(all_courses_group_by_area.keys()) + 2, 1):
        buttonLists.append(list())

    for i in range(0, len(all_courses_group_by_area.keys()), 1):
        buttonLists[i].append(list(all_courses_group_by_area.keys())[i])

    buttonLists[len(all_courses_group_by_area.keys())].append(BACK_TO_MAIN)
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
    buttonLists[len(all_courses_group_by_area[area])].append(BACK_TO_MAIN)
    if mode == Mode.MAKE_PLAN:
        buttonLists[len(all_courses_group_by_area[area])+1].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def make_teachings_keyboard(code, mode):
    buttonLists = list()

    for i in range(0, len(all_courses[code].teachings) + 2, 1):
        buttonLists.append(list())

    for i in range(0, len(all_courses[code].teachings), 1):
        buttonLists[i].append(str(all_courses[code].teachings[i]))

    buttonLists[len(all_courses[code].teachings)].append(BACK_TO_AREAS)
    buttonLists[len(all_courses[code].teachings)].append(BACK_TO_MAIN)

    if mode == Mode.MAKE_PLAN:
        buttonLists[len(all_courses[code].teachings)+1].append(END_PLAN)

    keyboard = ReplyKeyboardMarkup(keyboard=buttonLists, resize_keyboard=True)
    return keyboard


def print_output_timetable(timetable):
    output_string = str(timetable)
    if output_string == "":
        output_string = "NO LESSONS FOR TODAY"
    return output_string


def make_inline_keyboard(day):
    next_day = day + datetime.timedelta(days=1)
    prec_day = day - datetime.timedelta(days=1)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=emo_arrow_back + " " + 'Back', callback_data=prec_day.strftime("%d/%m/%YT%H:%M:%S")),
         InlineKeyboardButton(text='Next '+emo_arrow_forward,
                              callback_data=next_day.strftime("%d/%m/%YT%H:%M:%S"))]
    ])
    return keyboard


def on_callback_query(msg):
    query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
    try:

        msg_edited = (chat_id, msg['message']['message_id'])

        day = datetime.datetime.strptime(query_data, "%d/%m/%YT%H:%M:%S")
        timetable = get_plan_timetable(day, users_plans[chat_id])
        print(day)
        print(users_plans[chat_id])
        output_string = day.strftime("%d/%m/%Y") + "\n\n"
        output_string += print_output_timetable(timetable)
        try:
            bot.editMessageText(msg_edited, output_string, reply_markup=make_inline_keyboard(day))
            # bot.answerCallbackQuery(query_id, text="TRACKING STARTED!")
        except telepot.exception.TelegramError:
            pass

    except:
        traceback.print_exc()
        output_string = traceback.format_exc()
        bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))


def on_chat_message(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(msg)
        now = datetime.datetime.now()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### MESSAGGIO = " + str(msg))
        if content_type == "text":
            if msg["text"] == '/start':
                users_mode[chat_id] = Mode.NORMAL

                writer_lock.acquire()
                with open(users_file, "w") as f:
                    for u in users_mode.keys():
                        f.writelines(str(u))
                writer_lock.release()

                output_string = "Hi! Thanks to try this bot!\n" + help_string

                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))


            elif msg["text"] == '/help':
                users_mode[chat_id] = Mode.NORMAL

                output_string = help_string

                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))

            elif msg["text"] == ALL_COURSES:
                users_mode[chat_id] = Mode.NORMAL

                output_string = "Choose your area!"

                bot.sendMessage(chat_id, output_string, reply_markup=make_area_keyboard(users_mode[chat_id]))

            elif msg["text"] == MY_TIMETABLE:
                users_mode[chat_id] = Mode.NORMAL

                now = datetime.datetime.now()

                ############################# DEBUG ########################################
                now = datetime.datetime.strptime("2019-05-29T09:00:00", "%Y-%m-%dT%H:%M:%S")
                ############################################################################

                timetable = get_plan_timetable(now, users_plans[chat_id])
                output_string = emo_calendar +" "+now.strftime("%d/%m/%Y") + "\n\n"
                output_string += print_output_timetable(timetable)

                bot.sendMessage(chat_id, donation_string)
                bot.sendMessage(chat_id, output_string, reply_markup=make_inline_keyboard(now))

            elif msg["text"] == MY_PLAN:
                users_mode[chat_id] = Mode.NORMAL

                if chat_id in users_plans.keys():
                    plan = users_plans[chat_id]
                    output_string = str(plan)
                    bot.sendMessage(chat_id, donation_string)
                    bot.sendMessage(chat_id, output_string,
                                    reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))

            elif msg["text"] == DEL_PLAN:

                users_mode[chat_id] = Mode.NORMAL
                users_plans.pop(chat_id)

                if os.path.isfile(dir_plans_name + str(chat_id)):
                    os.remove(dir_plans_name + str(chat_id))

                output_string = "Your study plan was deleted!"
                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))


            elif msg["text"] == MAKE_PLAN:
                users_mode[chat_id] = Mode.MAKE_PLAN

                output_string = "Navigate menu and choose your teachings to make your study plan. Send " + END_PLAN + " when you have finisched!"
                bot.sendMessage(chat_id, output_string, reply_markup=make_area_keyboard(users_mode[chat_id]))

            elif msg["text"] == END_PLAN:
                users_mode[chat_id] = Mode.NORMAL
                store_user_plan(chat_id, users_plans[chat_id])
                output_string = "Well done! Now you can use " + MY_PLAN + " to see your study plan and " + MY_TIMETABLE + " to get your lessons shedules!"
                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))

            elif msg["text"] == BACK_TO_MAIN:
                users_mode[chat_id] = Mode.NORMAL

                output_string = "Choose your action!"

                bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))
            elif msg["text"] == BACK_TO_AREAS:

                output_string = "Choose your area!"

                bot.sendMessage(chat_id, output_string, reply_markup=make_area_keyboard(users_mode[chat_id]))
            elif msg["text"] in all_courses_group_by_area.keys():

                output_string = "Choose your course!"

                bot.sendMessage(chat_id, output_string,
                                reply_markup=make_courses_keyboard(msg["text"], users_mode[chat_id]))

            elif msg["text"].split()[0] in all_courses.keys():

                if users_mode[chat_id] == Mode.NORMAL:
                    output_string = "Choose a teaching!"
                    bot.sendMessage(chat_id, output_string,
                                    reply_markup=make_teachings_keyboard(msg["text"].split()[0], users_mode[chat_id]))


                elif users_mode[chat_id] == Mode.MAKE_PLAN:

                    output_string = "Choose a teaching to add to your plan!"
                    bot.sendMessage(chat_id, output_string,
                                reply_markup=make_teachings_keyboard(msg["text"].split()[0], users_mode[chat_id]))

            else:

                array = msg["text"].split()
                s = array[len(array) - 1]
                componente_id = s.replace("[", "").replace("]", "")

                if users_mode[chat_id] == Mode.NORMAL:

                    plan = Plan()
                    teaching = all_teachings[componente_id]

                    plan.add_teaching(teaching)

                    now = datetime.datetime.now()
                    timetable = get_plan_timetable(now, plan)

                    output_string = emo_calendar +" "+now.strftime("%d/%m/%Y") + "\n\n"
                    output_string += print_output_timetable(timetable)
                    bot.sendMessage(chat_id, output_string)

                elif users_mode[chat_id] == Mode.MAKE_PLAN:

                    if componente_id in all_teachings.keys():
                        teaching = all_teachings[componente_id]
                        users_plans[chat_id].add_teaching(teaching)
                        output_string = "Choose your area!"
                        bot.sendMessage(chat_id, output_string, reply_markup=make_area_keyboard(users_mode[chat_id]))

                    else:

                        output_string = "Sorry.. I don't understand.."

                        bot.sendMessage(chat_id, output_string,
                                        reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))
        else:

            users_mode[chat_id] = Mode.NORMAL

            output_string = "Sorry.. I don't understand.."
            output_string += "\n\n" + help_string
            bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))
    except:
        traceback.print_exc()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())
        output_string = traceback.format_exc()
        bot.sendMessage(chat_id, output_string, reply_markup=make_main_keyboard(chat_id, users_mode[chat_id]))


get_all_courses()
load_users_plans()
MessageLoop(bot, {'chat': on_chat_message, 'callback_query': on_callback_query}).run_as_thread()

print('Listening ...')
# Keep the program running.
while 1:
    time.sleep(10)
