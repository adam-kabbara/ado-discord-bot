import asyncio
import discord
import requests
import base64
import random
import os
from help_msg import help_msg, help_weather_msg
import json
import tqdm
import private_data
from collections import defaultdict
import copy
from aiohttp import ClientSession
from io import BytesIO

token = private_data.ids['discord']
weather_token = private_data.ids['weather']

client = discord.Client()
base_url = 'https://opentdb.com/api.php?amount=1&encode=base64'
token_url = "https://opentdb.com/api_token.php?command=request"
weather_url = "http://api.openweathermap.org/data/2.5/weather?"
weather_img_url = "http://openweathermap.org/img/wn/CODE@2x.png"
res = requests.get(token_url)
question_token = res.json()['token']
trivia_asked = False
trivia_random = None
difficulty = None
data = ()

trivia_to_letter = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
loss_msgs = ['Sorry you\'re answer is wrong. Don\'t worry you can try again.', 
            'I actually thought humans were smarter than that',
            'damn you have -100 IQ... congrats',
            'dumbass thats the wrong answer',
            'are you fricking kidding me? That is completely wrong',
            'are you sure you are not an ape. That was the wrong answer']

win_msgs = ['Hurray you got the answer correct', 
            'Finally a smart one. That was the correct answer',
            'Damn ur good at this',
            'Damn that was the correct answer',
            'You\'re going to outsmart me. That was the correct answer',
            'Are you sure you\'re not cheating? That was an epic answer']

subject_codes = {
    'math': 19,
    'science': 17,
    'gk': 9,
    'geography': 22,
    'history': 23,
    'computer': 18,
    'tv': 14,
    'cartoon': 32,
    'anime': 31,
    'animal': 27,
    'vehicle': 28,
    'vg': 15,
    'bg': 16,
    'film': 11,
    'sport': 21,
    'celebrity': 26,
    'book': 10,
    'music': 12,
}


def get_data(url, data={}):
    try:
        res = requests.get(url, params=data)
    except Exception as exp:
        print(f'Error retrieving data ({exp})')
    else:
        return res.json()

async def get_data(url, data={}):
    async with ClientSession() as session:
        async with session.get(url, params = data) as response:
            response = await response.json()
            return response


def process_data(res):
    res = res['results'][0]

    if type(res) is not dict:
        return res, res

    else:
        res_decrypted = {}
        for k, v in res.items():
            try:
                res_decrypted[k] = base64.b64decode(v).decode('utf-8')
            except TypeError:
                try:
                    res_decrypted[k] = [base64.b64decode(i).decode('utf-8') for i in v]
                except TypeError:
                    pass

        print(res_decrypted)
        available_answers = res_decrypted['incorrect_answers'][:]
        available_answers.append(res_decrypted['correct_answer'])
        random.shuffle(available_answers)
        tup = (res_decrypted['question'], res_decrypted['correct_answer'], available_answers)
        return tup


async def send_rf(channel):
    await client.wait_until_ready()
    channel = client.get_channel(channel)
    while True:
        data = get_data(get_random_question_url())
        print(data)
        try: 
            msg_to_send = data['data']
        except KeyError:
            msg_to_send = data['text']
        await channel.send(msg_to_send)
        await asyncio.sleep(86400)  # one day


def get_random_question_url():
    url = random.choice(['https://uselessfacts.jsph.pl/random.json?language=en', 'https://useless-facts.sameerkumar.website/api'])
    return url

def get_points(user, channel):
    dd = defaultdict(float)
    user = str(user)
    int_dict = dict()
    with open ('points.json') as f:
        points = json.load(f)
    points = points[str(channel)]
    dd.update(points)
    for k, v in dd.items():
        int_dict[k] = int(v)
    try:
        return int_dict[user]
    except KeyError:
        return 0

