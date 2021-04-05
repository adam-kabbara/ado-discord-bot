import asyncio
import discord
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
import html
import time
import youtube_dl
import requests

'''
# Features to add #

- daily would you rather questions 
- add time for the trivia questions 
- add the functionality to follow sports social media (twitter - instagram - reddit...)
- apply the new trivia api for the spesific trivias (its already implimented for random trivia)
- add a daily trivia question with 20 points and 30 seconds to answer
- add the functionality for daily weather 
- add a shop for users to use up their points 
- fix async problem 
- fix the code (how it looks)
- youtube music
- spotify music
- ado challenge 
'''

token = private_data.discord_id
weather_token = private_data.weather_api_id

client = discord.Client()
trivia1_url = 'https://opentdb.com/api.php?amount=1&encode=base64' # url to get trivia1
token_url = "https://opentdb.com/api_token.php?command=request" # url to get trivia1 token
trivia_refresh_token_url = 'https://opentdb.com/api_token.php?command=reset' # trivia1 token refresh url
weather_url = "http://api.openweathermap.org/data/2.5/weather?" # url to get weather
weather_img_url = "http://openweathermap.org/img/wn/CODE@2x.png" # url to get weather img
trivia2_url = 'https://beta-trivia.bongo.best'
random_fact_urls = ['https://uselessfacts.jsph.pl/random.json?language=en', 'https://useless-facts.sameerkumar.website/api']
rcf_url = 'https://catfact.ninja/fact' # random cat fact url
joke_url = 'https://official-joke-api.appspot.com/random_joke'
dict_of_servers = {}


trivia_to_letter = {'a': 0, 'b': 1, 'c': 2, 'd': 3}


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
    'general knowledge': 9,
    'geography': 22,
    'geo': 22,
    'history': 23,
    'computer': 18,
    'tv': 14,
    'cartoon': 32,
    'anime': 31,
    'animal': 27,
    'vehicle': 28,
    'vehicles': 28,
    'vg': 15,
    'video game': 15,
    'video games': 15,
    'bg': 16,
    'board games': 16,
    'board game': 16,
    'film': 11,
    'sport': 21,
    'sports': 21,
    'celebrity': 26,
    'book': 10,
    'music': 12,
}    


def generate_loss_msg(solution):
    loss_msgs = [f'Sorry your answer is wrong. The correct answer is {solution}', 
            f'I actually thought humans were smarter than that. The answers is {solution}',
            f'Damn you have -100 IQ... congrats. I won\'t even bother telling you the correct answer',
            f'Dumbass thats the wrong answer, the correct one is {solution}',
            f'Are you fricking kidding me? That is completely wrong, its supposed to be {solution}',
            f'Are you sure you are not an ape. Your answer should\'ve been {solution}',
            f'Ohh come on the answer was {solution}',
            f'Pfftt, the answer was {solution}']
    msg = random.choice(loss_msgs)
    return msg


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



async def get_data(url, data={}):
    async with ClientSession() as session:
        async with session.get(url, params = data) as response:
            response = await response.json()
            return response


def process_trivia1(res):
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
        tup = {'question': res_decrypted['question'], 
                'correct_answer': res_decrypted['correct_answer'], 
                'available_answers': available_answers}
        return tup

def process_trivia2(res):
    res = res[0]
    print(res)
    raw_incorrect_answers = res['incorrect_answers']
    incorrect_answers = []

    correct = html.unescape(res['correct_answer'])
    catagory = res['category']
    difficulty = res['difficulty']

    if catagory is None:
        catagory = 'unknown'
    else:
        catagory = catagory.split(':')[-1].strip()
    if difficulty is None:
        difficulty = 'unknowen'

    for i in raw_incorrect_answers:
        i = html.unescape(i)
        incorrect_answers.append(i)
    available = incorrect_answers[:]
    available.append(correct)


    return {'correct_answer': correct,
            'question': html.unescape(res['question']),
            'difficulty': difficulty,
            'catagory': catagory,
            'available_answers': available}

