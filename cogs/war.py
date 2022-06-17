import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import json
from typing import Optional

with open('./tracks.json', 'r') as cjson:
    tracks = json.load(cjson)

spotScores = {
    "mk8": {
        2: [5, 3, 2, 1],
        3: [7, 5, 4, 3, 2, 1],
        4: [10, 8, 6, 5, 4, 3, 2, 1],
        5: [12, 10, 8, 7, 6, 5, 4, 3, 2, 1],
        6: [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        "sum": [11, 22, 39, 58, 82]
    },
    "mkw": {
        2: [15, 9, 4, 1],
        3: [15, 10, 6, 3, 1, 0],
        4: [15, 11, 8, 6, 4, 2, 1, 0],
        5: [15, 12, 10, 8, 6, 4, 3, 2, 1, 0],
        6: [15, 12, 10, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        "sum": [29, 35, 47, 61, 73]
    }
}
placements = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th"]

class war(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

        self.ongoing_wars = {}
        
    def getRaceScores(self, game, size, args):
        t1race = 0
        places = []
        for i in range(len(args)):
            t1race += spotScores[game][size][args[i]-1]
            places.append(placements[args[i]-1])
        t2race = spotScores[game]["sum"][len(args)-2] - t1race
        
        return t1race, t2race, places

    def createScoreEmbed(self, channelid):
        wartracks = self.ongoing_wars[channelid]["tracks"]
        game = self.ongoing_wars[channelid]["game"]
        e = discord.Embed(title="Total Score after Race %d" % len(wartracks))
        team1 = self.ongoing_wars[channelid]["team1"]
        team2 = self.ongoing_wars[channelid]["team2"]
        t1score = self.ongoing_wars[channelid]["score1"]
        t2score = self.ongoing_wars[channelid]["score2"]
        racescores = self.ongoing_wars[channelid]["racescores"]
        penalties = self.ongoing_wars[channelid]["penalties"]
        e.add_field(name=team1, value=t1score)
        e.add_field(name=team2, value=t2score)
        e.add_field(name="Difference", value=t1score-t2score, inline=False)
        if len(wartracks) > 0 and self.ongoing_wars[channelid]["showRaceScores"] is True:
            raceScores = "```"
            for i in range(len(wartracks)):
                if i == 12: #only showing first 12 races
                    break
                raceScores += str((i+1)).rjust(2)
                raceScores += " | {:02d} - {:02d} ({:+d})".format(racescores[0][i], racescores[1][i],
                                                                 racescores[0][i]-racescores[1][i])
                if wartracks[i] is not None:
                    raceScores += " (%s)" % tracks["properCase"][game][wartracks[i]]
                raceScores += "\n"
            raceScores += "```"
            e.add_field(name="Race Scores (first 12)", value=raceScores)
        if len(penalties) > 0:
            pens = "```"
            for penalty in penalties:
                #print(penalty)
                pens += "Race %d: %s -%d\n" % (penalty["raceNum"], penalty["team"], penalty["amount"])
            pens += "```"
            e.add_field(name="Penalties", value=pens, inline=False)
        return e

    @app_commands.command(name="score")
    #@app_commands.guilds(305351582017388544)
    async def score(self, interaction:discord.Interaction):
        if interaction.channel_id not in self.ongoing_wars:
            await interaction.response.send_message("There is no war going on in this channel! Use /startwar to use this command")
            return
        e = self.createScoreEmbed(interaction.channel_id)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="checkrace")
    #@app_commands.guilds(305351582017388544)
    @app_commands.choices(
        game=[
        Choice(name='MK8DX', value='mk8'),
        Choice(name='MKW', value='mkw'),
        Choice(name='MKTour', value='mk8'),
        Choice(name='MK7', value='mk8')
        ])
    async def checkrace(self, interaction:discord.Interaction,
                        spots:str, game:Choice[str]):
        strSpotsList = spots.strip().split(" ")
        spotsList = []
        for spot in strSpotsList:
            try:
                intSpot = int(spot)
            except Exception as e:
                await interaction.response.send_message(f"The spot {spot} is not a valid number! Try again")
                return
            if intSpot < 1 or intSpot > 12:
                await interaction.response.send_message(f"The spot {intSpot} is not between 1 and 12! Try again")
                return
            spotsList.append(intSpot)
        if len(set(spotsList)) != len(spotsList):
            await interaction.response.send_message(f"You cannot enter duplicate spots! Try again")
            return
        size = len(spotsList)
        t1race, t2race, places = self.getRaceScores(game.value, size, spotsList)
        e = discord.Embed(title="Race Score")
        e.add_field(name="Spots", value=", ".join(places), inline=False)
        e.add_field(name="Score", value="%d - %d" % (t1race, t2race), inline=False)
        e.add_field(name="Difference", value=t1race-t2race, inline=False)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="race")
    #@app_commands.guilds(305351582017388544)
    async def race(self, interaction:discord.Interaction,
                   spots:str, track:Optional[str] = None):
        if interaction.channel_id not in self.ongoing_wars:
            await interaction.response.send_message("There is no war going on in this channel! Use /startwar to use this command")
            return
        size = self.ongoing_wars[interaction.channel_id]["size"]
        game = self.ongoing_wars[interaction.channel_id]["game"]
        strSpotsList = spots.strip().split(" ")
        if len(strSpotsList) != size:
            await interaction.response.send_message(f"The current war size is {size}v{size} but you entered {len(strSpotsList)} spots.")
            return
        spotsList = []
        for spot in strSpotsList:
            try:
                intSpot = int(spot)
            except Exception as e:
                await interaction.response.send_message(f"The spot {spot} is not a valid number! Try again")
                return
            if intSpot < 1 or intSpot > 12:
                await interaction.response.send_message(f"The spot {intSpot} is not between 1 and 12! Try again")
                return
            spotsList.append(intSpot)
        if len(set(spotsList)) != len(spotsList):
            await interaction.response.send_message(f"You cannot enter duplicate spots! Try again")
            return
        trackid = None
        if track is not None:
            if track.lower() in tracks["abbreviations"][game]:
                trackid = tracks["abbreviations"][game].index(track.lower())
        t1race, t2race, places = self.getRaceScores(game, size, spotsList)
        self.ongoing_wars[interaction.channel_id]["score1"] += t1race
        self.ongoing_wars[interaction.channel_id]["score2"] += t2race
        self.ongoing_wars[interaction.channel_id]["racescores"][0].append(t1race)
        self.ongoing_wars[interaction.channel_id]["racescores"][1].append(t2race)
        self.ongoing_wars[interaction.channel_id]["tracks"].append(trackid)

        raceEmbed = discord.Embed(title="Score for Race %d" % len(self.ongoing_wars[interaction.channel_id]["tracks"]))
        team1 = self.ongoing_wars[interaction.channel_id]["team1"]
        team2 = self.ongoing_wars[interaction.channel_id]["team2"]
        raceEmbed.add_field(name="Spots", value=", ".join(places), inline=False)
        raceEmbed.add_field(name=team1, value=t1race)
        raceEmbed.add_field(name=team2, value=t2race)
        raceEmbed.add_field(name="Difference", value=t1race-t2race, inline=False)
        
        if trackid is not None:
            raceEmbed.add_field(name="Track", value=tracks["names"][game][trackid], inline=False)
            raceEmbed.set_thumbnail(url=tracks["images"][game][trackid])
        await interaction.response.send_message(embed=raceEmbed)
        scoreEmbed = self.createScoreEmbed(interaction.channel_id)
        await interaction.channel.send(embed=scoreEmbed)

    @app_commands.command(name="penalty")
    #@app_commands.guilds(305351582017388544)
    async def penalty(self, interaction:discord.Interaction,
                      team:str, amount:app_commands.Range[int, 0, None]):
        if interaction.channel_id not in self.ongoing_wars:
            await interaction.response.send_message("There is no war going on in this channel! Use /startwar to use this command")
            return
        team1 = self.ongoing_wars[interaction.channel_id]["team1"]
        team2 = self.ongoing_wars[interaction.channel_id]["team2"]
        if team != team1 and team != team2:
            await interaction.response.send_message(f"The teams in this war are: {team1}, {team2}")
            return
        raceCount = len(self.ongoing_wars[interaction.channel_id]["tracks"])
        penAddition = {"raceNum":raceCount+1, "amount":amount, "team":team}
        self.ongoing_wars[interaction.channel_id]["penalties"].append(penAddition)
        if team == team1:
            self.ongoing_wars[interaction.channel_id]["score1"] -= amount
        else:
            self.ongoing_wars[interaction.channel_id]["score2"] -= amount
        await interaction.response.send_message(f"Successfully added -{amount} penalty to team {team}")

    def recalc(self, channelid:int):
        war = self.ongoing_wars[channelid]
        t1score = 0
        t2score = 0
        for i in range(len(war["racescores"][0])):
            t1score += war["racescores"][0][i]
            t2score += war["racescores"][1][i]
        for penalty in war["penalties"]:
            if penalty["team"] == war["team1"]:
                t1score -= penalty["amount"]
            elif penalty["team"] == war["team2"]:
                t2score -= penalty["amount"]
        war["score1"] = t1score
        war["score2"] = t2score

    @app_commands.command(name="revertscore")
    #@app_commands.guilds(305351582017388544)
    async def revertScore(self, interaction:discord.Interaction, race:app_commands.Range[int, 1, 12]):
        if interaction.channel_id not in self.ongoing_wars:
            await interaction.response.send_message("There is no war going on in this channel! Use /startwar to use this command")
            return
        war = self.ongoing_wars[interaction.channel_id]
        raceCount = len(war["tracks"])
        if race > raceCount:
            await interaction.response.send_message(f"You can only revert to a race <= the current race count({raceCount})")
            return
        for i in range(len(war["penalties"])):
            if war["penalties"][i]["raceNum"] > race:
                war["penalties"].pop(i)
        war["tracks"] = war["tracks"][:race]
        war["racescores"][0] = war["racescores"][0][:race]
        war["racescores"][1] = war["racescores"][1][:race]
        self.recalc(interaction.channel_id)
        e = self.createScoreEmbed(interaction.channel_id)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="startwar")
    #@app_commands.guilds(305351582017388544)
    @app_commands.choices(
        size=[
        Choice(name='2v2', value=2),
        Choice(name='3v3', value=3),
        Choice(name='4v4', value=4),
        Choice(name='5v5', value=5),
        Choice(name='6v6', value=6)
        ],
        game=[
        Choice(name='MK8DX', value='mk8'),
        Choice(name='MKW', value='mkw'),
        Choice(name='MKTour', value='mk8'),
        Choice(name='MK7', value='mk8')
        ])
    async def startwar(self, interaction: discord.Interaction,
                       team1:str, team2:str,
                       size: Choice[int],
                       game: Choice[str]):
        self.ongoing_wars[interaction.channel_id] = {
            "game": game.value,
            "size": size.value,
            "team1": team1,
            "team2": team2,
            "score1": 0,
            "score2": 0,
            "racescores": [[], []],
            "tracks": [],
            "penalties": [],
            "showRaceScores": True
            }
        await interaction.response.send_message(f"Started {game.name} {size.name}: {team1} vs {team2}:", ephemeral=False)

    @app_commands.command(name="stopwar")
    #@app_commands.guilds(305351582017388544)
    async def stopwar(self, interaction:discord.Interaction):
        if interaction.channel_id not in self.ongoing_wars:
            await interaction.response.send_message("There is no war going on in this channel! Use /startwar to use this command")
            return
        del self.ongoing_wars[interaction.channel_id]
        await interaction.response.send_message("Stopped war.")
        
        
        
async def setup(bot):
    await bot.add_cog(war(bot))
