# -*- coding: utf-8 -*-

import sys
import json
import threading
import time
import random
import re
from cmd import Cmd

import tweepy

import config

FAV_INTERVAL_MIN = 3
FAV_INTERVAL_MAX = 5

class ChooChooCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.intro = "Fun Fun We hit the star star"
        self.prompt = "ChooChooFav >>> "
        self.main_account_api = None
        self.initialize()

    def initialize(self):
        try:
            self.api_list = []
            self.thread_dic = {}

            file = open('userdata.json', 'r')
            json_data = json.load(file)
            file.close()

            for index in json_data:
                auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
                auth.set_access_token(
                    json_data[index]["access_token"],
                    json_data[index]["access_token_secret"])

                api = tweepy.API(auth)
                print("%s logged in" % api.me().screen_name)
                if self.main_account_api is None:
                    self.main_account_api = api

                self.api_list.append(api)

        except Exception as e:
            print(e)
            self.do_exit("")
            return True

    def do_start(self, line):
        # todo : error if no user available

        pattern = r"https?://twitter\.com/[0-9a-zA-Z_]{1,15}/status/[0-9]*"
        if re.match(pattern, line):
            status_id_string = line.rsplit('/', 1)[1]
        else:
            status_id_string = line

        try:
            status_id = int(status_id_string)
            self.thread_dic[status_id] = ChooChooThread(self.api_list, status_id)

        except Exception:
            print('status_id')
            self.do_exit("")
            return True

    def do_stop(self, line):
        try:
            status_id = int(line)
            self.thread_dic[status_id].stop()

        except Exception:
            print('status_id')
            self.do_exit("")
            return True

    def do_adduser(self, line):
        # todo
        # write url, read pin code, post oauth, write to json
        pass

    def do_exit(self, line):
        for key in self.thread_dic:
            self.thread_dic[key].stop()
        return True

    def do_status(self, line):
        for key in self.thread_dic:
            print(key)

    def default(self, line):
        self.do_start(line)

    # override to catch keyboard interrupt
    # https://stackoverflow.com/questions/8813291
    def cmdloop(self, intro=None):
        print(self.intro)
        while True:
            try:
                super(ChooChooCmd, self).cmdloop(intro="")
                self.postloop()
                break

            except KeyboardInterrupt:
                print("keyboard interrupt shutting down...")
                self.do_exit("")
                break

#https://qiita.com/xeno1991/items/b207d55a413664513e5f
class ChooChooThread():
    def __init__(self, api_list, status_id):
        self.api_list = api_list
        self.status_id = status_id
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target = self.target)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join()

    def target(self):
        # do unfav
        for api in self.api_list:
            try:
                api.destroy_favorite(self.status_id)
            except Exception:
                # no problem. just i havn't faved
                pass

        # do fav, unfav, fav, unfav, ...
        try:
            while not self.stop_event.is_set():
                for api in self.api_list:
                    api.create_favorite(self.status_id)
                    #print(api.me().screen_name + ' favs')
                    time.sleep(random.uniform(FAV_INTERVAL_MIN, FAV_INTERVAL_MAX))
                    api.destroy_favorite(self.status_id)

        except Exception as e:
            print(e)
            for api in self.api_list:
                try:
                    api.destroy_favorite(self.status_id)
                except Exception:
                    pass

if __name__ == '__main__':
    choochoo = ChooChooCmd()
    choochoo.cmdloop()
