import ast
import datetime
import io
import sqlite3
from sqlite3 import Error
from time import sleep

import PySimpleGUI
from PIL import Image
import requests
from concurrent import futures


def convertToPNG(im: Image) -> Image:
    with io.BytesIO() as f:
        im.save(f, format='PNG')
        return f.getvalue()


def get_user_sum(key, user):
    try:
        global qx
        res = requests.get(
            f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={key}&steamids={user}'
        )
        while res.status_code == 429:
            sleep(0.5)
            res = requests.get(
                f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={key}&steamids={user}'
            )
        qx.append(2)
        player = res.json()['response']['players'][0]
        return player['personaname'], player['avatarfull']
    except Exception as er:
        print(er)


def get_games_json(key, user):
    try:
        res = requests.get(
            f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={key}&steamid={user}&include_appinfo=true&include_played_free_games=true&format=json'
        )
        while res.status_code == 429:
            sleep(0.5)
            res = requests.get(
                f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={key}&steamid={user}&include_appinfo=true&include_played_free_games=true&format=json'
            )
        res = res.json()
        return res
    except Exception as er:
        print(er)


def get_game_stats(ip, key, user, lg):
    b = True
    while b:
        try:
            res = requests.get(
                f'http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={ip}&key={key}&steamid={user}&l={lg}')
            sd = res.json()
            b = False
        except:
            sleep(0.01)
    b = True
    while b:
        try:
            res = requests.get(
                f"http://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid={ip}&format=json")
            sd_percentage = res.json()
            b = False
        except:
            sleep(0.01)
    b = True
    while b:
        try:
            res = requests.get(
                f"https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?appid={ip}&key={key}&l={lg}")
            sd_desc = res.json()
            b = False
        except:
            sleep(0.01)

    stats = sd['playerstats']
    try:
        res = requests.get(
            f'http://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid={ip}&key={key}&steamid={user}')
        sd_stats = res.json()
        sd_stats = sd_stats['playerstats']['stats']
    except:
        sd_stats = None
    try:
        uspex = stats['achievements']
    except:
        uspex = False
    if uspex:
        name = stats['gameName']
        ach = stats['achievements']
        ach_per = sd_percentage['achievementpercentages']["achievements"]
        ach_desc = sd_desc['game']['availableGameStats']['achievements']
        ach_list = []
        ach_list_tsr = []
        ach_list_per = []
        ach_list_ico = []
        ach_api = [i['name'] for i in ach_per]
        for i in ach:
            ach_list_tsr.append([i['apiname'], i['description'], i['achieved'], i['unlocktime'], i['name']])
        for i in ach_per:
            ach_list_per.append([i['name'], i['percent']])
        for i in ach_desc:
            ach_list_ico.append([i['name'], i['icon'], i['icongray']])
        ach_list_tsr = sorted(ach_list_tsr)
        ach_list_per = sorted(ach_list_per)
        ach_list_ico = sorted(ach_list_ico)
        q = 0

        for i in ach_list_tsr:
            try:
                if ach_list_tsr[q][0] not in ach_api:
                    ach_list_per.append([ach_list_per[q][0], 0])
                    ach_list_per = sorted(ach_list_per)
                    print(len(ach_list_per))
            except:
                pass

            perc = ach_list_per[q][1]
            achieved_icon = ach_list_ico[q][1]
            not_achieved_icon = ach_list_ico[q][2]
            unlock_time_un = i[3]
            if unlock_time_un != 0:
                unlock_time_norm = str(datetime.datetime.fromtimestamp(unlock_time_un))
            else:
                unlock_time_norm = 'нет'
            ach_list.append(
                [i[4], i[2], i[1], perc, unlock_time_norm, achieved_icon, not_achieved_icon, ach_list_tsr[q][0]])
            q += 1

        return name, ach_list, sd_stats
    else:
        return False


