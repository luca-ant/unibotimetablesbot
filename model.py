from enum import Enum

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


class Teaching:
    def __init__(self, corso_codice, materia_codice, materia_descrizione, docente_nome, componente_id, url):
        self.componente_id = componente_id
        self.corso_codice = corso_codice
        self.materia_codice = materia_codice
        self.docente_nome = docente_nome
        self.url = url
        self.materia_descrizione = materia_descrizione

    def __str__(self):
        result = self.materia_codice + " - " + self.materia_descrizione
        if self.docente_nome != "":
            result += " (" + self.docente_nome + ")"
        result += " [" + self.componente_id + "]"
        result += "\n"
        return result


class Course:

    def __init__(self, corso_codice, corso_descrizione, tipologia, sededidattica, ambiti, url):
        self.url = url
        self.ambiti = ambiti
        self.tipologia = tipologia
        self.corso_descrizione = corso_descrizione
        self.sededidattica = sededidattica
        self.corso_codice = corso_codice
        self.teachings = list()

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

    def remove_teaching(self, teaching):
        index_to_remove = -1
        for i in range(0, len(self.teachings), 1):
            t = self.teachings[i]
            if t.componente_id == teaching.componente_id:
                index_to_remove = i
        if index_to_remove >= 0:
            del self.teachings[index_to_remove]

    def set_teachings(self, t):
        self.teachings = t

    def find_teaching_by_componente_id(self, componente_id):
        for t in self.teachings:
            if t.componente_id == componente_id:
                return t
        return None

    def __str__(self):
        result = emo_plan + " YOUR STUDY PLAN\n\n"
        for t in self.teachings:
            result += t.materia_codice + " - " + t.materia_descrizione
            if t.docente_nome != "":
                result += " (" + t.docente_nome + ")"
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


class Lesson(Teaching):
    def __init__(self, corso_codice, materia_codice, materia_descrizione, docente_nome, componente_id, url, inizio,
                 fine):
        Teaching.__init__(self, corso_codice, materia_codice, materia_descrizione, docente_nome, componente_id, url)
        self.inizio = inizio
        self.fine = fine
        self.lista_aule = list()

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
            result += l.materia_codice + " - " + l.materia_descrizione
            if l.docente_nome != "":
                result += " (" + l.docente_nome + ") "
            result += "\n"

            result += emo_calendar + " " + l.inizio.strftime("%d/%m/%Y")
            result += "\n"
            result += emo_clock + " " + l.inizio.strftime("%H:%M")
            result += " - "
            result += l.fine.strftime("%H:%M")
            result += "\n"
            for a in l.lista_aule:
                result += emo_room + " " + a.aula_nome
                result += "\n"
                result += emo_address + " " + a.aula_indirizzo
                result += " - "
                result += a.aula_piano
                result += "\n"
                if a.lat != "" and a.lon != "":
                    result += emo_gps + " " + a.lat + ", " + a.lon
                    result += "\n"
            result += "\n"

        return result


class Mode(Enum):
    NORMAL = 1
    MAKE_PLAN = 2
