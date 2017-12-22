#!/usr/bin/python3
# coding: utf-8

import json
import requests


def get_all_players():
    ap = open('all_players', 'a+')
    for i in range(900):
        url = 'https://fantasy.hupu.com/api/player/data/{0}'.format(i)
        player_info = requests.get(url).text
        player_json = json.loads(player_info)
        if int(player_json['status']['code']) == 200:
            info = player_json['data']['player_info']
            ap.write('{0} {1} {2} {3} {4}\n'.format(i, info['alias'], info['name'], info['en_name'].replace(' ', '-'), info['ability']))
            print('{0} is ok.'.format(i))
        else:
            print('{0} does not exist.'.format(i))
            continue
    ap.close()

if __name__ == '__main__':
    get_all_players()