async def send_rf(channel):
    await client.wait_until_ready()
    channel = client.get_channel(channel)
    while True:
        data = await get_data(get_random_question_url())
        print(data)
        try: 
            msg_to_send = data['data']
        except KeyError:
            msg_to_send = data['text']
        await channel.send(msg_to_send)
        await asyncio.sleep(86400)  # one day


def get_random_question_url():
    url = random.choice(random_fact_urls)
    return url


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


def get_weather_msg(data):

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

    msg_content = msg.content.lower().strip()
     
    if msg_content.startswith('ado ') and msg.author.id != client.user.id:

        
        try: 
            s = dict_of_servers[msg.guild.id]
            await s.async_init()
        except KeyError:
            dict_of_servers[msg.guild.id] = Server(msg.guild.id)
            s = dict_of_servers[msg.guild.id]
            await s.async_init()

        print(msg.content.lower())
        await s.process_msg(msg)




class Server:    
    def __init__(self, server):
        self.server_id = server
        self.trivia_asked = False
        self.trivia_random = None
        self.difficulty = None
        self.msg = None
        self.question_token = None
        self.solution = None
        self.available_answers = None
        self.daily_trivia_users = {}
        self.voice_channel_controller = None 
        self.voice_channel = None
        print(self.question_token)

        with open('challenge.json') as f:
            data = json.load(f)
            try:
                b = data[str(self.server_id)]['active']
            except KeyError:
                self.challenge = False
            else:
                if b == 'True':
                    self.challenge = True
                else:
                    self.challenge = False

    async def async_init(self):
        self.question_token = await get_data(token_url)
        self.question_token = self.question_token['token']

    async def process_msg(self, msg):
        self.msg = msg
        self.difficulty = None
        msg_to_send = None
        e = None
        tts = False
        msg_content = self.msg.content.lower()[4:].strip()

        if msg_content == 'help':
            e = help_msg
            
        elif msg_content == 'ping':
            before = time.monotonic()
            message = await self.msg.channel.send("Pong!")
            ping = (time.monotonic() - before) * 1000
            await message.edit(content=f"Pong!  `{int(ping)}ms`")
        
        elif msg_content == 'restart':
            if self.msg.author.id == 739167113880535191:
                try:
                    await self.msg.channel.send('Restarting Ado Bot')
                except discord.errors.HTTPException:
                    print('network error')

                # disconnect from all voice channels 
                for vc in client.voice_clients:
                    await vc.disconnect()

                print('restarting \n\n\n\n')
                os.system('bash startup.sh')
            else:
                msg_to_send = 'Only my owner can restart me'

        elif msg_content == 'help weather':
            msg_to_send = help_weather_msg

        elif msg_content.startswith('say'):
            msg_to_send = msg_content[4:]
            tts = True 


        elif msg_content == 'join' or msg_content == 'connect': #todo
            self.voice_channel = self.msg.author.voice

            if self.voice_channel is None:
                msg_to_send = 'You are not in a voice channel'
            else:
                self.voice_channel = self.msg.author.voice.channel
                try:
                    self.voice_channel_controller = await self.voice_channel.connect()
                except discord.errors.ClientException:
                    await self.voice_channel_controller.move_to(self.voice_channel)
                
                msg_to_send = f'ado joined {self.voice_channel}'
                print(f'connected to {self.voice_channel}')
        
        elif msg_content == 'leave' or msg_content == 'exit' or msg_content == 'disconnect': 
            if self.voice_channel_controller is not None:
                await self.voice_channel_controller.disconnect()
                self.voice_channel_controller = None
                msg_to_send = f'Ok I will leave {self.voice_channel}'
                self.voice_channel = None
            else: 
                msg_to_send = 'I\'m already out of the voice channel'


        elif msg_content.startswith('yt '):
            if self.voice_channel_controller is not None:
                url = msg_content[3:]
                await msg.channel.send('getting data')
                player = await YTDLSource.from_url(url, stream=True)
                self.voice_channel_controller.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

                msg_to_send = f'Now playing: {player.title}'
            else:
                msg_to_send = 'I am not in a voice channel. Type ado join in order for me to enter'


        elif msg_content.startswith('w '):
            error_msg = 'please use "ado help weather" to see commands for weather'
            error_msg2 = 'Please enter a valid city. If you are sure the city/provence is an actual place please report problem to a Adam_k'
            try:
                city, country = msg_content[2:].split(',')
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
        

        elif msg_content == 'start challenge':
            if not self.challenge:
                admin_role = discord.utils.find(lambda r: r.name == 'ado admin', self.msg.guild.roles)

                if admin_role in self.msg.author.roles:
                    self.challenge = True

                    with open('challenge.json', 'r') as f:
                        data = json.load(f)
                        data[str(self.server_id)] = {'active': 'True'}
                    with open('challenge.json', 'w') as f:
                        json.dump(data, f)

                    msg_to_send = 'Challenge started'
                else:
                    msg_to_send = 'You need to have an "ado admin" role in order to start a challenge'
            
            else: 
                msg_to_send = 'There is a challenge already'

        elif msg_content == 'stop challenge':
            admin_role = discord.utils.find(lambda r: r.name == 'ado admin', self.msg.guild.roles)
            if admin_role in self.msg.author.roles:
                self.challenge = False
                
                with open('challenge.json', 'r') as f:
                    data = json.load(f)
                    data[str(self.server_id)] = {'active': 'False'}
                with open('challenge.json', 'w') as f:
                    json.dump(data, f)

                msg_to_send = 'Challenge stopped'
            else:
                msg_to_send = 'You need to have an "ado admin" role in order to stop the challenge'


        elif msg_content.startswith('challenge points'):
            print(self.challenge)
            if self.challenge:
                if msg_content == 'challenge points':
                    points = self.get_points(self.msg.author.id, 'challenge.json')
                    msg_to_send = f'you have {points} challenge points'
                
                elif len(self.msg.mentions) == 1:
                    user = self.msg.mentions[0].id
                    points = self.get_points(user, 'challenge.json')
                    msg_to_send = f'{self.msg.mentions[0].mention} has {points} challenge points'
                
                elif msg_content.split()[2] == 'top':
                    with open ('challenge.json') as f:
                        points = json.load(f)

                    top = self.get_top_points(points)
                    e = discord.Embed(title='Top challenge points', color=discord.Color.red())
                    for k, v in top:
                        user = await client.fetch_user(k)
                        e.add_field(name=f'{user.name}', value=v, inline=False)

            else:
                msg_to_send = 'There is no challenge....'


        elif msg_content.startswith('points'):
            if msg_content == "points":
                points = self.get_points(self.msg.author.id, 'points.json')
                msg_to_send = f'you have {points} points'

            elif len(self.msg.mentions) == 1:
                user = self.msg.mentions[0].id
                points = self.get_points(user, 'points.json')
                msg_to_send = f'{self.msg.mentions[0].mention} has {points} points'
            
            elif msg_content.split()[1] == 'top':
                with open ('points.json') as f:
                    points = json.load(f)

                top = self.get_top_points(points)
                e = discord.Embed(title='Top points', color=discord.Color.red())
                for k, v in top:
                    user = await client.fetch_user(k)
                    e.add_field(name=f'{user.name}', value=v, inline=False)
                    

        elif msg_content == 'die':
            msg_to_send = f'ill kill you first {self.msg.author.mention}'
        elif msg_content == 'sad':
            msg_to_send = 'ado is sad u are using dank memer instead of him'

        elif 'gay' in msg_content and 'is' in msg_content:
            msg_to_send = random.choice(['I\'m not sure', 'yes he is', 'no he isn\'t', 'definitly', 'I mean like, duh', 'Naa', 'no he isn\'t, you are', 'no way'])
        
        elif msg_content.startswith('kill'):
            user_id = msg_content[5:] 

            if len(user_id) == 0:
                msg_to_send = 'You didn\'t mention who you wanted to kill. I really thought humans were smarter than this'
            else:
                msg_to_send = f'{self.msg.author.mention}, you just killed {user_id}'
        
        elif msg_content == 'random cat fact' or msg_content == 'rcf':
            data = await get_data(rcf_url)
            print(data)
            msg_to_send = data['fact']

        elif msg_content == 'daily':  #todo
            with open ('daily_trivia.json') as f:
                data = json.load(f)

        elif msg_content == 'random fact' or msg_content == 'rf':
            data = await get_data(get_random_question_url())
            print(data)
            try: 
                msg_to_send = data['data']
            except KeyError:
                try:
                    msg_to_send = data['fact']
                except KeyError:
                    msg_to_send = data['text']

        elif msg_content == 'joke':
            data = await get_data(joke_url)
            _type = data['type']
            if _type == 'general':
                _type = ''
            print(_type)
            e = discord.Embed(title=f'Bad {(_type).capitalize()} Joke', color=discord.Color.red())
            e.add_field(name='Joke', value=f"{data['setup']} {data['punchline']}", inline=False)
            
        elif msg_content == 'bj':
            msg_to_send = 'please use [ado joke]'


        elif msg_content == 'random trivia' or msg_content == 'rt':
            if not self.trivia_asked:
                rand = random.randint(1, 2)

                if rand == 1:
                    self.difficulty = random.choice(['easy','medium','hard'])
                    subject = random.choice(list(subject_codes.keys()))
                    
                    res = await get_data(trivia1_url, data={'difficulty':self.difficulty,
                                                    'category':subject_codes[subject],
                                                    'token': self.question_token})
                    if res['response_code'] !=0:
                        res = self.handel_token_error(res)
                        self.question_token = res['token']

                    res = await get_data(trivia1_url, data={'difficulty':self.difficulty,
                                                    'category':subject_codes[subject],
                                                    'token': self.question_token})
                    data = process_trivia1(res)
                    question = data['question']
                    self.available_answers = data['available_answers']
                    self.solution = data['correct_answer'].lower().strip()

                else:
                    res = await get_data(trivia2_url)
                    res = process_trivia2(res) 
                    self.solution = res['correct_answer'].lower().strip()
                    self.difficulty = res['difficulty']
                    self.available_answers = res['available_answers']
                    subject = res['catagory']
                    question = res['question']

                msg_to_send = f'SUBJECT: {subject}\nDIFFICULTY: {self.difficulty}\n\n{question} \navailable answers: {self.available_answers}'
                self.trivia_asked = True
                self.trivia_random = True

            else:
                msg_to_send = 'Solve the previous trivia before asking for a new one'

        elif msg_content.split()[0] in subject_codes.keys():
            if not self.trivia_asked:
                subject = msg_content.split()[0]

                if 'easy' in msg_content:
                    self.difficulty = 'easy'
                elif 'medium' in msg_content:
                    self.difficulty = 'medium'
                elif 'hard' in msg_content:
                    self.difficulty = 'hard'

                if self.difficulty:
                    res = await get_data(trivia1_url, data={'difficulty':self.difficulty,
                                                    'category':subject_codes[subject],
                                                    'token':  self.question_token})
                    print(res['response_code'])
                    if res['response_code'] !=0:
                        res = self.handel_token_error(res)
                        self.question_token = res['token']
                        
                    res = await get_data(trivia1_url, data={'difficulty':self.difficulty,
                                                    'category':subject_codes[subject],
                                                    'token': self.question_token})
                    data = process_trivia1(res)
                    question = data['question']
                    self.available_answers = data['available_answers']
                    msg_to_send = f'{question} \navailable answers: {self.available_answers}'
                    
                    self.trivia_asked = True
                    self.trivia_random = False
                    self.solution = data['correct_answer'].lower().strip()

                else:
                    msg_to_send = 'Try again and please enter a difficulty level (easy, medium, hard)'
            else:
                msg_to_send = 'Solve the previous trivia before asking for a new one'


        else:
            ans = msg_content.lower().strip()

            if self.trivia_asked:
                if ans in trivia_to_letter.keys():  # check if user answers by a,b,c or d 
                    index = trivia_to_letter[ans]
                    try: 
                        user_answer = self.available_answers[index].lower().strip()
                    except IndexError:
                        msg_to_send = generate_loss_msg(self.solution)
                        self.trivia_asked = False
                    else: 
                        if self.solution == user_answer:
                            msg_to_send = random.choice(win_msgs)
                            self.trivia_asked = False
                            self.add_points('points.json')
                            if self.challenge:
                                self.add_points('challenge.json')
                            self.trivia_random = None
                        else:
                            msg_to_send = generate_loss_msg(self.solution)
                            self.trivia_asked = False

                elif ans == self.solution:
                    msg_to_send = random.choice(win_msgs)
                    self.trivia_asked = False
                    self.add_points('points.json')
                    if self.challenge:
                        self.add_points('challenge.json')          
                    self.trivia_random = None
                else:
                    msg_to_send = generate_loss_msg(self.solution)
                    self.trivia_asked = False

            else:
                msg_to_send = 'please ask for a new trivia question before you answer'

        if msg_to_send is not None or e is not None:
            try:
                await self.msg.channel.send(msg_to_send, embed=e, tts=tts)
            except discord.errors.HTTPException:
                print('error sending msg')

    def add_points(self, file_name):
        if self.trivia_random: # 25 AND THE DAILY IS 30
            points_to_add = 10
        else:
            if self.difficulty == 'easy': # 20
                points_to_add = random.randint(1, 3)
            elif self.difficulty == 'medium':
                points_to_add = random.randint(3, 5)
            else:
                points_to_add = random.randint(6, 8)
        print(points_to_add)
        self.update_points({self.msg.author.id: points_to_add}, file_name)

    def get_top_points(self, points):
        points.setdefault(str(self.server_id), {})
        points = points[str(self.server_id)]
        top = []
        int_dict = dict()

        for k, v in points.items():
            try:
                int_dict[k] = int(v)
            except ValueError as e:
                print(f'{e} error. dont worry about it')
        
        sorted_keys = sorted(int_dict, key=int_dict.get, reverse=True)
        for i, k in enumerate(sorted_keys):
            if i<=4:
                top.append((k, int_dict[k]))
            else:
                break 
        return top

    def update_points(self, dictionary, file_name):
        dd = defaultdict(float)
        main_dict = dict()
        dictionary = {str(k): v for k, v in  dictionary.items()}
        with open (file_name) as f:
            points = json.load(f)

        points.setdefault(str(self.server_id), {})

        other = copy.deepcopy(points)
        del other[str(self.server_id)]
        main_dict.update(other)

        points = points[str(self.server_id)]
        dd.update(points)
        for key, value in dictionary.items():
            dd[key] += value
        
        main_dict[str(self.server_id)] = dd
        with open(file_name, 'w') as f:
            json.dump(main_dict, f)

    def get_points(self, user, file_name):
        dd = defaultdict(float)
        user = str(user)
        int_dict = dict()
        with open (file_name) as f:
            points = json.load(f)
        points = points[str(self.server_id)]
        dd.update(points)
        for k, v in dd.items():
            try:
                int_dict[k] = int(v)
            except ValueError as e:
                print(f'{e} probably it is an error from the activate key in the challenge json dw about it')
        try:
            return int_dict[user]
        except KeyError:
            return 0

    async def handel_token_error(self, res):
        while res['response_code'] != 0:
            print(f'error code {res["response_code"]}')
            if res['response_code'] == 4:
                try:
                    res = await get_data(trivia_refresh_token_url, data={'token': self.question_token})
                except Exception as exp:
                    return f'Error retrieving data ({exp})'

            elif res['response_code'] == 3:
                print('debug')
                res = await get_data(token_url)
                self.question_token = res['token']
            
        return res

client.run(token)