def fetch_img(url, used_id=None, session=None, size=(64, 64), to_ach_lay=False):
    if used_id:
        conn = sqlite3.connect('Steam_Ach_View.db')
        cursor = conn.cursor()
        st_ur = str(url)
        idg = st_ur[st_ur.rindex('s/') + 2:st_ur.rindex('/')]
        data_db = cursor.execute(f"SELECT * FROM games WHERE game_id={idg}")
        for i in data_db:
            if i:
                return i[1]
    if to_ach_lay:
        urls = url[5]
        if session:
            r = session.get(urls, timeout=60., stream=True).raw
        else:
            r = requests.get(urls, timeout=60., stream=True).raw
        return convertToPNG(Image.open(r).resize(size)), url[4], url[0], url[2], url[3], url[8]
    if len(url) == 2:
        url = url[0]
    elif len(url) == 5:
        url = url[2]
    if session:
        r = session.get(url, timeout=60., stream=True).raw
    else:
        r = requests.get(url, timeout=60., stream=True).raw
    return convertToPNG(Image.open(r).resize(size))


def fetch_all_img(urls, session=requests.session(), threads=16, size=(64, 64), used_id=None, to_ach_lay=False):
    with futures.ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_url = {
            executor.submit(fetch_img, url, used_id=used_id, session=session, size=size, to_ach_lay=to_ach_lay): url for
            url
            in urls}
        for future in futures.as_completed(future_to_url):
            url = future_to_url[future]
            if future.exception() is None:
                yield url, future.result()
            else:
                print(f"{url}g generated an exception: {future.exception()}")
                yield url, convertToPNG(Image.open('no-image.png'))


def fetch_game(i, key, user, lg):
    st = get_game_stats(i['appid'], key, user, lg)
    if st and st is not None:
        return {"name": st[0], "ach": st[1], "appid": i['appid'],
                'img_icon_url': 1, 'stats': st[2]}
    else:
        return None


def fetch_all_games(games, key, user, lg, threads=16):
    with futures.ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_url = {executor.submit(fetch_game, game, key, user, lg): game for game in games}
        for future in futures.as_completed(future_to_url):
            game = future_to_url[future]
            if future.exception() is None:
                yield game, future.result()
            else:
                print(f"{game} game generated an exception: {future.exception()}")
                yield None


s = []
qx = []


def fetch_game_bd(ip, key, steamid, lg):
    st = [ip[0], ip[1], get_game_stats(ip[0], key, steamid, lg)[0], ip[2], 0]
    return st


def fetch_games_bd(games, key, user, lg, threads=16):
    with futures.ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_url = {executor.submit(fetch_game_bd, game, key, user, lg): game for game in games}
        for future in futures.as_completed(future_to_url):
            friend = future_to_url[future]
            if future.exception() is None:
                yield future.result()
            else:
                print(f"{friend} generated an exception: {future.exception()}")
                yield None


def recently_update(key, user, lg):
    conn = sqlite3.connect('Steam_Ach_View.db')
    cursor = conn.cursor()
    res = requests.get(
        f'http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={key}&steamid={user}&format=json')
    res = res.json()['response']
    try:
        res = res['games']
        checked_recently_game = []
        for i in cursor.execute(f"select user_played_games from users WHERE user_id = {user}"):
            if i[0] != '  ':
                bd_recently_game = ast.literal_eval(i[0].replace('Ковычки', '"'))
            else:
                bd_recently_game = []
        cursor.execute(
            f"""UPDATE users SET user_played_games= "{str(res).replace('"', 'Ковычки')}" WHERE user_id = {user}""")
        for i in res:
            if str(i).replace('"', 'Ковычки') not in bd_recently_game:
                checked_recently_game.append(i)
    except Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        PySimpleGUI.Popup('Нет игр за 2 недели')
        return None
    except:
        PySimpleGUI.Popup('Нет игр за 2 недели')
        return None
    fetching_res = fetch_all_games(checked_recently_game, key, user, lg)
    for i in fetching_res:
        if i[1] is not None:
            cursor.execute("""UPDATE game_user SET achivments=? WHERE user_id = ? AND game_id = ?""",
                           (str(i[1]['ach']), user, i[1]['appid']))
    conn.commit()
    conn.close()


def get_steamId_by_name(name, key):
    res = \
        requests.get(
            f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={key}&vanityurl={name}').json()[
            'response']
    res = res['steamid']
    return res
