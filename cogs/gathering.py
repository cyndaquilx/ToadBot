import discord
from discord.ext import commands
from discord import app_commands
import json
from dateutil.parser import parse
from datetime import tzinfo
from datetime import datetime, timedelta
import time

with open('./timezones.json', 'r') as cjson:
    timezones = json.load(cjson)

class Lineup:
    def __init__(self, name=None, timestamp=None):
        self.name = name
        self.timestamp = timestamp
        self.players = []

    def __str__(self):
        if self.name is not None and self.timestamp is not None:
            return f"`{self.name}` / {discord.utils.format_dt(self.timestamp)}"
        elif self.name is not None:
            return f"`{self.name}`"
        elif self.timestamp is not None:
            return f"{discord.utils.format_dt(self.timestamp)}"
        return ""

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self.players):
            raise StopIteration
        else:
            currplayer = self.players[self.index]
            self.index += 1
            return currplayer

    def __len__(self):
        return len(self.players)

    def add_player(self, player):
        for p in self.players:
            if p == player:
                return
        self.players.append(player)

    def drop_player(self, player):
        for p in self.players:
            if p == player:
                self.players.remove(player)
                return
        

class Channel_List:
    def __init__(self):
        self.lineups = []

    def get_name(self, name:str):
        for l in self.lineups:
            if l.name == name:
                return l

    def get_time(self, timestamp):
        for l in self.lineups:
            if l.timestamp == timestamp:
                return l

    def end_name(self, name:str):
        for l in self.lineups:
            if l.name == name:
                self.lineups.remove(l)
                return True
        return False

    def end_time(self, timestamp):
        for l in self.lineups:
            if l.timestamp == timestamp:
                self.lineups.remove(l)
                return True
        return False

    def end_all(self):
        self.lineups = []

    def add_named(self, name:str):
        for i, l in enumerate(self.lineups):
            if l.name == name:
                self.lineups[i] = Lineup(name=name)
                return
        self.lineups.append(Lineup(name=name))

    def add_time(self, timestamp):
        for i, l in enumerate(self.lineups):
            if l.timestamp == timestamp:
                self.lineups[i] = Lineup(timestamp=timestamp)
                return
        self.lineups.append(Lineup(timestamp=timestamp))

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self.lineups):
            raise StopIteration
        else:
            currlu = self.lineups[self.index]
            self.index += 1
            return currlu

    def __len__(self):
        return len(self.lineups)

