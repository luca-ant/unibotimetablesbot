import os
import collections
import sys
import xml.etree.ElementTree as ET
import datetime
import logging
import json
import requests
import operator
import time
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from threading import Lock

with open(sys.argv[1]) as f:
    token = f.read().strip()
f.close()

bot = telepot.Bot(token)

donation_string = "Se ti è piacuto questo bot e vuoi sostenerlo puoi fare una donazione qui! -> https://www.paypal.me/lucaant"

uni = collections.defaultdict(list)
courses = collections.defaultdict(list)
schedules = collections.defaultdict()
timestamps_cache = collections.defaultdict()

logging.basicConfig(filename="lessonsinfobot.log", level=logging.INFO)
# logging.basicConfig(filename="/bot/lessonsinfobot/lessonsinfobot.log", level=logging.INFO)

dir_cache_name = './cache/'
# dir_cache_name = '/bot/lessonsinfobot/cache/'

writer_lock = Lock()


def loadData():
    #    tree = ET.parse("/bot/lessonsinfobot/data.xml")
    tree = ET.parse("data.xml")
    xml_root = tree.getroot()

    for fac in xml_root:
        nomefac = fac.attrib["nome"]
        for cor in fac:
            nomecor = cor.attrib["nome"]
            uni[nomefac].append(nomecor)
            for a in cor:
                nomeanno = a[0].text
                linkanno = a[1].text
                courses[nomecor].append(nomeanno)
                schedules[nomeanno] = linkanno


# return a json as a dict
def getJsonLessonsFromUrl(url):
    response = requests.get(url)
    result = response.text
    return result


# return a list of lessons (a lesson = a dict)
def parseJson(data):
    insegnamenti = (data["insegnamenti"])

    lessons = data["events"]

    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=2)
    nextlessons = list()
    for l in lessons:
        starttime = datetime.datetime.strptime(l["start"], "%Y-%m-%dT%H:%M:%S")
        endtime = datetime.datetime.strptime(l["end"], "%Y-%m-%dT%H:%M:%S")

        if starttime > now and starttime < tomorrow:
            try:
                nextlesson = dict()
                nextlesson["title"] = l["title"]
                nextlesson["starttime"] = starttime
                nextlesson["endtime"] = endtime
                nextlesson["class"] = l["aule"][0]["des_risorsa"]
            except:
                pass
            nextlessons.append(nextlesson)

    nextlessons.sort(key=operator.itemgetter('starttime'))

    return nextlessons


# return a json as a dict
def getJsonLessonsFromCache(course):
    try:
        if os.path.isfile(dir_cache_name + course):
            with open(dir_cache_name + course) as f:
                return json.load(f)
        else:
            return getJsonLessonsFromUrl(schedules.get(course))
    except:
        return getJsonLessonsFromUrl(schedules.get(course))


def getLessons(course):
    now = datetime.datetime.now()

    if course in timestamps_cache.keys() and timestamps_cache[course] > now - datetime.timedelta(days=1):
        return parseJson(getJsonLessonsFromCache(course))
    else:

        json_string = getJsonLessonsFromUrl(schedules.get(course))

        if not os.path.isdir(dir_cache_name):
            os.mkdir(dir_cache_name)

        writer_lock.acquire()
        with open(dir_cache_name + course, 'w') as outfile:
            outfile.write(json_string)
        writer_lock.release()
        logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " UPDATE CACHE for course \"" + course + "\"")
        timestamps_cache[course] = now

        data = json.loads(json_string)
        return parseJson(data)


def printOutput(course):
    try:
        lessons = getLessons(course)

        outputstring = []

        for l in lessons:
            outputstring.append(l["title"])
            outputstring.append("\n")
            outputstring.append(l["starttime"].strftime("%d-%m-%Y"))
            outputstring.append("\n")
            outputstring.append(l["starttime"].strftime("%H:%M"))
            outputstring.append(" - ")

            outputstring.append(l["endtime"].strftime("%H:%M"))
            try:
                outputstring.append("\n")
                outputstring.append(l["class"])
            except:
                pass

            outputstring.append("\n")
            outputstring.append("\n")

        return ''.join(outputstring)

    except Exception as e:
        logging.info(e)
        print(e)
        return "ERRORE!"


