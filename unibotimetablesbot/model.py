from enum import Enum


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
            result += " (" + self.docente_nome + ") "

        return result


class Course:

    def __init__(self, corso_codice, corso_descrizione, tipologia, sededidattica, ambiti):
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

    def add_teaching(self, t):
        self.teachings.append(t)

    def set_teachings(self, t):
        self.teachings = t

    def find_teaching_by_componente_id(self, componente_id):
        for t in self.teachings:
            if t.componente_id == componente_id:
                return t
        return None


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

            result += l.inizio.strftime("%d/%m/%Y")
            result += "\n"
            result += l.inizio.strftime("%H:%M")
            result += " - "
            result += l.fine.strftime("%H:%M")
            result += "\n"
            for a in l.lista_aule:

                result += a.aula_nome
                result += "\n"
                result += a.aula_indirizzo
                result += "\n"
                result += a.aula_piano
                result += "\n"
                result += str(a.lat)+", "+str(a.lon)
            result += "\n\n"
        return result


class Mode(Enum):
    NORMAL = 1
    MAKE_PLAN = 2
