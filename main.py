import ast
import datetime
import sqlite3
import webbrowser
from concurrent import futures
from io import BytesIO

import PySimpleGUI as sg
import requests
from PIL import Image

from post_get import get_steamId_by_name, fetch_all_games, fetch_all_img, \
    fetch_games_bd, get_games_json, get_game_stats, recently_update, \
    get_user_sum

# https://steamcommunity.com/profiles/76561198820929267
# МОЙ 76561198126403886
# 76561198286183724

key_f = open('key.ini','r')
key = key_f.readline()
key_f.close()
ach_data = None
user = ''
theme = ''
max_game = 0
max_ach = 0
lg = 'Russian'
d = ['Black', 'BlueMono', 'BluePurple', 'BrightColors', 'BrownBlue', 'Dark', 'Dark2', 'DarkAmber', 'DarkBlack',
     'DarkBlack1', 'DarkBlue', 'DarkBlue1', 'DarkBlue10', 'DarkBlue11', 'DarkBlue12', 'DarkBlue13', 'DarkBlue14',
     'DarkBlue15', 'DarkBlue16', 'DarkBlue17', 'DarkBlue2', 'DarkBlue3', 'DarkBlue4', 'DarkBlue5', 'DarkBlue6',
     'DarkBlue7', 'DarkBlue8', 'DarkBlue9', 'DarkBrown', 'DarkBrown1', 'DarkBrown2', 'DarkBrown3', 'DarkBrown4',
     'DarkBrown5', 'DarkBrown6', 'DarkBrown7', 'DarkGreen', 'DarkGreen1', 'DarkGreen2', 'DarkGreen3', 'DarkGreen4',
     'DarkGreen5', 'DarkGreen6', 'DarkGreen7', 'DarkGrey', 'DarkGrey1', 'DarkGrey10', 'DarkGrey11', 'DarkGrey12',
     'DarkGrey13', 'DarkGrey14', 'DarkGrey15', 'DarkGrey2', 'DarkGrey3', 'DarkGrey4', 'DarkGrey5', 'DarkGrey6',
     'DarkGrey7', 'DarkGrey8', 'DarkGrey9', 'DarkPurple', 'DarkPurple1', 'DarkPurple2', 'DarkPurple3', 'DarkPurple4',
     'DarkPurple5', 'DarkPurple6', 'DarkPurple7', 'DarkRed', 'DarkRed1', 'DarkRed2', 'DarkTanBlue', 'DarkTeal',
     'DarkTeal1', 'DarkTeal10', 'DarkTeal11', 'DarkTeal12', 'DarkTeal2', 'DarkTeal3', 'DarkTeal4', 'DarkTeal5',
     'DarkTeal6', 'DarkTeal7', 'DarkTeal8', 'DarkTeal9', 'Default', 'Default1', 'DefaultNoMoreNagging', 'GrayGrayGray',
     'Green', 'GreenMono', 'GreenTan', 'HotDogStand', 'Kayak', 'LightBlue', 'LightBlue1', 'LightBlue2', 'LightBlue3',
     'LightBlue4', 'LightBlue5', 'LightBlue6', 'LightBlue7', 'LightBrown', 'LightBrown1', 'LightBrown10',
     'LightBrown11', 'LightBrown12', 'LightBrown13', 'LightBrown2', 'LightBrown3', 'LightBrown4', 'LightBrown5',
     'LightBrown6', 'LightBrown7', 'LightBrown8', 'LightBrown9', 'LightGray1', 'LightGreen', 'LightGreen1',
     'LightGreen10', 'LightGreen2', 'LightGreen3', 'LightGreen4', 'LightGreen5', 'LightGreen6', 'LightGreen7',
     'LightGreen8', 'LightGreen9', 'LightGrey', 'LightGrey1', 'LightGrey2', 'LightGrey3', 'LightGrey4', 'LightGrey5',
     'LightGrey6', 'LightPurple', 'LightTeal', 'LightYellow', 'Material1', 'Material2', 'NeutralBlue', 'Purple',
     'Python', 'PythonPlus', 'Reddit', 'Reds', 'SandyBeach', 'SystemDefault', 'SystemDefault1', 'SystemDefaultForReal',
     'Tan', 'TanBlue', 'TealMono', 'Topanga']
# Settings for you to modify are the size of the element, the circle width & color and the font for the % complete
GRAPH_SIZE = (75 , 75)          # this one setting drives the other settings
CIRCLE_LINE_WIDTH, LINE_COLOR = 3, 'black'
TEXT_FONT = 'Courier'


