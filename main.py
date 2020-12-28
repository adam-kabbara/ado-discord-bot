import asyncio
import discord
import requests
import base64
import random

with open('private data.txt') as f:
    token = f.read()

client = discord.Client()
base_url = 'https://opentdb.com/api.php?amount=1&category=SUBJECTCODE&difficulty=spotholder&encode=base64&token=YOURTOKENHERE'
data = ()
token_url = "https://opentdb.com/api_token.php?command=request"

res = requests.get(token_url)
question_token = res.json()['token']

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


async def keep_token_active():
    while True:
        await asyncio.sleep(20880)
        requests.get(base_url)
        print('sent msg to keep token active')


def get_data(url, difficulty='', subject_code=''):
    url = url.replace('YOURTOKENHERE', question_token)
    url = url.replace('spotholder', difficulty)
    url = url.replace('SUBJECTCODE', str(subject_code))
    try:
        res = requests.get(url)
    except Exception as exp:
        return f'Error retrieving data ({exp})'
    else:
        return res.json()


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


async def send_rf():
    await client.wait_until_ready()
    channel = client.get_channel(787359133590355968)
    while True:
        data = get_data('https://useless-facts.sameerkumar.website/api')
        print(data)
        msg_to_send = data['data']
        await channel.send(msg_to_send)
        await asyncio.sleep(86400)  # one day


print('running')
@client.event
async def on_message(msg):
    global data
    msg_content = msg.content.lower()
    param = None
    if msg_content.startswith('ado '):
        print(msg_content)
        msg_content = msg_content[4:].strip()

        if msg_content == 'help':
            msg_to_send = """Hello to daily math questions
Below is a list of commands for the bot ado
Note before typing the command please proceed it with \"ado\"
- animal (difficulty) --> gives you a animal question
- anime (difficulty) --> gives you a anime question
- bg (difficulty) --> gives you a board game question
- book (difficulty) --> gives you a book question
- cartoon (difficulty) --> gives you a cartoon question
- celebrity (difficulty) --> gives you a celebrity question
- computer (difficulty) --> gives you a computer question
- film (difficulty) --> gives you a film question
- geography (difficulty) --> gives you a geography question
- gk (difficulty) --> gives you a general knowledge question
- history (difficulty) --> gives you a history question
- math (difficulty) --> gives you a math question
- music (difficulty) --> gives you a music question
- tv (difficulty) --> gives you a television question
- vehicle (difficulty) --> gives you a vehicle question
- vg (difficulty) --> gives you a video game question
- sport (difficulty) --> gives you a sport question
- science (difficulty) --> gives you a science question
- random fact ; rf --> gives you a random fact
- random cat fact ; rcf --> gives you a random fact about cats
- (type answer) --> check if you're answer is correct
- reveal solution --> reveals the answer
- help --> get help... duh
Note: The difficulties are (easy, medium, hard)"""

        elif msg_content == 'reveal solution' or msg_content == 'reveal answer' or msg_content == 'show answer' or msg_content == 'show solution' or msg_content == 'reveal' or msg_content == 'show':
            msg_to_send = f'The solution is {data[1]}'

        elif msg_content == 'random cat fact' or msg_content == 'rcf':
            data = get_data('https://catfact.ninja/fact')
            print(data)
            msg_to_send = data['fact']

        elif msg_content == 'random fact' or msg_content == 'rf':
            data = get_data('https://useless-facts.sameerkumar.website/api')
            print(data)
            msg_to_send = data['data']

        elif msg_content.split()[0] in subject_codes.keys():
            subject = msg_content.split()[0]

            if 'easy' in msg_content:
                param = 'easy'
            elif 'medium' in msg_content:
                param = 'medium'
            elif 'hard' in msg_content:
                param = 'hard'

            if param:
                res = get_data(base_url, param, subject_codes[subject])

                while res['response_code'] != 0:
                    print(res['response_code'])
                    if res['response_code'] == 4:
                        await msg.channel.send('resetting token')
                        try:
                            requests.get(f'https://opentdb.com/api_token.php?command=reset&token={question_token}')
                        except Exception as exp:
                            return f'Error retrieving data ({exp})'
                    res = get_data(base_url, param, subject_codes[subject])

                data = process_data(res)
                msg_to_send = f'{data[0]} \navailable answers: {data[2]}'

            else:
                msg_to_send = 'Try again and please enter a difficulty level (easy, medium, hard)'

        else:
            ans = msg_content.lower().strip()
            solution = data[1].lower().strip()

            if ans == solution:
                msg_to_send = 'Hurray you got the answer correct'
            else:
                msg_to_send = 'Sorry you\'re answer is wrong. Don\'t worry you can try again.' \
                              'If you want to know what was the correct answer type "ado reveal solution"'

        try:
            await msg.channel.send(msg_to_send)
        except discord.errors.HTTPException:
            pass


client.loop.create_task(send_rf())
client.loop.create_task(keep_token_active())
client.run(token)