def makeMainMenu():
    buttonsUni = list()

    for i in range(0, len(uni), 1):
        buttonsUni.append(list())

    i = 0
    for str in uni.keys():
        buttonsUni[i].append(str)
        i += 1

    mainMenukeyboard = ReplyKeyboardMarkup(keyboard=buttonsUni, resize_keyboard=True)

    return mainMenukeyboard


def makeSubMenu(key):
    schedulesList = uni[key]
    buttonsCourses = list()

    for i in range(0, len(schedulesList) + 1, 1):
        buttonsCourses.append(list())

    for i in range(0, len(schedulesList), 1):
        buttonsCourses[i].append(schedulesList[i])

    buttonsCourses[len(schedulesList)].append('<- Tutte le facoltà')
    subMenukeyboard = ReplyKeyboardMarkup(keyboard=buttonsCourses, resize_keyboard=True)
    return subMenukeyboard


def makeScheduleMenu(key):
    schedulesList = courses[key]
    buttonsCourses = list()

    for i in range(0, len(schedulesList) + 1, 1):
        buttonsCourses.append(list())

    for i in range(0, len(schedulesList), 1):
        buttonsCourses[i].append(schedulesList[i])

    buttonsCourses[len(schedulesList)].append('<- Tutte le facoltà')
    scheduleMenukeyboard = ReplyKeyboardMarkup(keyboard=buttonsCourses, resize_keyboard=True)
    return scheduleMenukeyboard


def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(msg)
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### MESSAGGIO = " + repr(msg))

    if content_type == "text":
        if msg["text"] == '/start':

            output_string = "Benvenuto! Puoi usare questo bot per visualizzare velocemente le tue prossime lezioni presso l'Unibo"

            bot.sendMessage(chat_id, output_string, reply_markup=makeMainMenu())


        elif msg["text"] == '/help':

            output_string = "Scegli la tua facoltà dal menù qui sotto. Poi scegli il tuo corso e riceverai in risposta dal bot le tue lezioniper le prissime 24 ore!\nPer problemi e malfunzionamenti inviare una mail a luca.ant96@libero.it descrivendo dettagliatamente il problema."

            bot.sendMessage(chat_id, output_string, reply_markup=makeMainMenu())
        elif msg["text"] in list(schedules.keys()):

            output_string = printOutput(msg["text"])
            if output_string == "":
                output_string = "Nessuna lezione da mostrare"
            bot.sendMessage(chat_id, output_string)

        elif msg["text"] in list(courses.keys()):

            output_string = "Scegli l'orario da visualizzare"

            bot.sendMessage(chat_id, donation_string)
            bot.sendMessage(chat_id, output_string, reply_markup=makeScheduleMenu(msg["text"]))
        elif msg["text"] in list(uni.keys()):

            output_string = "Scegli il tuo corso"

            bot.sendMessage(chat_id, donation_string)
            bot.sendMessage(chat_id, output_string, reply_markup=makeSubMenu(msg["text"]))


        elif msg["text"] == '<- Tutte le facoltà':

            output_string = "Scegli la tua facoltà"

            bot.sendMessage(chat_id, donation_string)
            bot.sendMessage(chat_id, output_string, reply_markup=makeMainMenu())
        else:

            output_string = "Scegli la tua facoltà"

            bot.sendMessage(chat_id, donation_string)
            bot.sendMessage(chat_id, output_string, reply_markup=makeMainMenu())
    else:

        output_string = "Non ho capito...\nScegli la tua facoltà"

        bot.sendMessage(chat_id, donation_string)
        bot.sendMessage(chat_id, output_string, reply_markup=makeMainMenu())


loadData()
MessageLoop(bot, {'chat': on_chat_message}).run_as_thread()

print('Listening ...')
# Keep the program running.
while 1:
    time.sleep(10)
