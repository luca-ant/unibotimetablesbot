import datetime
import traceback
import logging
import requests
import os
import json

from model import Course, Teaching, Mode, Plan, Lesson, Aula, Timetable, User
from user_manager import get_user
import config


def get_plan_timetable(day, plan, orari):
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

    orari_table = "orari_" + config.accademic_year
    aule_table = "aule_" + config.accademic_year
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


def get_next_lesson(chat_id, now, plan, orari):
    timetable = Timetable()

    if plan.is_empty():
        return timetable

    u = get_user(chat_id)

    lesson_time = now + datetime.timedelta(minutes=u.notification_time)

    for t in plan.teachings:
        for o in orari[t.componente_id]:
            try:
                ##### DEBUG #####
                # if t.componente_id == '448380':
                #     print(t)
                #################
                inizio = datetime.datetime.strptime(
                    o["inizio"], "%Y-%m-%dT%H:%M:%S")

                if inizio == lesson_time:
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


def load_user_plan(chat_id):
    if os.path.isfile(config.dir_plans_name + str(chat_id)):
        with open(config.dir_plans_name + str(chat_id)) as f:
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


def print_plan(chat_id, plan):
    result = config.emo_plan + " YOUR STUDY PLAN" + "\n\n"
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


def print_teachings_message(chat_id, all_courses, corso_codice, year):
    result = list()
    mode = get_user(chat_id).mode

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


def print_output_timetable(timetable):
    if timetable != None:

        output_string = str(timetable)
        if output_string == "":
            output_string = config.emo_no_less + " <b>NO LESSONS FOR TODAY</b>"
    else:
        output_string = config.emo_404 + " SCHEDULES DATA NOT FOUND!"

    return output_string
