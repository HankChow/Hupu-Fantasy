#!/usr/bin/python3
# coding: utf-8

import json
import time


def load_room(roomid):
    j = json.load(open('./all_rooms/{0}.txt'.format(roomid)))
    if 'data' in j.keys() and len(j['data']) > 0:
        game_date = time.strftime('%m-%d', time.localtime(j['data'][0]['start_time']))
        rf = open('./rooms', 'r')
        lines = rf.readlines()
        last_line = '' if len(lines) == 0 else lines[-1]
        rf.close()
        if last_line == '' or last_line.split(' ')[0] != game_date:
            wf = open('./rooms', 'a+')
            wf.write('{0} {1}\n'.format(game_date, roomid))
            wf.close()
            print('{0} {1}'.format(game_date, roomid)) 


if __name__ == '__main__':
    for i in range(1, 3570):
        load_room(i)
