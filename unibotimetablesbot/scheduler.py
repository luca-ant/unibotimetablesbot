import datetime
import schedule
import logging
import traceback
import time
from user_manager import add_user, check_user, get_user, load_user, store_user, get_all_users
import config


def send_notifications():
    now = datetime.datetime.now()

    fix_now = datetime.datetime.strptime(
        str(now.year)+"-"+str(now.month) + "-"+str(now.day)+"T"+str(now.hour)+":"+str(now.minute)+":00", "%Y-%m-%dT%H:%M:%S")

    ##### DEBUG #####
    # fix_now = datetime.datetime.strptime("2019-10-08T13:45:00", "%Y-%m-%dT%H:%M:%S")
    #################

    for chat_id in get_all_users().keys():
        try:
            u = get_user(chat_id)

            if u.notification:

                plan = load_user_plan(chat_id)

                timetable = get_next_lesson(
                    chat_id, fix_now, plan, orari, all_aule)

                # output_string = config.emo_ay + " A.Y. <code>" + config.accademic_year + "/" + str(
                #     int(config.accademic_year) + 1) + "</code>\n"
                # output_string += config.emo_calendar + " " + \
                #     now.strftime("%A %B %d, %Y") + "\n\n"
                # output_string += config.emo_less+"<b>YOUR NEXT LESSON</b>\n\n"

                # output_string += print_output_timetable(timetable)

                output_string = ""
                for l in timetable.lessons:
                    for a in l.lista_aule:
                        output_string += config.emo_room + " <b>" + a.aula_nome+"</b> - "

                    output_string += "IS GOING TO START <b>" + l.materia_descrizione + "</b>"
                    if l.docente_nome != "":
                        output_string += " (<i>" + l.docente_nome + "</i>)"
                    if l.crediti != None and l.crediti != "":
                        output_string += " - " + l.crediti + " CFU"

                    output_string += "\n"

                    output_string += config.emo_clock + " " + \
                        l.inizio.strftime("%H:%M")
                    output_string += " - "
                    output_string += l.fine.strftime("%H:%M")

                    output_string += " "+config.emo_calendar + \
                        " " + l.inizio.strftime("%d/%m/%Y")
                    output_string += "\n\n"

                if output_string:

                    logging.info(
                        "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### SENDING NOTIFICATION TO " + str(chat_id))
                    print("TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + "  ### SENDING NOTIFICATION TO " + str(
                        chat_id))

                    update.message.reply_html(output_string)

        except:
            traceback.print_exc()
            now = datetime.datetime.now()
            logging.info(
                "TIMESTAMP = " + now.strftime("%b %d %Y %H:%M:%S") + " ### EXCEPTION = " + traceback.format_exc())


def scheduler_function():

    for j in range(0, 60, 5):
        m = "%02d" % j
        schedule.every().hour.at(":"+m).do(send_notifications)

    while True:

        schedule.run_pending()
        time.sleep(150)
