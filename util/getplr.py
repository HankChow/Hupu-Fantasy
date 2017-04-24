#!/usr/bin/python3
# coding: utf-8

import os
import sys


def gt3300(n):
    if n > 3300:
        return False
    else:
        return True


def download(num):
    for i in range(1, 6):
        url = 'https://fantasy.hupu.com/api/player/candidates/{0}/{1}'.format(num, i)
        os.system('wget {0} -O {1}/{2}-{3}.plr'.format(url, sys.path[0], num, i))
    

if __name__ == '__main__':
    all_rooms = open('./all_rooms')
    lines = all_rooms.readlines()
    for i in range(len(lines)):
        lines[i] = int(lines[i].strip().split(' ')[1])
    lines = list(filter(gt3300, lines))
    for i in lines:
        download(i)