# Computations based on your settings above
TEXT_HEIGHT = GRAPH_SIZE[0]//4
TEXT_LOCATION = (GRAPH_SIZE[0]//2, GRAPH_SIZE[1]//2)
TEXT_COLOR = LINE_COLOR

# DarkGrey2 , BrightColors ,GrayGrayGray
def update_meter(graph_elem, percent_complete):
    """
    Update a circular progress meter
    :param graph_elem:              The Graph element being drawn in
    :type graph_elem:               sg.Graph
    :param percent_complete:        Percentage to show complete from 0 to 100
    :type percent_complete:         float | int
    """
    graph_elem.erase()
    arc_length = percent_complete/100*360+.9
    if arc_length >= 360:
        arc_length = 359.9
    graph_elem.draw_arc((CIRCLE_LINE_WIDTH, GRAPH_SIZE[1] - CIRCLE_LINE_WIDTH), (GRAPH_SIZE[0] - CIRCLE_LINE_WIDTH, CIRCLE_LINE_WIDTH),
                   arc_length, 0, 'arc', arc_color=LINE_COLOR, line_width=CIRCLE_LINE_WIDTH)
    percent = percent_complete
    graph_elem.draw_text(f'{percent}%', TEXT_LOCATION, font=(TEXT_FONT, -TEXT_HEIGHT+2), color=TEXT_COLOR)

def convertToPNG(im):
    with BytesIO() as f:
        im.save(f, format='PNG')
        return f.getvalue()


last_aches = []


def geting_last_ach(game, game_id):
    global last_aches
    for i in game:
        if i[1]:
            q = list(i)
            q.append(game_id)
            last_aches.append(q)


def get_last_ach(games, threads=8):
    with futures.ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_url = {executor.submit(geting_last_ach, game[1], game[0]): game for game in games}
        for _ in futures.as_completed(future_to_url):
            pass


def get_ach_quantity():
    data = ach_data
    quantity = 0
    for i in data:
        for j in i[1]:
            if j[1]:
                quantity += 1
    return quantity


def get_percent_at_game(ach_list):
    gain = 0
    ach_all = 0
    achived = False
    for j in ach_list:
        if j[1]:
            gain += 1
        ach_all += 1
    perc = (gain / ach_all) * 100
    if gain > 0:
        achived = True
    return perc, achived, gain, ach_all


def get_percen_at_js():
    try:
        data = ach_data
        per = []
        for i in data:
            percen = get_percent_at_game(i[1])[0]
            if percen != 0:
                per.append(percen)
        percen = sum(per) / len(per)
        return percen
    except:
        return 0


def sort_by_key(key, list, rev=False):
    list = sorted(list, key=lambda x: 1 if x[key] == 'получено' else 0 if x[key] == 'не получено' else x[key],
                  reverse=rev)
    return list


def sort_by_time(key, list, rev=False):
    list = sorted(list, key=lambda x: datetime.datetime.strptime(x[key].replace('нет', '1969-06-18 14:53:32'),
                                                                 '%Y-%m-%d %H:%M:%S'), reverse=rev)
    return list


def get_ach_from_bd(user):
    global last_aches
    last_aches = []
    conn = sqlite3.connect('Steam_Ach_View.db')
    cursor = conn.cursor()
    game = []
    for i in cursor.execute(f"SELECT * FROM game_user WHERE user_id={user}"):
        s = i[2].replace('[[', '[').replace(']]', ']').replace('], [', '] [').split('] [')
        ach = []
        for j in s:
            if j.find(']') < len(j) - 2:
                j += ']'
            ach.append(ast.literal_eval(('[' + j).replace('[[', '[').replace(' ]', '')))
        stats = 'Нет'
        if i[3] != 'None':
            stats = i[3]
        game.append([i[0], ach, stats])
    get_last_ach(game)
    last_aches = sort_by_time(4, last_aches, True)
    conn.close()
    return game


def get_ach_img(js_of_game):
    conn = sqlite3.connect("Steam_Ach_View.db")
    cursor = conn.cursor()
    def appid_from_url(url):
        idr = url[0][0]
        idr = idr[idr.find('apps/') + 5:]
        idr = idr[:idr.find('/')]
        return idr
    def update_ins(list_url,list_ach,str_img):
        for i in fetch_all_img(list_url):
            idr = appid_from_url(i)
            try:

                cursor.execute(f"insert into achivments (game_id,ach_id,{str_img}) values(?,?,?)",
                               (idr, i[0][1], i[1]))
                conn.commit()
            except:
                cursor.execute(f"update achivments set {str_img} =? where game_id = ? and ach_id = ?",
                               (i[1], idr, i[0][1]))
                conn.commit()
            list_ach.append([i[0], i[1]])
    lis = []
    urls = []
    urls_n = []
    ach_ico = []
    n_ach_ico = []
    to_do = []
    for i in js_of_game:
        check = 'no'
        for j in cursor.execute(f'select * from achivments where game_id = {i[-1]} and ach_id = "{i[-2]}"'):
            if i[1] and j[2] is not None:
                lis.append([i[0], 'получено', i[2], i[3], i[4], j[2]])
                check = "se"
            elif not i[1] and j[3] is not None:
                lis.append([i[0], 'не получено', i[2], i[3], i[4], j[3]])
                check = "se"

        if check == 'no':
            if len(i) == 6:
                lis.append(i)
            else:
                if i[1] == 1:
                    urls.append([i[5], i[7]])
                elif i[1] == 0:
                    urls_n.append([i[6], i[7]])
                to_do.append(i)
    update_ins(urls,ach_ico,'getet_img')
    update_ins(urls_n,n_ach_ico,'not_getet_img')
    conn.close()
    for i in to_do:
        if i[1]:
            for j in ach_ico:
                if j[0][0] == i[5]:
                    achiv = j[1]
                    break
            lis.append([i[0], 'получено', i[2], i[3], i[4], achiv])
        else:
            for j in n_ach_ico:
                if j[0][0] == i[6]:
                    achiv = j[1]
                    break
            lis.append([i[0], 'не получено', i[2], i[3], i[4], achiv])
    return lis


def get_lis_ach_img_games():
    conn = sqlite3.connect('Steam_Ach_View.db')
    cursor = conn.cursor()
    data_db = cursor.execute(f"SELECT * FROM games")
    used_id = []
    for i in data_db:
        used_id.append(i[0])
    data = ach_data
    games = []
    for i in data:
        game_data = get_percent_at_game(i[1])
        date = datetime.datetime(1900, 1, 1)
        for j in i[1]:
            if j[4] != 'нет':
                date_f = j[4].split('-')
                date_h = j[4].split()[1].split(':')

                date_c = datetime.datetime(int(date_f[0]), int(date_f[1]), int(date_f[2][:2]), int(date_h[0]),
                                           int(date_h[1]), int(date_h[2]))
                if date < date_c:
                    date = date_c
        name = ''
        for j in cursor.execute(f"SELECT * FROM games WHERE game_id = {i[0]}"):
            name = j[2]
        games.append([int(i[0]), name, round(game_data[0], 2),
                      game_data[2], game_data[3] - game_data[2], game_data[3], i, date, i[2]])
    games = sort_by_key(0, games)
    urls = []
    for i in data:
        urls.append(f"https://steamcdn-a.akamaihd.net/steam/apps/{i[0]}/capsule_sm_120.jpg")
    conn.close()
    logo = fetch_all_img(urls, size=(133, 50), used_id=used_id)
    logo_with_appid = []
    for i in logo:
        appid = i[0][:i[0].rindex('/')]
        appid = appid[appid.rindex("/") + 1:]
        logo_with_appid.append([int(appid), i[1], i[0]])
    logo_with_appid = sort_by_key(0, logo_with_appid)
    conn = sqlite3.connect('Steam_Ach_View.db')
    cursor = conn.cursor()
    q = 0
    game_to_bd = []
    for i in games:
        if i[0] not in used_id:
            game_to_bd.append([i[0], logo_with_appid[q][1], f'{i[2]} {i[3]} {i[4]} {i[5]} {i[7]}'])
        i.append(logo_with_appid[q][1])
        q += 1
    to_simp = fetch_games_bd(game_to_bd, key, user, lg)
    for i in to_simp:
        cursor.execute("INSERT INTO games VALUES (?,?,?)", (i[0], i[1], i[2]))
    for i in games:
        if i[0] not in used_id:
            for j in cursor.execute(f"SELECT * FROM games WHERE game_id = {i[0]}"):
                name = j[2]
            i[1] = name
    conn.commit()
    conn.close()
    return games


def update_one_game(js):
    conn = sqlite3.connect('Steam_Ach_View.db')
    cursor = conn.cursor()
    new_js = get_game_stats(js[0], key, user, lg)
    cursor.execute(f"UPDATE game_user SET achivments = ? WHERE user_id = ? AND game_id = ?",
                   (str(new_js[1]), int(user), js[0]))
    conn.commit()
    conn.close()
    for i in new_js[1]:
        i.append(js[0])
    js[1] = new_js[1]
    return js


def get_list_of_name_ach_games(win=None):  # главная функция
    conn = sqlite3.connect('Steam_Ach_View.db')
    cursor = conn.cursor()
    js = get_games_json(key=key, user=user)
    games = js['response']['games']
    count = len(games)
    adding = 999 / count
    pr = 0
    q = 0
    data = []
    for i in fetch_all_games(games, key, user, lg):
        pr += adding
        q += 1
        if win is not None:
            win['Progress'].update(pr)
            win['Progresstxt'].update(f'{q}/{count}')
        if i[1]:
            check = cursor.execute(f"SELECT * FROM game_user WHERE game_id={i[1]['appid']} AND user_id={int(user)}")
            checked = True
            ach = ""
            for _ in i[1]['ach']:
                ach += str(_) + ' '
            for j in check:
                if j:
                    checked = False
                    cursor.execute("""UPDATE game_user SET achivments=?, stats=? WHERE user_id = ? AND game_id = ?""",
                                   (ach, str(i[1]['stats']), user, i[1]['appid']))
            if checked:
                cursor.execute(f'''INSERT INTO game_user VALUES (?,?,?,?)''',
                               (i[1]['appid'], user, ach, str(i[1]['stats'])))
            data.append(i[1])
    conn.commit()
    conn.close()


def start_wind(from_opt=False):
    global key, ach_data, user, theme, max_game, max_ach,TEXT_COLOR,LINE_COLOR
    try:
        f = open('id.ini', 'r')
        user = f.readline()
        theme = f.readline()
        theme = theme[:len(theme) - 1]
        sg.theme(theme)
        max_game = int(f.readline())
        max_ach = int(f.readline())
        color_perc = f.readline()
        if color_perc:
            TEXT_COLOR=LINE_COLOR=color_perc
        f.close()
        if not from_opt:
            sg.Popup('Происходит обновление игр в которые вы играли за последние 2 недели', auto_close=True,
                     auto_close_duration=1)
            recently_update(key, user, lg)
            ach_data = get_ach_from_bd(user)
            ach_data = ach_data

    except:
        options_wind()
    main_wind()


# except:
#   options_wind()


def write_theme_and_id(theme_v, id_user, max_games_to_show, mach,color_perc):
    global user, max_ach, max_game
    f = open('id.ini', 'w')
    f.write(str(int(id_user)))
    f.write('\n')
    if theme_v != '':
        sg.theme(theme_v)
        f.write(theme_v)
    else:
        f.write(theme)
    f.write('\n')
    f.write(str(int(max_games_to_show)))
    f.write('\n')
    f.write(str(int(mach)))
    f.write('\n')
    f.write(str(color_perc))

    user, max_ach, max_game, LINE_COLOR, TEXT_COLOR = int(id_user), mach, max_games_to_show,color_perc,color_perc
    f.close()


def options_wind(win_to_clo=None):
    global user, d, theme, ach_data
    conn = sqlite3.connect('Steam_Ach_View.db')
    cursor = conn.cursor()
    users = cursor.execute("select user_id, user_name from users")
    user_dict = {}
    name = []
    for i in users:
        user_dict[i[1]] = i[0]
        name.append(i[1])
    conn.close()
    layout = [
        [sg.Combo(values=name, tooltip='Введите steamid или ссылку на ваш профиль', key='id', size=(30, 5),
                  enable_events=True)],
        [sg.Combo(values=d, key='theme',readonly=True)],
        [sg.Text('Цвет процентов достижений'), sg.Combo(readonly=True,values=['black','white','yellow','green','blue','orange'],default_value=LINE_COLOR,key='color_perc')],
        [sg.Text('Кол-во показываемых достижений', size=(27, 1)),
         sg.Slider(range=(1, 400), size=(30, 5), orientation='h', default_value=max_ach, key='Mach')],
        [sg.Text('Кол-во показываемых игр', size=(27, 1)),
         sg.Slider(range=(1, 400), size=(30, 5), orientation='h', default_value=max_game, key='M game')],
        [sg.Button('Применить'), sg.Button('Принять')],
        [sg.ProgressBar(max_value=999, key='Progress', visible=False, size=(30, 5)), sg.Text(key='Progresstxt')]
    ]
    windows = sg.Window('Настройки', layout, finalize=True)
    windows['id'].update(user)
    windows['theme'].update(theme)
    while True:
        event, values = windows.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'id':
            windows['id'].update(user_dict[values['id']])
        elif event == 'Применить':
            if values['theme']:
                theme = values['theme']
                sg.theme(theme)
                write_theme_and_id(theme, user, values['M game'], values['Mach'], values['color_perc'])
                windows.close()
                options_wind(win_to_clo)

        elif event == 'Принять':
            try:

                if str(values['id']).find('id') != -1:
                    user_val = get_steamId_by_name(values['id'][values['id'].rindex('id/') + 3:], key).replace('/', '')
                elif str(values['id']).find('profiles') != -1:
                    user_val = values['id'][values['id'].rindex('profiles/') + 9:].replace('/', '')
                else:
                    user_val = values['id']
                another_id = False
                if user != user_val:
                    another_id = True
                write_theme_and_id(values['theme'], user_val, values['M game'], values['Mach'], values['color_perc'])
                conn = sqlite3.connect('Steam_Ach_View.db')
                cursor = conn.cursor()
                check = True
                for _ in cursor.execute(f"Select * from users where user_id ={user_val}"):
                    check = False
                user = user_val + '\n'
                if another_id and check:
                    windows['Progress'].update(visible=True)
                    get_list_of_name_ach_games(windows)
                    windows['Progress'].update(visible=False)
                ach_data = get_ach_from_bd(user)
                if win_to_clo is not None:
                    win_to_clo.close()
                windows.close()

                start_wind(True)
            except NameError:
                print(NameError)

            except ValueError:
                print(ValueError)

            except IOError:
                print(IOError)

            except:
                sg.Popup('проверьте соединение, верность написания steamid или доступность данных этого пользователя')


def main_wind(win_to_close=None):
    global ach_data, last_aches
    conn = sqlite3.connect('Steam_Ach_View.db')
    cursor = conn.cursor()
    check = cursor.execute(f"SELECT * FROM users WHERE user_id={user}")
    checked = True
    data_from_db = None
    for i in check:
        if i:
            data_from_db = i
            checked = False

    if checked:
        player_wn = get_user_sum(key, user)
        name_db = player_wn[0]
        jpg_data = Image.open(requests.get(player_wn[1], stream=True).raw)
        png_data = convertToPNG(jpg_data)
    else:
        name_db = data_from_db[1]
        png_data = data_from_db[2]
    ach_img_to_lay = []
    img = fetch_all_img(last_aches[:42], size=(48, 48), to_ach_lay=True)
    for i in img:
        ach_img_to_lay.append(i[1])
    ach_img_to_lay = sort_by_time(1, ach_img_to_lay, rev=True)
    q = -1
    ach_lay = []
    try:
        for _ in range(36):
            perc = ach_img_to_lay[_][4]
            color_back = ''
            if _ % 6 == 0:
                ach_lay.append([])
                q += 1
            if perc > 59.9:
                color_back = '#347c17'
            elif 25 <= perc <= 59.9:
                color_back = '#38d131'
            elif 7 <= perc < 25:
                color_back = '#00ffff'
            elif 2 <= perc < 7:
                color_back = '#b23aee'
            elif perc < 2:
                color_back = '#e56717'
            ach_lay[q].append(sg.Image(data=ach_img_to_lay[_][0], size=(56.25, 56.25), background_color=color_back,
                                       tooltip=f'{ach_img_to_lay[_][1]}\n{ach_img_to_lay[_][2]}\n{ach_img_to_lay[_][3]}'))
    except:
        pass
    layout = [[
        sg.Frame('', layout=[
            [sg.Text(name_db, key='Name')],
            [sg.Image(data=png_data, key='avatar')],
            [sg.Text('Профиль в стим', key=f"https://steamcommunity.com/profiles/{user}",
                     enable_events=True),
             sg.Text('Игры', key=f"https://steamcommunity.com/profiles/{user}/games",
                     enable_events=True)],
            [sg.Button('Список игр с достижениями'), sg.Button('Все достижения'),
             sg.Button('Обновить список игр'),
             sg.Button('Настройки')],
            [sg.Text(f'Средний процент достижений: {round(get_percen_at_js(), 2)}', key="percent"),sg.Graph(GRAPH_SIZE, (0,0), GRAPH_SIZE, key='-GRAPH-')],
            [sg.Text(f'Всего достижений: {get_ach_quantity()}', key="ach")],
            [sg.ProgressBar(max_value=999, orientation='h', size=(30, 10), key='Progress', visible=False),
             sg.Text(key='Progresstxt')],
        ], border_width=0),
        sg.Frame('', layout=ach_lay, border_width=0)]
    ]
    use_db = user[:len(user)]
    if checked:
        name_db = player_wn[0]
        use_ava_db = png_data
        get_list_of_name_ach_games()
        ach_data = get_ach_from_bd(user)
        ach_data = ach_data
        cursor.execute('''INSERT INTO users VALUES (?,?,?,?,?,?)''',
                       (use_db, name_db, use_ava_db, round(get_percen_at_js(), 2), get_ach_quantity(), '  '))
    else:
        cursor.execute("""UPDATE users SET user_percentage=? and user_ach = ? WHERE user_id = ?""",
                       (round(get_percen_at_js(), 2), get_ach_quantity(), use_db))

    conn.commit()
    window_main = sg.Window('Основное окно', layout, size=(1500, 600))
    if win_to_close is not None:
        win_to_close.close()
    while True:
        event, values = window_main.read(timeout=10)
        update_meter(window_main['-GRAPH-'], round(get_percen_at_js(), 2))
        if event == sg.WIN_CLOSED:
            conn.close()
            break
        elif event == 'Все достижения':
            conn.close()
            show_window_with_ach_game(window_main, [None, last_aches], len(last_aches), to_main=True, sort=-4)
        elif event == 'Список игр с достижениями':
            conn.close()
            show_window_with_ach(window_main)
        elif event.startswith('http'):
            webbrowser.open(event, new=0)
        elif event == 'Обновить список игр':
            conn.close()
            window_main['Progress'].update(visible=True)
            window_main['Progresstxt'].update(visible=True)
            get_list_of_name_ach_games(window_main)
            ach_data = get_ach_from_bd(user)
            ach_data = ach_data
            window_main['Progress'].update(visible=False)
            window_main['Progresstxt'].update(visible=False)
            new_perc = round(get_percen_at_js(), 2)
            new_ach = get_ach_quantity()
            window_main["percent"].update(f'steam percent: {new_perc}')
            window_main["ach"].update(f'Всего достижений: {new_ach}')
            conn = sqlite3.connect('Steam_Ach_View.db')
            cursor = conn.cursor()
            cursor.execute("""UPDATE users SET user_percentage= ? and user_ach = ? WHERE user_id = ?""",
                           (new_perc, new_ach, use_db))
            conn.commit()
            conn.close()
            sg.popup("Обновление окончено")
        elif event == 'Настройки':
            conn.close()
            options_wind(window_main)


def show_window_with_ach(win_to_close):
    def perc(games):
        perc = games[2]
        txt_st_col = "Red"
        stats = "Нет"
        if perc == 100:
            txt_col = '#b23aee'
        if 100 > perc >= 75:
            txt_col = '#42BED8'
        elif 75 > perc >= 50:
            txt_col = '#2a96ff'
        elif 50 > perc >= 25:
            txt_col = '#38d131'
        elif 0 < perc < 25:
            txt_col = '#347c17'
        elif perc == 0:
            txt_col = 'Red'
        if games[8] != "Нет":
            stats = "Есть"
            txt_st_col = "#b23aee"
        return stats, txt_col, txt_st_col

    sort = ""
    games = get_lis_ach_img_games()
    games = sort_by_key(7, games, True)
    col = [
        [sg.Text('Лого', size=16), sg.Text('Название', size=40, enable_events=True, key='name'),
         sg.Text('              %', size=15, enable_events=True, key='procent'),
         sg.Text('Есть', size=4, enable_events=True, key='Полученные'),
         sg.Text('Осталось', size=10, enable_events=True, key='не полученные'),
         sg.Text('Все в игре', size=9, enable_events=True, key='всего'),
         sg.Text('Есть статистика?', size=20, enable_events=True, key='статистика')]
    ]

    q = 0
    progres_bar_app = []

    viewed = 0
    curent = 0

    def update_window(wind, q, viewed, games):

        if q[0] + viewed > len(games):
            viewed = len(games) - q[0] - 1
        for i in q:
            stats, txt_col, txt_st_col = perc(games[i + viewed])
            wind[f'img{i}'].update(data=games[i + viewed][9], size=(133, 50))
            wind[f"name{i}"].update(games[i + viewed][1], text_color=txt_col)
            wind[f"progress{i}"].update(bar_color=(txt_col, 'black'))
            wind[f"progress{i}"].update(games[i + viewed][2])
            wind[f"progress{i}"].set_tooltip(games[i + viewed][2])
            wind[f"getet{i}"].update(games[i + viewed][3], text_color=txt_col)
            wind[f"to_done{i}"].update(games[i + viewed][4], text_color=txt_col)
            wind[f"all{i}"].update(games[i + viewed][5], text_color=txt_col)
            wind[f"stats{i}"].update(stats, text_color=txt_st_col)
        return q[-1] + viewed

    q_list = []
    for i in range(len(games) - viewed):
        stats, txt_col, txt_st_col = perc(games[i + viewed])
        col.append(
            [sg.Image(data=games[i + viewed][9], size=(133, 50), key=f'img{q}', enable_events=True),
             sg.Text(games[i + viewed][1], size=40, text_color=txt_col, key=f"name{q}"),
             sg.ProgressBar(max_value=100, size=(10, 4), bar_color=(txt_col, 'black'), key=f"progress{q}"),
             sg.Text(games[i + viewed][3], size=6, text_color=txt_col, key=f"getet{q}"),
             sg.Text(games[i + viewed][4], size=10, text_color=txt_col, key=f"to_done{q}"),
             sg.Text(games[i + viewed][5], size=9, text_color=txt_col, key=f"all{q}"),
             sg.Text(stats, size=20, text_color=txt_st_col, key=f"stats{q}", enable_events=True)]
        )
        progres_bar_app.append((f"progress{q}", games[i + viewed][2]))
        q_list.append(q)
        q += 1
        curent += 1
        if curent % max_game == 0:
            break
    buttons = [sg.Button('Назад')]
    layout = [
        buttons,
        [sg.Column(col, scrollable=True, vertical_scroll_only=True, size=(950, 650))]
    ]

    buttons.append(sg.Button('<-----------', key="Предыдущая страница"))
    buttons.append(sg.Button('----------->', key="Следующая страница"))

    layout[1].append(
        sg.Table(values=[], headings=['Статистика', 'Значение'], justification='left', auto_size_columns=False,
                 def_col_width=30, size=(700, 100), key="TABLE", visible=False))

    window_ach = sg.Window('Игры с достижениями', layout=layout, size=(1500, 700), finalize=True)
    table = window_ach["TABLE"]
    table_widget = table.Widget
    for i in progres_bar_app:
        window_ach[i[0]].update(i[1])
        window_ach[i[0]].set_tooltip(i[1])
    win_to_close.close()
    while True:
        event, values = window_ach.read()
        if event == sg.WIN_CLOSED:
            break
        if event.startswith('img'):
            show_window_with_ach_game(window_ach, games[int(event[3:]) + viewed][6],
                                      getet_ach=games[int(event[3:]) + viewed][3],
                                      game_id=games[int(event[3:]) + viewed][0])
        elif event.startswith('stats'):
            table_stats_value = []
            ms, mz = '', ''
            for i in ast.literal_eval(games[int(event.replace('stats', '')) + viewed][8]):
                name = i['name']
                value = i['value']
                table_stats_value.append([name, value])
                if len(name) > len(ms):
                    ms = name
                if len(str(value)) > len(mz):
                    mz = str(value)
            window_ach['TABLE'].update(values=table_stats_value, visible=True)
            table_widget.column('Статистика', width=7 * len(ms) + 40 * int(len(ms) < 20))
            table_widget.column('Значение', width=12 * len(mz) + 10 * int(len(mz) < 3))
        elif event == 'Назад':
            main_wind(window_ach)
        elif event == 'Предыдущая страница':
            if viewed > 0 and max_game < len(games):
                viewed -= max_game
                if viewed < 0:
                    viewed = 0
                viewed = update_window(window_ach, list(reversed(q_list)), viewed, games)
        elif event == 'Следующая страница':
            if curent != 0 and curent != len(games):
                viewed += max_game
                if viewed > len(games):
                    viewed = len(games) - q_list[len(q_list) - 1]
                viewed = update_window(window_ach, list(reversed(q_list)), viewed, games)
        elif event == 'name':
            if sort == 1:
                games = sort_by_key(1, games, True)
                sort = ''
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
            else:
                games = sort_by_key(1, games)
                sort = 1
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
        elif event == 'procent':
            if sort == 2:
                games = sort_by_key(2, sort_by_key(1, games))
                sort = -2
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
            else:
                games = sort_by_key(2, sort_by_key(1, games), True)
                sort = 2
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
        elif event == 'Полученные':
            if sort == 3:
                games = sort_by_key(3, sort_by_key(1, games))
                sort = -3
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
            else:
                games = sort_by_key(3, sort_by_key(1, games), True)
                sort = 3
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
        elif event == 'не полученные':
            if sort == 4:
                games = sort_by_key(4, sort_by_key(1, games))
                sort = -4
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
            else:
                games = sort_by_key(4, sort_by_key(1, games), True)
                sort = 4
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
        elif event == 'всего':
            if sort == 5:
                games = sort_by_key(5, sort_by_key(1, games))
                sort = -5
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
            else:
                games = sort_by_key(5, sort_by_key(1, games), True)
                sort = 5
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
        elif event == 'статистика':
            if sort == 8:
                games = sort_by_key(8, sort_by_key(1, games), True)
                sort = -8
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)
            else:
                games = sort_by_key(8, sort_by_key(8, games))
                sort = 8
                viewed = update_window(window_ach, list(reversed(q_list)), 0, games)


