import os
import logging

token = os.environ['UNI_BOT_TOKEN']

accademic_year = ""

current_dir = ""
logging.basicConfig(filename=current_dir +
                    "unibotimetablesbot.log", level=logging.INFO)

logging.info("### WORK DIR " + current_dir)

dir_plans_name = current_dir + 'plans/'
dir_users_name = current_dir + 'users/'


# EMOJI

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
emo_pin = u'\U0001F4CC'
emo_less = u'\U0001F4D6'


# BUTTONS
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

# COMMANDS

SET_NOT_TIME_CMD = "/set_notification_time"


# CONSTANT STRINGS


donation_string = emo_money + \
    " Do you like this bot? If you want to support it you can make a donation here!  -> https://www.paypal.me/lucaant"

issue_string = "For issues send a mail to luca.ant96@libero.it describing the problem in detail."

command_help_string = "<b>AVAILABLE COMMANDS:</b>\n\n" + SET_NOT_TIME_CMD + " => to set your favourite notification time\n<i>Example:</i> send \"" + \
    SET_NOT_TIME_CMD + \
    " 20\" (without quotes) to set 20 minutes and then will you receive a notification 20 minutes before the lesson. Please set a number of minutes multiple of 5."

important_string = "<b>IMPORTANT! All data (provided by https://dati.unibo.it) are updated once a day. For suddend changes or extra lessons please check on official Unibo site! (Especially for the first weeks)</b>"

help_string = "This bot helps you to get your personal timetable of Unibo lessons. First of all <b>you need to make your study plan</b> by pressing " + MAKE_PLAN+". Then you have to add your teachings by pressing \"/add_XXXXXX\" command near the teaching that you want to insert in your plan. After that by simply pressing " + MY_TIMETABLE+" you get your personal  timetable for today!\n\n<b>USE:</b>\n\n" + ALL_COURSES + " to see today's schedule\n\n" + MAKE_PLAN + " to make your study plan\n\n" + MY_PLAN + " to see your study plan and remove teachings\n\n" + MY_TIMETABLE + " to get your personal lesson's schedule\n\n" + NOTIFY_ON + \
    " to receive a notification before every lesson\n\n" + DEL_PLAN + " to delete your plan" + \
    "\n\n" + command_help_string+"\n\n"+issue_string+"\n\n" + important_string


privacy_string = "<b>In order to provide you the service, this bot collects user data like your study plan and your preferences (ON/OFF notification...). \nUsing this bot you allow your data to be saved.</b>"