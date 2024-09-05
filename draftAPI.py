import requests
import json
import os
    # pwd = 'Xip01qzc!'
    # email_address = 'noah@videcrantz.com'

    # print('authenticating...')
    # url = 'https://users.premierleague.com/accounts/login/'
    # payload = {
    #  'password': pwd,
    #  'login': email_address,
    #  'redirect_uri': 'https://fantasy.premierleague.com/a/login',
    #  'app': 'plfpl-web'
    # }
    # response = session.post(url, data=payload)
    # if (not assert_success(response)):
    #     return

def assert_success(response):
    if(response.status_code != 200):
        print(f'Something went wrong. Got response => {response.status_code}: {response.reason}')
        return False # throw exception instead?
    print(f'Success. Got response => {response.status_code}: {response.reason}')
    return True
    
def get_data(path, api): 
    session = requests.session()
    print(f'getting {path[7:]}...')
    r = session.get(api)
    if (not assert_success(r)):
        return

    jsonResponse = r.json()
    print(f'writing {path[7:]}...')
    with open(path, 'w') as outfile:
        json.dump(jsonResponse, outfile, indent=4)


def get_all_data():
    gw, gw_done = determine_current_gameweek()
    if not gw_done:
        print('Warning! Current gameweek is not finished!')
        ignore_warning = input('Continue anyway? y/n: ')
        if ignore_warning == 'n':
            print(f'Got {ignore_warning} - stopping')
            os.remove('./data/game.json')
            return False
        print(f'Got {ignore_warning} - continuing')


    base = './data/w' + str(gw)
    if os.path.exists(base):
        print(f'Data for current gameweek (w{gw}) already exists...')
        os.remove('./data/game.json')
        return False
    
    os.makedirs(base)
    os.rename('./data/game.json', base + '/game.json')

    extract_meta_data(gw)
    extract_manager_events(gw)
    extract_manager_publics(gw)
    return True

def determine_current_gameweek():
    path = './data/game.json'
    api = 'https://draft.premierleague.com/api/game'
    get_data(path, api)
    with open('./data/game.json') as file:
        content = json.load(file)
        return content['current_event'], content['current_event_finished']

def extract_meta_data(gw):
    base = './data/w' + str(gw)
    
    # paths = [base + '/details.json', 
    #          base + '/transactions.json', 
    #          base + '/elements.json', 
    #          base + '/elements_status.json',
    #          base + '/game.json',
    #          base + '/live.json',
    #          base + '/event_status.json']

    # apis = ['https://fantasy.premierleague.com/api/league/71492/details',
    #         'https://fantasy.premierleague.com/api/draft/league/71492/transactions',
    #         'https://fantasy.premierleague.com/api/bootstrap-static',
    #         'https://fantasy.premierleague.com/api/league/71492/element-status',
    #         'https://fantasy.premierleague.com/api/game',
    #         'https://fantasy.premierleague.com/api/event/' + str(gw) + '/live',
    #         'https://fantasy.premierleague.com/api/event-status/']
    
    
    paths = [base + '/standings.json', 
             base + '/static.json', 
             base + '/event_status.json',
             base + '/live.json']
        
    apis = ['https://fantasy.premierleague.com/api/leagues-classic/782337/standings/',
            'https://fantasy.premierleague.com/api/bootstrap-static',
            'https://fantasy.premierleague.com/api/event-status/',
            'https://fantasy.premierleague.com/api/event/1/live/']
    
    pairs = zip(paths, apis)

    for path, api in pairs:
        get_data(path, api)


def extract_managers():
    managers = [] 
    with open('./data/standings.json', 'r') as file:
        details = json.load(file)
        for manager in details['standings']['results']:
            new_manager = dict()
            new_manager['name'] = manager['player_name']
            new_manager['team_name'] = manager['entry_name']
            new_manager['entry_id'] = manager['entry']
            new_manager['id'] = manager['id']
            managers.append(new_manager)
    return managers


def extract_manager_events(gw):
    managers = extract_managers()
    base = './data/w' + str(gw)

    for manager in managers:
        path = base + '/entry_' + manager['name'] + '.json'
        api = 'https://fantasy.premierleague.com/api/entry/'+ str(manager['entry_id']) +'/event/' + str(gw) + '/picks/'
        get_data(path, api)


def extract_manager_publics(gw):
    managers = extract_managers()
    base = './data/w' + str(gw)

    for manager in managers:
        path = base + '/entry_' + manager['name'] + '_meta.json'
        api = 'https://fantasy.premierleague.com/api/entry/'+ str(manager['entry_id']) +'/'
        get_data(path, api)

def load_json(path):
    with open(path) as file:
        content = json.load(file)
        return content


def mid_to_mname(mid):
    with open('./data/details.json', 'r') as f:
        details = json.load(f)
        for manager in details['league_entries']:
            if manager['entry_id'] == mid or manager['id'] == mid:
                return manager['player_first_name']

def pid_to_pname(pid, gw):
    with open('./data/w'+ str(gw) +'/elements.json', 'r') as f:
        data = json.load(f)
        for player in data['elements']:
            if player['id'] == pid:
                return player['web_name']

def restore_data(gws):
    # gws = [1, 2, 3, 4, 5, 6, 7]
    managers = extract_managers()

    for gw in gws:
        print(f'\nrestoring gw: {gw}...')
        base = './data/w' + str(gw)
        for manager in managers:
            # os.remove(base + '/entry_' + manager['name'] + '_event.json')
            path = base + '/entry_' + manager['name'] + '.json'
            api = 'https://draft.premierleague.com/api/entry/'+ str(manager['entry_id']) + '/event/' + str(gw)
            get_data(path, api)

        path_live = base + '/live.json'
        api_live = 'https://draft.premierleague.com/api/event/' + str(gw) + '/live'
        get_data(path_live, api_live)



def restore_event_points(gws):
    for gw in gws:
        print(f'\nrestoring gw: {gw}...')
        prev = './data/w' + str(gw-1) + '/elements.json'
        curr = './data/w' + str(gw) + '/elements.json'
        with open(prev, "r") as p:
            prev_elements = [element for element in json.load(p)['elements']]
        
        with open(curr, "r") as c:
            data = json.load(c)
        
        for curr_element in data['elements']:
            for prev_element in prev_elements:
                if curr_element['id'] == prev_element['id']:
                    curr_element['event_points'] = curr_element['total_points'] - prev_element['total_points']
        
        with open(curr, "w") as c:
            json.dump(data, c)





def load_player_data(pid, gw=1):
    with open('./data/w'+str(gw)+'/elements.json') as details:
        content = json.load(details)
    for data in content["elements"][pid-5:pid+5]:
        if data["id"] == pid:
            return data


# get_all_data()
if __name__ == "__main__":
    print(get_all_data())
    # extract_meta_data(1)
    # load_player_data(200)

    # print("Script is running!")
    # print("Everything is good!")