#!/usr/bin/python3
# coding: utf-8

import configparser
import json
import os
import requests
import sys
import time

from prettytable import PrettyTable


# 获取当天金豆场房间id
def get_current_roomid():
    url = 'https://fantasy.hupu.com/api/schedule/normal'
    r = requests.post(url, headers=HEADER)
    j = json.loads(r.text)
    status_code = int(j['status']['code'])
    if status_code != 200:
        if status_code == 401:
            print('Cookie 设置错误。')
            exit()
        print('启动失败。')
        exit()
    for i in j['normal_games']:
        if i['name'] == '金豆专场':
            return i['id']


# 根据当天的金豆房间id拉取当天参赛球员数据
# 按照号位保存在当前路径下
def get_players(roomid):
    if roomid is None:
        print('本日无范特西。。。')
        exit()
    os.system('rm {0}/plrs/{1}-*.plr'.format(sys.path[0], roomid))
    for i in range(1, 6):
        url = 'https://fantasy.hupu.com/api/player/candidates/{0}/{1}'.format(roomid, i)
        os.system('wget {0} -O {1}/plrs/{2}-{3}.plr'.format(url, sys.path[0], roomid, i))


# 读取球员数据文件，解析json，存放到list中，每名球员为一个dict
def parse_data(roomid, position):
    path = '{0}/plrs/{1}-{2}.plr'.format(sys.path[0], roomid, position)
    player_data = json.load(open(path))['data']
    parsed_dict = {}
    player_list = []
    max_timestamp = 0
    for player in player_data:
        if player['name'] not in AVOID_PLAYERS and \
            int(player['injuryStatus']) == 2 and \
            (1 if MAX_SALARY == 0 else int(player['salary']) <= MAX_SALARY) and \
            (1 if MIN_SALARY == 0 else int(player['salary']) >= MIN_SALARY) and \
            (1 if MIN_PLAYTIME == 0 else int(player['play_time']) >= MIN_PLAYTIME):
            to_append = {'id': player['id'], 'name': player['name'], 'salary': int(player['salary']), 'score': float(player['fantasy_score']), 'positions': player['positions'], 'injury': int(player['injuryStatus']), 'playtime': int(player['play_time'])}
            if ORDER_BY == 3:
                to_append['score'] = float(get_players_data([to_append['id']])[0]['player_info']['ability'])
            player_list.append(to_append)
        if int(player['start_time']) > max_timestamp:
            max_timestamp = int(player['start_time'])
    parsed_dict['player_list'] = player_list
    game_date = time.strftime('%m-%d', time.localtime(max_timestamp))
    parsed_dict['game_date'] = game_date
    return parsed_dict


# 压缩list
# 两个球员a、b，若Wealth(a) > Wealth(b)且Cost(a) < Cost(b)，则可以把球员剔出考虑范围
def shrink(player_list):
    dels = []
    preserves = []
    for sub in player_list:
        if sub['name'] in PRESERVE_PLAYERS:
            preserves.append(sub['id'])
        for obj in player_list:
            if sub['salary'] < obj['salary'] and sub['score'] > obj['score']:
                dels.append(obj['id'])
    dels = unique(dels)
    preserves = unique(preserves)
    for pres in preserves:
        if pres in dels:
            dels.remove(pres)
    new_list = []
    for x in player_list:
        if x['id'] not in dels:
            new_list.append(x)
    return new_list


# 将球员id转换为球员名
def find_name_by_pid(roomid, pid):
    all_players = []
    all_players.extend(parse_data(roomid, 1)['player_list'])
    all_players.extend(parse_data(roomid, 2)['player_list'])
    all_players.extend(parse_data(roomid, 3)['player_list'])
    all_players.extend(parse_data(roomid, 4)['player_list'])
    all_players.extend(parse_data(roomid, 5)['player_list'])
    for i in all_players:
        if i['id'] == str(pid):
            return '{0}({1})'.format(i['name'], i['salary'])