def show_window_with_ach_game(win_to_close, js_of_game, getet_ach, game_id=None, lis_per=None, sort=None,
                              to_main=None):
    def percent(games):
        perc = round(games[3], 2)
        if perc > 59.9:
            color_back = '#347c17'
        elif 25 <= perc <= 59.9:
            color_back = '#38d131'
        elif 7 <= perc < 25:
            color_back = '#00ffff'
        elif 2 <= perc < 7:
            color_back = '#b23aee'
        elif perc < 2:
            color_back = '#e56717'
        desc = games[2]
        kol_space = len(desc) // 115
        if kol_space == 0:
            desc = '\n' + desc
        return perc, color_back, desc

    def update_wind(wind, viewed, q, lis):
        for i in reversed(q):
            if i + viewed > len(lis):
                viewed = len(lis) - i - 1
            perc, color_back, desc = percent(lis[i + viewed])
            wind[f"img{i}"].update(data=lis[i + viewed][5], size=(64, 64))
            wind["kolvo"].update(f"{viewed}-{viewed + len(q)}")
            wind[f"img{i}"].ParentRowFrame.config(background=color_back)
            wind[f"fr{i}"].Widget.config(background=color_back)
            wind[f"fr{i}"].Widget.config(highlightbackground=color_back)
            wind[f"fr{i}"].Widget.config(highlightcolor=color_back)
            wind[f"have{i}"].update('\n' + str(lis[i + viewed][1]))
            wind[f"name{i}"].update('\n' + str(lis[i + viewed][0]))
            wind[f"desc{i}"].update(desc)
            wind[f"perc{i}"].update('\n' + str(perc))
            wind[f"date{i}"].update('\n' + str(lis[i + viewed][4]))

    if lis_per is None and sort is None:
        lis = sort_by_key(1, sort_by_key(3, js_of_game[1], True), True)
        for i in lis:
            if i[-1] == game_id:
                break
            i.append(game_id)
    elif sort == -4 and to_main:
        lis = js_of_game[1]
    lis = get_ach_img(lis)
    to_col_add = [sg.Text("logo", size=(9, 1)),
                  sg.Text('Есть?', size=(11, 1), enable_events=True),
                  sg.Text('Имя', size=(30, 1), enable_events=True),
                  sg.Text('Описание', size=(100, 1), enable_events=True),
                  sg.Text('%', size=(5, 1), enable_events=True, ),
                  sg.Text('Дата открытия', size=(12, 1), enable_events=True)]
    column_data = [to_col_add]
    curent = 0
    viewed = curent
    q_list = []
    q = 0
    for i in range(len(lis) - viewed):
        perc, color_back, desc = percent(lis[i + viewed])
        column_data.append(
            [sg.Frame('', [[sg.Image(data=lis[i + viewed][5], size=(64, 64), key=f"img{q}")]],
                      background_color=color_back, key=f'fr{q}'),
             sg.Text('\n' + str(lis[i + viewed][1]), size=(12, 4), key=f"have{q}"),
             sg.Text('\n' + str(lis[i + viewed][0]), size=(30, 4), key=f"name{q}"),
             sg.Text(desc, size=(100, 4), key=f"desc{q}"),
             sg.Text('\n' + str(perc), size=(5, 4), key=f"perc{q}"),
             sg.Text('\n' + str(lis[i + viewed][4]), size=(10, 4), key=f"date{q}")])
        q_list.append(q)
        curent += 1
        q += 1
        if curent % max_ach == 0:
            break
    pred_sled = [sg.Button('<-----------', key="Предыдущая страница"),
                 sg.Button('----------->', key="Следующая страница")]
    buttons = [sg.Button('Назад'), sg.Text(f'Полученных достижений {getet_ach}'),
               sg.Text(f'{viewed + 1}-{curent}', key="kolvo")]
    if js_of_game[0]:
        buttons.append(sg.Button('Обновить'))
    layout = [buttons,
              [sg.Column(column_data, key='col', scrollable=True, vertical_scroll_only=True, size=(1460, 600))]]

    if curent >= max_ach:
        layout.append(pred_sled)
    conn = sqlite3.connect('Steam_Ach_View.db')
    cursor = conn.cursor()
    name = ''
    if js_of_game[0]:
        for i in cursor.execute(f"SELECT * FROM games WHERE game_id={js_of_game[0]}"):
            name = i[2]
    else:
        name = 'Все достижения'
    window = sg.Window(name, layout, size=(1500, 700), finalize=True)
    win_to_close.close()

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'Назад':
            if to_main:
                main_wind(window)
            else:
                show_window_with_ach(window)
        elif event == 'Обновить':
            lis = update_one_game(js_of_game)[1]
            lis = get_ach_img(lis)
            update_wind(window, viewed, q_list, lis)

        elif event == 'Предыдущая страница':
            if viewed > 0:
                viewed -= max_ach
                if viewed < 0:
                    viewed = 0
                update_wind(window, viewed, q_list, lis)
        elif event == 'Следующая страница':
            if curent != 0 and curent != len(lis):
                viewed += max_ach
                if viewed > len(lis):
                    viewed = len(lis) - max_ach
                update_wind(window, viewed, q_list, lis)
        elif event == 'Есть?':
            if sort != -1:
                viewed = 0
                lis = sort_by_key(1, lis, True)
                sort = -1
                update_wind(window, viewed, q_list, lis)
            else:
                viewed = 0
                lis = sort_by_key(1, lis)
                sort = 1
                update_wind(window, viewed, q_list, lis)
        elif event == 'Имя':
            if sort != 0:
                viewed = 0
                lis = sort_by_key(0, lis)
                sort = 0
                update_wind(window, viewed, q_list, lis)
            else:
                viewed = 0
                lis = sort_by_key(0, lis, True)
                sort = -123123
                update_wind(window, viewed, q_list, lis)
        elif event == 'Описание':
            if sort != 2:
                viewed = 0
                lis = sort_by_key(2, lis)
                sort = 2
                update_wind(window, viewed, q_list, lis)
            else:
                viewed = 0
                lis = sort_by_key(2, lis, True)
                sort = -2
                update_wind(window, viewed, q_list, lis)
        elif event == '%':
            if sort != 3:
                viewed = 0
                lis = sort_by_key(3, lis)
                sort = 3
                update_wind(window, viewed, q_list, lis)
            else:
                viewed = 0
                lis = sort_by_key(3, lis, True)
                sort = -3
                update_wind(window, viewed, q_list, lis)
        elif event == 'Дата открытия':
            if sort != 4:
                viewed = 0
                lis = sort_by_key(4, lis)
                sort = 4
                update_wind(window, viewed, q_list, lis)
            else:
                viewed = 0
                lis = sort_by_key(4, lis, True)
                sort = -4
                update_wind(window, viewed, q_list, lis)


if __name__ == '__main__':
    start_wind()