def update_points(dictionary, channel):
    dd = defaultdict(float)
    main_dict = dict()
    dictionary = {str(k): v for k, v in  dictionary.items()}
    with open ('points.json') as f:
        points = json.load(f)

    points.setdefault(str(channel), {})

    other = copy.deepcopy(points)
    del other[str(channel)]
    main_dict.update(other)

    points = points[str(channel)]
    dd.update(points)
    for key, value in dictionary.items():
        dd[key] += value
    
    main_dict[str(channel)] = dd
    with open('points.json', 'w') as f:
        json.dump(main_dict, f)

def get_top_points(channel):
    with open ('points.json') as f:
        points = json.load(f)
    
    points.setdefault(str(channel), {})
    points = points[str(channel)]
    top = []
    int_dict = dict()

    for k, v in points.items():
        int_dict[k] = int(v)
    
    sorted_keys = sorted(int_dict, key=int_dict.get, reverse=True)
    for i, k in enumerate(sorted_keys):
        if i<=4:
            top.append((k, int_dict[k]))
        else:
            break 
    return top

def add_points(difficulty, trivia_random, msg):
    if trivia_random:
        points_to_add = 10
    else:
        if difficulty == 'easy':
            points_to_add = random.randint(1, 3)
        elif difficulty == 'medium':
            points_to_add = random.randint(3, 5)
        else:
            points_to_add = random.randint(6, 8)
    print(points_to_add)
    update_points({msg.author.id: points_to_add}, msg.guild.id)


def handel_token_error(res):
    while res['response_code'] != 0:
        print(f'error code {res["response_code"]}')
        if res['response_code'] == 4:
            try:
                res = requests.get(f'https://opentdb.com/api_token.php?command=reset&token={question_token}').json()
            except Exception as exp:
                return f'Error retrieving data ({exp})'

        elif res['response_code'] == 3:
            print('debug')
            res = (requests.get(token_url)).json()
            question_token = res['token']
            
    return res


def get_city_code(city, country):
    if country == 'usa' or country == 'us' or country == 'United states of america':
        country = 'united states'
    found_cities = []
    with open('city.list.json/city.list.json') as f:
        city_data = json.load(f)

    country_code = get_country_code(country)
    if country_code is not None:
        for dictionary in tqdm.tqdm(city_data):
            if dictionary['name'].lower() == city and dictionary['country'] == country_code: 
                found_cities.append(dictionary)

        return found_cities
    else:
        return None


def get_country_code(country):
    with open ('city.list.json/country_codes.json') as f:
        country_codes = json.load(f)
    try: 
        country_code = country_codes[country.title()]
    except KeyError:
        return None
    else:
        return country_code


def get_weather_msg(code):

    with open ('city.list.json/country_codes.json') as f:
        country_codes = json.load(f)
    inv_country_codes = {v: k for k, v in country_codes.items()}

    code = data['weather'][0]['icon']
    city = data['name']
    country = inv_country_codes[data['sys']['country']]
    description = data['weather'][0]['description']
    feels_like = data['main']['feels_like']
    temp = data['main']['temp']
    temp_min = data['main']['temp_min']
    temp_max = data['main']['temp_max']
    humidity = data['main']['humidity']
    wind = data['wind']['speed']
    lat = data['coord']['lat']
    lon = data['coord']['lon']


    url = weather_img_url.replace('CODE',code)
    e = discord.Embed(title=f'Weather in {city}, {country}', color=discord.Color.red())
    e.set_image(url=url)
    e.add_field(name='Weather Decription', value=description, inline=True)
    e.add_field(name='Coords', value=f'lat: {lat}, lon: {lon}')
    e.add_field(name="Temperature", value=f"Temp: {temp} ℃\nMax Temp: {temp_max} ℃\nMin Temp: {temp_min} ℃\nFeels Like: {feels_like} ℃", inline=False)
    e.add_field(name='Wind Speed', value=f'Wind Speed: {wind} km/hour', inline=True)
    e.add_field(name='Humidity', value=f'Humidity: {humidity} %', inline=True)
    return e
        
