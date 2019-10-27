import datetime
import config
from enum import Enum


class Mode(Enum):
    NORMAL = 1
    MAKE_PLAN = 2
    DEL = 3
    PLAN = 4


class User:
    def __init__(self, chat_id, mode=Mode.NORMAL, notification=False, notification_time=15):
        self.chat_id = chat_id
        self.mode = mode
        self.notification = notification
        self.notification_time = notification_time


class Teaching:
    def __init__(self, corso_codice, materia_codice, materia_descrizione, docente_nome, componente_id, url, anno, crediti, componente_padre, componente_radice):
        self.componente_id = componente_id
        self.corso_codice = corso_codice
        self.materia_codice = materia_codice
        self.docente_nome = docente_nome
        self.url = url
        self.materia_descrizione = materia_descrizione
        self.anno = anno
        self.crediti = crediti
        self.componente_padre = componente_padre
        self.componente_radice = componente_radice

    def __str__(self):
        result = self.materia_codice + " - <b>" + self.materia_descrizione + "</b>"
        if self.docente_nome != "":
            result += " (<i>" + self.docente_nome + "</i>)"
        result += " [ " + self.componente_id + " ]"
        return result


class Course:

    def __init__(self, corso_codice, corso_descrizione, tipologia, sededidattica, ambiti, url, durata):
        self.url = url
        self.ambiti = ambiti
        self.tipologia = tipologia
        self.corso_descrizione = corso_descrizione
        self.sededidattica = sededidattica
        self.corso_codice = corso_codice
        self.teachings = list()
        self.durata = int(durata)

    def add_teaching(self, t):
        self.teachings.append(t)

    def __str__(self):
        return self.corso_codice + " - " + self.corso_descrizione + " (" + self.sededidattica + ") - " + self.tipologia


class Plan:
    def __init__(self):
        self.teachings = list()

    def add_teaching(self, teaching):

        index = -1
        for i in range(0, len(self.teachings), 1):
            t = self.teachings[i]
            if t.componente_id == teaching.componente_id:
                index = i
                break
        if index < 0:
            self.teachings.append(teaching)
            self.teachings.sort(key=lambda x: x.materia_descrizione)
            return True

        return False

    def remove_teaching(self, teaching):
        index_to_remove = -1
        for i in range(0, len(self.teachings), 1):
            t = self.teachings[i]
            if t.componente_id == teaching.componente_id:
                index_to_remove = i
        if index_to_remove >= 0:
            del self.teachings[index_to_remove]
            return True

        return False

    def set_teachings(self, t):
        self.teachings = t

    def find_teaching_by_componente_id(self, componente_id):
        for t in self.teachings:
            if t.componente_id == componente_id:
                return t
        return None

    def is_empty(self):
        if len(self.teachings) == 0:
            return True
        else:
            return False

    def __str__(self):
        result = config.emo_plan + " YOUR STUDY PLAN\n\n"
        for t in self.teachings:
            result += t.materia_codice + " - " + t.materia_descrizione + ""
            if t.docente_nome != "":
                result += " (<i>" + t.docente_nome + "</i>)"
            result += "\n\n"

        return result


class Aula:
    def __init__(self, aula_codice, aula_nome, aula_indirizzo, aula_piano, lat, lon):
        self.lon = lon
        self.lat = lat
        self.aula_piano = aula_piano
        self.aula_indirizzo = aula_indirizzo
        self.aula_nome = aula_nome
        self.aula_codice = aula_codice

    def is_empty(self, now, orari_group_by_aula):

        free = True

        start = datetime.datetime.strptime(now.strftime(
            "%Y-%m-%d") + "T00:00:00", "%Y-%m-%dT%H:%M:%S")
        stop = datetime.datetime.strptime(now.strftime(
            "%Y-%m-%d") + "T23:59:59", "%Y-%m-%dT%H:%M:%S")
        for o in orari_group_by_aula[self.aula_codice]:

            inizio = datetime.datetime.strptime(
                o["inizio"], "%Y-%m-%dT%H:%M:%S")
            fine = datetime.datetime.strptime(o["fine"], "%Y-%m-%dT%H:%M:%S")

            if inizio > start and inizio < stop:
                if now >= inizio and now <= fine:
                    free = False
                    break
        return free

    def __str__(self):

        result = self.aula_nome + " - " + self.aula_indirizzo

        return result


class Lesson(Teaching):
    def __init__(self, corso_codice, materia_codice, materia_descrizione, docente_nome, componente_id, url, inizio,
                 fine, anno, crediti, componente_padre, componente_radice):
        Teaching.__init__(self, corso_codice, materia_codice,
                          materia_descrizione, docente_nome, componente_id, url, anno, crediti, componente_padre, componente_radice)
        self.inizio = inizio
        self.fine = fine
        self.lista_aule = list()
        self.anno = anno
        self.crediti = crediti
        self.componente_padre = componente_padre

    def add_aula(self, a):
        self.lista_aule.append(a)


class Timetable:
    def __init__(self):
        self.lessons = list()

    def add_lesson(self, l):
        self.lessons.append(l)

    def __str__(self):
        result = ""
        for l in self.lessons:
            result += l.materia_codice + " - <b>" + l.materia_descrizione + "</b>"
            if l.docente_nome != "":
                result += " (<i>" + l.docente_nome + "</i>)"
            if l.crediti != None and l.crediti != "":
                result += " - " + l.crediti + " CFU"

            result += "\n"

            result += config.emo_calendar + " " + l.inizio.strftime("%d/%m/%Y")
            result += "\n"
            result += config.emo_clock + " " + l.inizio.strftime("%H:%M")
            result += " - "
            result += l.fine.strftime("%H:%M")
            result += "\n"
            for a in l.lista_aule:
                result += config.emo_room + " " + a.aula_nome
                result += "\n"
                result += config.emo_address + " " + a.aula_indirizzo
                result += " - "
                result += a.aula_piano
                result += "\n"
                if a.lat != None and a.lon != None and a.lat != "" and a.lon != "":
                    result += config.emo_gps + " <code>" + a.lat + ", " + a.lon + "</code>"
                    result += "\n"
            result += "\n"

        return result