# 查询历史得分
def get_history_score_by_team(pids, game_date):
    if len(pids) == 5:
        total_score = 0
        for pid in pids:
            url = 'https://fantasy.hupu.com/api/player/data/{0}'.format(pid)
            player_info = requests.get(url).text
            player_json = json.loads(player_info)
            for game in player_json['data']['last_ten_performance']:
                if game['start_time'] == game_date:
                    total_score += float(game['fantasy_score'])
                    break
        return round(total_score, 1)
    else:
        exit()


# 获取球员数据
def get_players_data(player_list):
    players_data = []
    for player in player_list:
        url = 'https://fantasy.hupu.com/api/player/data/{0}'.format(player)
        player_data = requests.get(url).text 
        player_json = json.loads(player_data)
        players_data.append(player_json['data'])
    return players_data


# 显示推荐条件
def show_conditions():
    if MIN_SALARY_SUM > 0 and MAX_SALARY_SUM > 0:
        print('队内工资总和范围：[{0}, {1}]'.format(MIN_SALARY_SUM, MAX_SALARY_SUM))
    if MIN_SALARY > 0 and MAX_SALARY > 0:
        print('队内单人工资范围：[{0}, {1}]'.format(MIN_SALARY, MAX_SALARY))
    if MAX_SALARY_DIFF > 0:
        print('队内最大工资差：{0}'.format(MAX_SALARY_DIFF))
    if len(AVOID_PLAYERS) > 0:
        print('规避球员为：{0}'.format(AVOID_PLAYERS))
    if len(PRESERVE_PLAYERS) > 0:
        print('保留球员为：{0}'.format(PRESERVE_PLAYERS))


# 计算球员评分效率
def calculate_efficiency(score, playtime):
    if int(playtime) == 0:
        return 0
    else:
        return score / playtime


# 自写list去重
def unique(lst):
    newlst = []
    for x in lst:
        if x not in newlst:
            newlst.append(x)
    return newlst


# 加载配置文件
def load_configuration():
    global MIN_SALARY_SUM
    global MAX_SALARY_SUM
    global MIN_SALARY
    global MAX_SALARY
    global MAX_SALARY_DIFF
    global MIN_SCORE
    global MIN_PLAYTIME
    global AVOID_PLAYERS
    global PRESERVE_PLAYERS
    global SHOW_PLAYERS_AMOUNT
    global ROOM_ID
    global ORDER_BY
    global USE_PRETTYTABLE
    global SHOW_HISTORY_SCORE
    global COOKIE
    global HEADER
    cp = configparser.ConfigParser()
    cp.read('f.conf')
    MIN_SALARY_SUM = int(cp.get('filter', 'min_salary_sum'))
    MAX_SALARY_SUM = int(cp.get('filter', 'max_salary_sum'))
    MIN_SALARY = int(cp.get('filter', 'min_salary'))
    MAX_SALARY = int(cp.get('filter', 'max_salary'))
    MAX_SALARY_DIFF = int(cp.get('filter', 'max_salary_diff'))
    MIN_SCORE = int(cp.get('filter', 'min_score'))
    MIN_PLAYTIME = int(cp.get('filter', 'min_playtime'))
    AVOID_PLAYERS = [] if cp.get('filter', 'avoid_players') == '' else cp.get('filter', 'avoid_players').split(',')
    PRESERVE_PLAYERS = [] if cp.get('filter', 'preserve_players') == '' else cp.get('filter', 'preserve_players').split(',')
    SHOW_PLAYERS_AMOUNT = int(cp.get('display', 'show_players_amount'))
    ROOM_ID = int(cp.get('display', 'room_id'))
    ORDER_BY = int(cp.get('display', 'order_by'))
    USE_PRETTYTABLE = int(cp.get('display', 'use_prettytable'))
    SHOW_HISTORY_SCORE = int(cp.get('display', 'show_history_score'))
    COOKIE = cp.get('others', 'cookie')
    HEADER = {'Cookie': COOKIE}