print('running')

@client.event
async def on_message(msg):
    global trivia_asked, question_token, trivia_random, difficulty, data
    if msg.content.isdigit():
        msg_content = msg.content
    else:
        msg_content = msg.content.lower()[4:].strip()
    msg_to_send = None
    e = None
     

    if msg.content.lower().startswith('ado '):
        print(msg.content.lower())

        if msg_content == 'help':
            e = help_msg

        if msg_content == 'test':
            import time
            await asyncio.sleep(5)
            msg_to_send = 'test'
            
        elif msg_content == 'ping':
            msg_to_send = 'pong'
        
        elif msg_content == 'help weather':
            msg_to_send = help_weather_msg # todo

        elif msg_content.startswith('w'):
            error_msg = 'please use "ado help weather" to see commands for weather'
            error_msg2 = 'Please enter a valid city. If you are sure the city/provence is an actual place please report problem to <@!739167113880535191>'
            try:
                city, country = msg_content[1:].split(',')
                city, country = city.strip(), country.strip()
            except ValueError:
                msg_to_send = error_msg
            
            else:
                if len(city) > 3: #means its a city name
                    city_code_lst = get_city_code(city, country)
                    if city_code_lst:
                        city_code = city_code_lst[0]['id']
                        data = await get_data(weather_url, data={'appid': weather_token,
                                                    'id': city_code,
                                                    'units': 'metric'})
                        e = get_weather_msg(data)
                    else:
                        msg_to_send = error_msg2

                elif len(city) == 3: # means its a zip code prefix
                    country_code = get_country_code(country).lower()
                    data = await get_data(weather_url, data={'appid': weather_token,
                                                        'units': 'metric',
                                                        'zip': f'{city},{country_code}'})
                    e = get_weather_msg(data)
                        
                else:
                    msg_to_send = f'Sorry city/provence was not found. {error_msg2}'
                

        elif msg_content == 'restart':
            try:
                await msg.channel.send('Restarting Ado Bot')
            except discord.errors.HTTPException:
                print('network error')
                
            print('restarting \n\n\n\n')
            os.system('bash startup.sh')

        elif msg_content.startswith('points'):
            if msg_content == "points":
                points = get_points(msg.author.id, msg.guild.id)
                msg_to_send = f'you have {points} points'

            elif len(msg.mentions) == 1:
                user = msg.mentions[0].id
                points = get_points(user, msg.guild.id)
                msg_to_send = f'{msg.mentions[0].mention} has {points} points'
            
            elif msg_content.split()[1] == 'top':
                top = get_top_points(msg.guild.id)
                e = discord.Embed(title='Top points', color=discord.Color.red())
                for k, v in top:
                    user = await client.fetch_user(k)
                    e.add_field(name=f'{user.name}', value=v, inline=False)
                    

        elif msg_content == 'die':
            msg_to_send = f'ill kill you first {msg.author.mention}'
        elif msg_content == 'sad':
            msg_to_send = 'ado is sad u are using dank memer instead of him'

        elif 'gay' in msg_content and 'is' in msg_content:
            msg_to_send = random.choice(['I\'m not sure', 'yes he is', 'no he isn\'t', 'definitly', 'I mean like, duh', 'Naa', 'no he isn\'t, you are', 'no way'])
        
        elif msg_content.startswith('kill'):
            user_id = msg_content[5:] 

            if len(user_id) == 0:
                msg_to_send = 'You didn\'t mention who you wanted to kill. I really thought humans were smarter than this'
            else:
                msg_to_send = f'{msg.author.mention}, you just killed {user_id}'

        elif msg_content == 'reveal solution' or msg_content == 'reveal answer' or msg_content == 'show answer' or msg_content == 'show solution' or msg_content == 'reveal' or msg_content == 'show':
            if trivia_asked:
                msg_to_send = f'The solution is {data[1]}'
                trivia_asked = False
            else:
                msg_to_send = 'please ask for a new trivia question before getting its answer'

        elif msg_content == 'random cat fact' or msg_content == 'rcf':
            data = await get_data('https://catfact.ninja/fact')
            print(data)
            msg_to_send = data['fact']

        elif msg_content == 'random fact' or msg_content == 'rf':
            data = await get_data(get_random_question_url())
            print(data)
            try: 
                msg_to_send = data['data']
            except KeyError:
                msg_to_send = data['text']

        elif msg_content == 'joke':
            data = await get_data('https://official-joke-api.appspot.com/random_joke')
            _type = data['type']
            if _type == 'general':
                _type = ''
            print(_type)
            e = discord.Embed(title=f'Bad {(_type).capitalize()} Joke', color=discord.Color.red())
            e.add_field(name='Joke', value=f"{data['setup']} {data['punchline']}", inline=False)
            
        elif msg_content == 'bj':
            msg_to_send = 'please use [ado joke]'


        elif msg_content == 'random trivia' or msg_content == 'rt':
            difficulty = random.choice(['easy','medium','hard'])
            subject = random.choice(list(subject_codes.keys()))
            
            res = await get_data(base_url, data={'difficulty':difficulty,
                                            'category':subject_codes[subject],
                                            'token': question_token})
            if res['response_code'] !=0:
                res = handel_token_error(res)
                question_token = res['token']

            res = await get_data(base_url, data={'difficulty':difficulty,
                                            'category':subject_codes[subject],
                                            'token': question_token})
            data = process_data(res)
            msg_to_send = f'SUBJECT: {subject}\nDIFFICULTY: {difficulty}\n\n{data[0]} \navailable answers: {data[2]}'
            trivia_asked = True
            trivia_random = True

        elif msg_content.split()[0] in subject_codes.keys():
            subject = msg_content.split()[0]

            if 'easy' in msg_content:
                difficulty = 'easy'
            elif 'medium' in msg_content:
                difficulty = 'medium'
            elif 'hard' in msg_content:
                difficulty = 'hard'

            if difficulty:
                res = await get_data(base_url, data={'difficulty':difficulty,
                                                'category':subject_codes[subject],
                                                'token': question_token})
                print(res['response_code'])
                if res['response_code'] !=0:
                    res = handel_token_error(res)
                    question_token = res['token']
                    
                res = await get_data(base_url, data={'difficulty':difficulty,
                                                'category':subject_codes[subject],
                                                'token': question_token})
                data = process_data(res)
                msg_to_send = f'{data[0]} \navailable answers: {data[2]}'
                trivia_asked = True
                trivia_random = False

            else:
                msg_to_send = 'Try again and please enter a difficulty level (easy, medium, hard)'

        else:
            ans = msg_content.lower().strip()
            try:
                solution = data[1].lower().strip()
            except IndexError as ero:
                print(f'error {ero}')
            else:
                if trivia_asked:
                    if ans in trivia_to_letter.keys():
                        index = trivia_to_letter[ans]
                        if solution == data[2][index].lower().strip():
                            msg_to_send = random.choice(win_msgs)
                            trivia_asked = False
                            add_points(difficulty, trivia_random, msg)
                            trivia_random = None
                        else:
                            msg_to_send = random.choice(loss_msgs)

                    elif ans == solution:
                        msg_to_send = random.choice(win_msgs)
                        trivia_asked = False
                        add_points(difficulty, trivia_random, msg)          
                        trivia_random = None
                    else:
                        msg_to_send = random.choice(loss_msgs)

                else:
                    msg_to_send = 'please ask for a new trivia question before you answer'

        if msg_to_send is not None or e is not None:
            try:
                await msg.channel.send(msg_to_send, embed=e)
            except discord.errors.HTTPException:
                print('error sending msg')


client.run(token)