class gathering(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.lineups = {}

    def getTime(self, schedule_time:str, timezone:str):
        if schedule_time.isnumeric():
            schedule_time += ":00"
        utc_offset = time.altzone if time.localtime().tm_isdst > 0 else time.timezone
        time_adjustment = timedelta(seconds=utc_offset)
        timezone_adjustment = timedelta(hours=0)
        if timezone.upper() in timezones.keys():
            timezone_adjustment = timedelta(hours=timezones[timezone.upper()])
        try:
            actual_time = parse(schedule_time)
        except Exception as e:
            return None
        corrected_time = actual_time - time_adjustment - timezone_adjustment
        return corrected_time
        
    @app_commands.command(name="get_time")
    #@app_commands.guilds(83058900537966592)
    async def get_time_command(self, interaction:discord.Interaction,
                      schedule_time:str, timezone:str):
        corrected_time = self.getTime(schedule_time, timezone)
        await interaction.response.send_message(discord.utils.format_dt(corrected_time))

    @app_commands.command(name="start_lineup_named")
    #@app_commands.guilds(305351582017388544)
    async def start_lineup_named(self, interaction:discord.Interaction,
                          name:str):
        if interaction.channel_id not in self.lineups.keys():
            self.lineups[interaction.channel_id] = Channel_List()
        self.lineups[interaction.channel_id].add_named(name)
        await interaction.response.send_message(f"{interaction.user.display_name} has started a lineup in this channel named: `{name}`")

    @app_commands.command(name="start_lineup_time")
    #@app_commands.guilds(305351582017388544)
    async def start_lineup_time(self, interaction:discord.Interaction,
                          schedule_time:str, timezone:str):
        if interaction.channel_id not in self.lineups.keys():
            self.lineups[interaction.channel_id] = Channel_List()
        corrected_time = self.getTime(schedule_time, timezone)
        if corrected_time is None:
            await interaction.response.send_message("Your time could not be parsed, try again", ephemeral=True)
            return
        self.lineups[interaction.channel_id].add_time(corrected_time)
        send_time = discord.utils.format_dt(corrected_time)
        await interaction.response.send_message(f"{interaction.user.display_name} has started a lineup in this channel for {send_time}")

    @app_commands.command(name="channel_lineups")
    #@app_commands.guilds(305351582017388544)
    async def channel_lineups(self, interaction:discord.Interaction):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        if len(self.lineups[interaction.channel.id]) == 0:
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        lu_list = "**Lineups\n**"
        for lu in self.lineups[interaction.channel_id]:
            lu_list += f"{str(lu)}\n"
        await interaction.response.send_message(lu_list)

    @app_commands.command(name="can")
    #@app_commands.guilds(305351582017388544)
    async def can(self, interaction:discord.Interaction, name:str):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        lu = self.lineups[interaction.channel_id].get_name(name)
        if lu is None:
            await interaction.response.send_message("There is no lineup in this channel with that name!", ephemeral=True)
            return
        lu.add_player(interaction.user)
        await interaction.response.send_message(f"`{interaction.user.display_name}` has joined the lineup named `{name}` ({len(lu)} players)")

    @app_commands.command(name="can_time")
    #@app_commands.guilds(305351582017388544)
    async def can_time(self, interaction:discord.Interaction,
                       schedule_time:str, timezone:str):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        corrected_time = self.getTime(schedule_time, timezone)
        if corrected_time is None:
            await interaction.response.send_message("Your time could not be parsed, try again", ephemeral=True)
        lu = self.lineups[interaction.channel.id].get_time(corrected_time)
        if lu is None:
            await interaction.response.send_message("There is no lineup in this channel at that time!", ephemeral=True)
            return
        lu.add_player(interaction.user)
        send_time = discord.utils.format_dt(corrected_time)
        await interaction.response.send_message(f"`{interaction.user.display_name}` has joined the lineup at {send_time} ({len(lu)} players)")

    @app_commands.command(name="drop")
    #@app_commands.guilds(305351582017388544)
    async def drop(self, interaction:discord.Interaction, name:str):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        lu = self.lineups[interaction.channel_id].get_name(name)
        if lu is None:
            await interaction.response.send_message("There is no lineup in this channel with that name!", ephemeral=True)
            return
        lu.drop_player(interaction.user)
        await interaction.response.send_message(f"`{interaction.user.display_name}` has dropped from the lineup named `{name}` ({len(lu)} players)")

    @app_commands.command(name="drop_time")
    #@app_commands.guilds(305351582017388544)
    async def drop_time(self, interaction:discord.Interaction,
                        schedule_time:str, timezone:str):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        corrected_time = self.getTime(schedule_time, timezone)
        if corrected_time is None:
            await interaction.response.send_message("Your time could not be parsed, try again", ephemeral=True)
        lu = self.lineups[interaction.channel.id].get_time(corrected_time)
        if lu is None:
            await interaction.response.send_message("There is no lineup in this channel at that time!", ephemeral=True)
            return
        lu.drop_player(interaction.user)
        send_time = discord.utils.format_dt(corrected_time)
        await interaction.response.send_message(f"`{interaction.user.display_name}` has dropped from the lineup at {send_time} ({len(lu)} players)")

    @app_commands.command(name="end")
    #@app_commands.guilds(305351582017388544)
    async def end(self, interaction:discord.Interaction, name:str):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        ended = self.lineups[interaction.channel.id].end_name(name)
        if not ended:
            await interaction.response.send_message("There is no lineup in this channel with that name!", ephemeral=True)
            return
        await interaction.response.send_message(f"`{interaction.user.display_name}` has ended the lineup named {name}")

    @app_commands.command(name="end_time")
    #@app_commands.guilds(305351582017388544)
    async def end_time(self, interaction:discord.Interaction,
                       schedule_time:str, timezone:str):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        corrected_time = self.getTime(schedule_time, timezone)
        if corrected_time is None:
            await interaction.response.send_message("Your time could not be parsed, try again", ephemeral=True)
        ended = self.lineups[interaction.channel.id].end_time(corrected_time)
        if not ended:
            await interaction.response.send_message("There is no lineup in this channel at that time!", ephemeral=True)
            return
        send_time = discord.utils.format_dt(corrected_time)
        await interaction.response.send_message(f"`{interaction.user.display_name}` has ended the lineup at {send_time}")

    @app_commands.command(name="end_all")
    #@app_commands.guilds(305351582017388544)
    async def end_all(self, interaction:discord.Interaction):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        self.lineups[interaction.channel.id].end_all()
        await interaction.response.send_message(f"`{interaction.user.display_name}` has ended all lineups in this channel")

    @app_commands.command(name="list")
    #@app_commands.guilds(305351582017388544)
    async def list(self, interaction:discord.Interaction,
                   name:str):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        lu = self.lineups[interaction.channel_id].get_name(name)
        if lu is None:
            await interaction.response.send_message("There is no lineup in this channel with that name!", ephemeral=True)
            return
        players = ""
        for i, player in enumerate(lu):
            players += f"`{i+1}.` {player.display_name}\n"
        await interaction.response.send_message(f"`Lineup: {name}`\n{players}")

    @app_commands.command(name="list_time")
    #@app_commands.guilds(305351582017388544)
    async def list_time(self, interaction:discord.Interaction,
                   schedule_time:str, timezone:str):
        if interaction.channel_id not in self.lineups.keys():
            await interaction.response.send_message("There are no lineups in this channel!", ephemeral=True)
            return
        corrected_time = self.getTime(schedule_time, timezone)
        if corrected_time is None:
            await interaction.response.send_message("Your time could not be parsed, try again", ephemeral=True)
        lu = self.lineups[interaction.channel.id].get_time(corrected_time)
        if lu is None:
            await interaction.response.send_message("There is no lineup in this channel at that time!", ephemeral=True)
            return
        players = ""
        for i, player in enumerate(lu):
            players += f"`{i+1}.` {player.display_name}\n"
        send_time = discord.utils.format_dt(corrected_time)
        await interaction.response.send_message(f"`Lineup:` {send_time}\n{players}")

        
async def setup(bot):
    await bot.add_cog(gathering(bot))
