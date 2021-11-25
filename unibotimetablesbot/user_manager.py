import os
import json
import datetime
import logging

from model import Course, Teaching, Mode, Plan, Lesson, Aula, Timetable, User
import config


class UserManager:

    __instance = None

    @staticmethod
    def get_instance():
        if UserManager.__instance == None:
            UserManager.__instance = UserManager()
        return UserManager.__instance

    def __init__(self):
        self.users = dict()
        UserManager.__instance = self

    def add_user(self, u):
        if u != None:
            self.users[u.chat_id] = u

    def get_all_users(self):
        return self.users

    def get_user(self, chat_id):
        if chat_id in self.users.keys():
            return self.users[chat_id]
        else:

            u = User(chat_id)
            self.users[chat_id] = u
            return u

    def store_user(self, chat_id):
        if not os.path.isdir(config.dir_users_name):
            os.makedirs(config.dir_users_name)

        u = self.users[chat_id]

        with open(config.dir_users_name + str(chat_id), 'w') as outfile:
            user_dict = {}
            user_dict["chat_id"] = u.chat_id
            user_dict["mode"] = u.mode.name
            user_dict["notification"] = u.notification
            user_dict["notification_time"] = u.notification_time
            outfile.write(json.dumps(user_dict))

    def load_user(self, chat_id):
        if os.path.isfile(config.dir_users_name+str(chat_id)):
            with open(config.dir_users_name + str(chat_id), 'r') as f:
                user_dict = json.load(f)

        u = User(chat_id)
        for key in user_dict.keys():
            if key == 'chat_id':
                pass
            elif key == 'mode':
                u.mode = Mode[user_dict["mode"]]

            elif key == 'notification':
                u.notification = user_dict["notification"]

            elif key == 'notification_time':
                u.notification_time = user_dict["notification_time"]

        return u

    def check_user(self, chat_id):
        u = self.users[chat_id]
        if os.path.isfile(config.dir_plans_name + str(chat_id)):
            u.mode = Mode.PLAN
        else:
            u.mode = Mode.NORMAL
