import os
import logging

token = os.environ['UNI_BOT_TOKEN']

accademic_year = ""

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"/"

logging.basicConfig(filename=current_dir + "unibotimetablesbot.log", level=logging.INFO)

data_dir = current_dir+"unibotimetablesbot_data/"

download_dir = current_dir+"download/"

dir_plans_name = data_dir + 'plans/'
dir_users_name = data_dir + 'users/'


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
emo_blue_circle = u'\U0001F535'
emo_red_circle = u'\U0001F534'
emo_black_circle = u'\U000026AB'
emo_yellow_square = u'\U0001F536'
emo_button = u'\U0001F532'
emo_commands = u'\U00000023' + u'\U000020E3'
emo_tap = u'\U0001F449' + u'\U0001F3FB'

# BUTTONS
ALL_COURSES = emo_courses + " " + "ALL COURSES"
MY_TIMETABLE = emo_timetable + " " + "MY TIMETABLE"
MY_PLAN = emo_plan + " " + "MY STUDY PLAN"
MAKE_PLAN = emo_make + " " + "UPDATE MY STUDY PLAN"
EMPTY_ROOMS = emo_room + " " + "EMPTY CLASSROOMS"
ROOMS = emo_room + " " + "CLASSROOMS"
ALL_ROOMS = emo_room + " " + "ALL CLASSROOMS"
NOTIFY_ON = emo_not_on + " " + "ENABLE NOTIFICATIONS"
NOTIFY_OFF = emo_not_off + " " + "DISABLE NOTIFICATIONS"
DEL_PLAN = emo_del + " " + "DELETE STUDY PLAN"
END_PLAN = emo_end_plan + " " + "DONE!"
BACK_TO_AREAS = emo_back + " " + "BACK TO AREAS"
BACK_TO_MAIN = emo_back + " " + "BACK TO MAIN"
DONATION = emo_money + " " + "DONATION"
HELP = emo_help + " " + "HELP"
PRIVACY = emo_privacy + " " + "PRIVACY POLICY"
SEND_LOCATION = emo_gps + " " + "TAP HERE TO SEND LOCATION"

# COMMANDS

SET_NOT_TIME_CMD = "/set_notify_time"


# CONSTANT STRINGS


donation_string = emo_money + \
    " Do you like this bot? If you want to support it you can make a donation here! -> https://www.paypal.me/lucaant"


location_string = emo_gps+" <b>LOCATION</b>\n\nAre you looking for an empty classroom to study? Try to send your current location and the bot will search empty classrooms around you."
issue_string = "For issues send a mail to luca.antognetti2@gmail.com describing the problem in detail."

command_help_string = emo_commands+" <b>COMMANDS:</b>\n\n" + SET_NOT_TIME_CMD + " - to set your favourite notification time\n<i>Example:</i> send \"" + \
    SET_NOT_TIME_CMD + \
    " 20\" (without quotes) to set 20 minutes and then will you receive notifications 20 minutes before each lesson (Please choose a number of minutes multiple of 5)."

important_string = "<b>IMPORTANT! All data (provided by https://dati.unibo.it) are updated once a day. For suddend changes or extra lessons please check on official Unibo site! (Especially for the first weeks)</b>"

help_string = "This bot helps you to get your personal timetable of Unibo lessons. First of all <b>you need to make your study plan</b> by pressing " + MAKE_PLAN+". Then you have to add your subjects by pressing \"/add_XXXXXX\" command near the subject that you want to insert in your plan. After that by simply pressing " + MY_TIMETABLE+" you get your personal timetable for today and can navigate through days!\n\n" + emo_button + " <b>BUTTONS:</b>\n\n" + ALL_COURSES + " - to see today's schedule\n\n" + MAKE_PLAN + " - to make your study plan\n\n" + MY_PLAN + " - to see your study plan and remove subjects\n\n" + MY_TIMETABLE + " - to get your personal lesson's schedule\n\n" + NOTIFY_ON + \
    " - to receive a notification before every lesson\n\n" + DEL_PLAN + " - to delete your plan" + \
    "\n\n" + command_help_string+"\n\n" + location_string + \
    "\n\n"+issue_string+"\n\n" + important_string


privacy_string = "<b>In order to provide you the service, this bot collects user data like your study plan and your preferences (ON/OFF notification...). Also your location is logged when you sent it.\nUsing this bot you allow all your data to be saved.</b>"
