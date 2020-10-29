from typing import Dict, List

import discord
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
import datetime
import asyncio

from datetime import time, timedelta

import logging

logging.basicConfig(level=logging.INFO)

TOKEN = 'NzEzMDUyMjY0MDE2NzczMTQw.XsagyQ.P8S5MSpM13v5Ryj1tlcwayzjKV4'
url = 'https://bdobosstimer.com/?&server=ru&stream=1'
page = ''
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'))

INTERVALS = [15, 5, 1]
embs = [discord.Embed(color=0x00FF00), discord.Embed(color=0xFFA500),discord.Embed(color=0xFF0000)]
DayTimeSchedule = ['03:20', '06:40','07:20', '10:40', '11:20', '14:40','15:20', '18:40', '19:20', '22:40' , '23:20', '02:40']

table = []
for i in range(0, 7):
    table.append([])

def LoadTable(path):
    global page
    f = open(path, 'r')
    page = ''
    for line in f:
        page += line
    soup = BeautifulSoup(page, 'html.parser')
    tbl = soup.find(id='boss-table')
    scdl = []
    for td in tbl.thead.tr.find_all('td'):
        scdl.append(td.text)
    for i in range(0, 7):
        for j in range(1, len(scdl)):
            id = str(i) + '-' + scdl[j]
            data = soup.find(id=id)
            for d in data.find_all('span'):
                newData = [d.text, scdl[j]]
                table[i].append(newData)

LoadTable('table.html')

def CalculateDiff(a, b : time):
    return timedelta(hours=b.hour - a.hour, minutes=b.minute-a.minute, seconds=b.second-a.second).seconds

async def loopBosses(p : int, tempList : list, currTime : time):
    interval = INTERVALS[p]
    flag = False
    for boss in tempList:
        [hours, minutes] = boss[1].split(':')
        diff = CalculateDiff(currTime, datetime.time(hour=int(hours), minute=int(minutes)))
        if diff // 60 < interval:
            print('{0} появится через {1} минут'.format(boss[0], interval))
            flag = True
            for channel in bot.get_all_channels():
                if channel.type == discord.ChannelType.text and channel.topic == 'Bot channel':
                    fp = open('pics/' + boss[0] + '.png', 'rb')
                    file = discord.File(fp=fp)
                    embs[p].title = '{0} появится через {1} минут'.format(boss[0], diff//60 + 1)
                    await channel.send('{0} появится через {1} минут'.format(boss[0], diff//60 + 1), file=file, delete_after=30 * 60, embed=embs[p])
                    file.close()
                    fp.close()
    return flag


interval = 0

@tasks.loop(seconds = 10)
async def CheckBoss():
    global interval
    today = datetime.datetime.now()
    weekday = today.weekday()
    hour = today.hour
    minute = today.minute
    seconds = today.second
    #for channel in bot.get_all_channels():
    #    print(channel.name, channel.type)

    currTime = datetime.time(hour=hour, minute=minute,second=seconds)
    #print(weekday, hour, minute, seconds)
    tempList = list()
    if table[(weekday + 1) % 7][0][1] == '00:00':
        tempList.append(table[(weekday + 1) % 7][0])
    if table[(weekday + 1) % 7][1][1] == '00:00':
        tempList.append(table[(weekday + 1) % 7][1])
    for i in range(1, len(table[weekday])):
        if table[weekday][i][1] != '00:00':
            tempList.append(table[weekday][i])
    if await loopBosses(interval, tempList, currTime):
        interval += 1
        interval %= 3
        if(interval == 0):
            await asyncio.sleep(90)

@tasks.loop(minutes=1)
async def updateNightStatus():
    today = datetime.datetime.now()
    weekday = today.weekday()
    hour = today.hour
    minute = today.minute
    seconds = today.second
    # for channel in bot.get_all_channels():
    #    print(channel.name, channel.type)

    currentTime = datetime.time(hour=hour, minute=minute, second=seconds)
    min = 24*60*60
    idx = 0
    length = len(DayTimeSchedule)
    for i in range(0, length):
        [hours, minutes] = DayTimeSchedule[i].split(':')
        diff = CalculateDiff(currentTime, datetime.time(hour=int(hours), minute=int(minutes)))
        if diff < min:
            min = diff
            idx = i
    [hrsStart, minStart] = DayTimeSchedule[idx].split(':')
    diff = CalculateDiff(currentTime, datetime.time(hour=int(hrsStart), minute=int(minStart)))

    if idx % 2:
        await bot.change_presence(activity=discord.Game('BDO День закончится через {0}ч. {1} мин.'.format(min//3600, (min%3600)//60)))
    else:
        await bot.change_presence(activity=discord.Game('BDO Ночь закончится через {0}ч. {1} мин.'.format(min//3600, (min%3600)//60)))

@bot.event
async def on_ready():
    CheckBoss.start()
    updateNightStatus.start()
    print('Bot logged {0} as {0.id}'.format(bot.user))

@bot.command()
async def next(ctx):
    global interval
    today = datetime.datetime.now()
    weekday = today.weekday()
    hour = today.hour
    minute = today.minute
    seconds = today.second
    # for channel in bot.get_all_channels():
    #    print(channel.name, channel.type)

    currTime = datetime.time(hour=hour, minute=minute)
    # print(weekday, hour, minute, seconds)
    tempList = list()
    if table[(weekday + 1) % 7][0][1] == '00:00':
        tempList.append(table[(weekday + 1) % 7][0])
    if table[(weekday + 1) % 7][1][1] == '00:00':
        tempList.append(table[(weekday + 1) % 7][1])
    for i in range(1, len(table[weekday])):
        if table[weekday][i][1] != '00:00':
            tempList.append(table[weekday][i])
    bossesOut = []
    min = 25*60*60
    for boss in tempList:
        [hours, minutes] = boss[1].split(':')
        diff = CalculateDiff(currTime, datetime.time(hour=int(hours), minute=int(minutes)))
        if(diff < min):
            min = diff
            bossesOut.clear()
            bossesOut.append(boss)
        elif(diff == min):
            bossesOut.append(boss)
    for boss in bossesOut:
        fp = open('pics/' + boss[0] + '.png', 'rb')
        file = discord.File(fp=fp)
        await ctx.send('{0} появится через {1} минут'.format(boss[0], min // 60 + 1), file=file,
                           delete_after=30 * 60)
        file.close()
        fp.close()



bot.run(TOKEN)
#Lime, Orange, Red