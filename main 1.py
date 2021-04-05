import discord
from discord.ext import commands
from private_data import discord_id
from YouTubeClass import YouTube

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
- ado challange 
'''

bot = commands.Bot(command_prefix=commands.when_mentioned_or("tado "),
                   description='Ado Bot', case_insensitive=True)

@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')

bot.add_cog(YouTube(bot))
bot.run(discord_id)