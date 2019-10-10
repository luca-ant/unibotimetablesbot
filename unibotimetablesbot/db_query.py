import datetime
import requests
import traceback
import csv
import logging
import os
import wget
import json
import collections

from model import Course, Teaching, Mode, Plan, Lesson, Aula, Timetable, User
import config


def download_csv_orari():
    orari = collections.defaultdict(list)
    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### DOWNLOADING CSV ORARI")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### DOWNLOADING CSV ORARI")

    if os.path.isfile(config.current_dir+"orari_"+config.accademic_year+".csv"):
        os.remove(config.current_dir+"orari_"+config.accademic_year+".csv")

    url_orari_csv = "https://dati.unibo.it/dataset/course-timetable-"+config.accademic_year + \
        "/resource/orari_"+config.accademic_year + \
        "/download/orari_"+config.accademic_year+".csv"

    csv_orari_filename = wget.download(
        url_orari_csv, config.current_dir+"orari_"+config.accademic_year+".csv", bar=None)

    with open(csv_orari_filename) as f:
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            o = {}
            o["componente_id"] = row[0]
            o["inizio"] = ''.join(row[1].split("+")[0])
            o["fine"] = ''.join(row[2].split("+")[0])
            o["aula_codici"] = row[3]
            orari[o["componente_id"]].append(o)

    return orari


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


def get_all_aule():
    all_aule = dict()

    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " +
                 now.strftime("%b %d %Y %H:%M:%S") + " ### GETTING ALL AULE")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### GETTING ALL AULE")

    aule_table = "aule_" + config.accademic_year

    url = "https://dati.unibo.it/api/action/datastore_search_sql"

    sql_aule = "SELECT * FROM " + aule_table

    headers = {'Content-type': 'application/json',
               'Accept': 'application/json'}
    json_aule = requests.post(url, headers=headers,
                              data='{"sql":'+'"'+sql_aule+'"}').text

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

    return all_aule


def get_all_courses():

    all_courses = dict()
    all_teachings = dict()
    all_courses_group_by_area = collections.defaultdict(list)

    now = datetime.datetime.now()
    logging.info("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
                 " ### GETTING ALL COURSES")
    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") +
          " ### GETTING ALL COURSES")
    url = "https://dati.unibo.it/api/action/datastore_search_sql"
    corsi_table = "corsi_" + config.accademic_year + "_it"
    insegnamenti_table = "insegnamenti_" + config.accademic_year + "_it"
    curricula_table = "curriculadettagli_"+config.accademic_year+"_it"

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
        if course.ambiti not in all_courses_group_by_area.keys():
            all_courses_group_by_area[course.ambiti] = list()
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
        if (t.anno == None or t.anno == ""):
            comp_p = t.componente_padre
            while (t.anno == None or t.anno == "") and comp_p != None and comp_p != "":
                t.anno = all_teachings[comp_p].anno
                comp_p = all_teachings[comp_p].componente_padre

        if (t.crediti == None or t.crediti == ""):
            comp_p = t.componente_padre
            while (t.crediti == None or t.crediti == "") and comp_p != None and comp_p != "":
                t.crediti = all_teachings[comp_p].crediti
                comp_p = all_teachings[comp_p].componente_padre

    for key in all_courses.keys():
        all_courses[key].teachings.sort(
            key=lambda x: x.materia_descrizione, reverse=False)

    return all_courses, all_teachings, all_courses_group_by_area