def run():
    load_configuration()
    rid = None
    if ROOM_ID == 0:
        rid = get_current_roomid()
        get_players(rid)
    else:
        rid = ROOM_ID
        curr_id = get_current_roomid()
        if curr_id is None:
            curr_id = -1
    posible = []
    s1 = shrink(parse_data(rid, 1)['player_list'])
    s2 = shrink(parse_data(rid, 2)['player_list'])
    s3 = shrink(parse_data(rid, 3)['player_list'])
    s4 = shrink(parse_data(rid, 4)['player_list'])
    s5 = shrink(parse_data(rid, 5)['player_list'])
    game_date = parse_data(rid, 1)['game_date']
    for l1 in s1:
        for l2 in s2:
            for l3 in s3:
                for l4 in s4:
                    for l5 in s5:
                        if (MIN_SALARY_SUM <= l1['salary'] + l2['salary'] + l3['salary'] + l4['salary'] + l5['salary'] <= MAX_SALARY_SUM) and \
                            (l1['score'] + l2['score'] + l3['score'] + l4['score'] + l5['score'] > MIN_SCORE) and \
                            (1 if MAX_SALARY_DIFF == 0 else (max(l1['salary'], l2['salary'], l3['salary'], l4['salary'], l5['salary']) - min(l1['salary'], l2['salary'], l3['salary'], l4['salary'], l5['salary']) <= MAX_SALARY_DIFF)) and \
                            (1 if len(PRESERVE_PLAYERS) == 0 else set(PRESERVE_PLAYERS) <= set([l1['name'], l2['name'], l3['name'], l4['name'], l5['name']])) and \
                            len(unique([l1['id'], l2['id'], l3['id'], l4['id'], l5['id']])) == 5:
                            posible.append([l1['id'], \
                            l2['id'], \
                            l3['id'], \
                            l4['id'], \
                            l5['id'], \
                            (l1['salary'] + l2['salary'] + l3['salary'] + l4['salary'] + l5['salary']), \
                            round(l1['score'] + l2['score'] + l3['score'] + l4['score'] + l5['score'], 1), \
                            (l1['playtime'] + l2['playtime'] + l3['playtime'] + l4['playtime'] + l5['playtime']), \
                            (round(calculate_efficiency(l1['score'], l1['playtime']) + calculate_efficiency(l2['score'], l2['playtime']) + calculate_efficiency(l3['score'], l3['playtime']) + calculate_efficiency(l4['score'], l4['playtime']) + calculate_efficiency(l5['score'], l5['playtime']), 3))]) 
    order_index = [6, 7, 8, 6]
    posible = sorted(posible, key=lambda x:-x[order_index[ORDER_BY]])
    if USE_PRETTYTABLE:
        order_table_head = ['总评分', '总时间', '总效率', 'ability']
        table_head = ['控球后卫', '得分后卫', '小前锋', '大前锋', '中锋', '总身价', order_table_head[ORDER_BY]]
        if SHOW_HISTORY_SCORE and int(ROOM_ID) > 0 and int(ROOM_ID) != int(curr_id):
            table_head.append('实际得分')
        pt = PrettyTable(table_head)
        for i in range(min(SHOW_PLAYERS_AMOUNT, len(posible))):
            table_row = [find_name_by_pid(rid, posible[i][0]), \
            find_name_by_pid(rid, posible[i][1]), \
            find_name_by_pid(rid, posible[i][2]), \
            find_name_by_pid(rid, posible[i][3]), \
            find_name_by_pid(rid, posible[i][4]), \
            posible[i][5], \
            posible[i][order_index[ORDER_BY]]]
            if SHOW_HISTORY_SCORE and int(ROOM_ID) > 0 and int(ROOM_ID) != int(curr_id):
                table_row.append(get_history_score_by_team([posible[i][0], posible[i][1], posible[i][2], posible[i][3], posible[i][4]], game_date))
            pt.add_row(table_row)
        print(pt)
        show_conditions()
    else:
        for i in range(SHOW_PLAYERS_AMOUNT):
            print(find_name_by_pid(rid, posible[i][0]), \
            find_name_by_pid(rid, posible[i][1]), \
            find_name_by_pid(rid, posible[i][2]), \
            find_name_by_pid(rid, posible[i][3]), \
            find_name_by_pid(rid, posible[i][4]), \
            posible[i][5], \
            posible[i][6])

if __name__ == '__main__':
    run()
