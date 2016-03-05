import threading

import discord
# Import Local Files
import settings
from BettingSystem import PointsManager as Points, ImpMatch as Match, AutoIncrement as Increment
import Database


class Bot(object):
    def __init__(self):
        print("Bot is starting.")
        self.client = discord.Client()
        print("Discord Client Initiated")

        # Dictionary of Channel Objects
        self.channels = dict()
        self.roles = dict()

        self.matches = dict()

        self.tournaments = dict()

        self.points = None

        self.increment = None

        @self.client.event
        async def on_ready():
            print("Logged in as", self.client.user.name)
            print("Client User ID", self.client.user.id)
            print("-----------------------------------")
            for server in self.client.servers:
                self.matches[server.id] = None
                self.tournaments[server.id] = None
                self.channels[server.id] = dict()
                self.roles[server.id] = dict()
                print(server.name, ":")
                print("Roles:")
                for role in server.roles:
                    print(role.id, role.name)
                    self.roles[server.id][role.name] = role
                print("Channels:")
                for channel in server.channels:
                    self.channels[server.id][channel.name] = channel
                    print(channel.id, channel.name)
            self.updateMembers()

            print("Finished creating dictionaries for Roles, Channels, and Possible Match Servers.")

            self.points = Points.PointsManager(self.client)

            self.increment = Increment.Increment()
            self.increment.start()


            self.thread(self.updateList)

            self.client.send_message(self.channels[server.id]["testing"], "ONLINE")

        @self.client.event
        async def on_member_join(member):
            if self.points.insertNewMember(member.id, member.server.id):
                self.client.send_message(member, "Welcome to the Imperial Server!\nYou have started out with 50 points for betting in matches.\nCheck your points with **!points**.\nType **!help** for more information on commands!")
            else:
                print("Failed to add new member points.")

        @self.client.event
        async def on_message(message):
            print(message.author.id, ":", message.content)
            info = {
                "channel" : message.channel,
                "author" : message.author,
                "server" : message.server,
                "mentions" : message.mentions
                }
            if message.content.startswith("!"):
                msg_parts = message.content[1:]
                params = msg_parts.split(" ")
                command = params[0]
                rest = " ".join(params[1:])
                numParams = len(params) - 1

                def sender(msg):
                    return self.client.send_message(info['channel'], msg)

                def deleter(msg):
                    return self.client.delete_message(msg)

                def sendToBetting(msg):
                    if "betting" in self.channels[info['server'].id]:
                        return self.client.send_message(self.channels[message.server.id]["betting"], msg)
                    else:
                        return self.client.send_message(info['channel'], "Betting Channel does not exist on this server.")

                # ! Commands
                if command == "help":
                    await sender("**COMMANDS**\nIf bets are open:\n!bet <red or blue> <points> - *Bet on a team.*\n!points - *Check how many points you have.*")
                elif command == "purge":
                    await deleter(message)
                    if self.checkpower(message.author):
                        if numParams < 1:
                            sender("Please specify how many messages to purge.")
                        else:
                            async for log in self.client.logs_from(message.channel, limit=int(params[1])):
                                await deleter(log)

                # Betting Commands
                if message.channel == self.channels[message.server.id]["betting"]:
                    if command == "bet":
                        if numParams < 2:
                            await sender(message.author.mention + " - You did not enter enough parameters. **Example:** \"!bet red 100\"")
                        elif numParams > 2:
                            await sender(message.author.mention + " - You have used too many parameter for this command. Ex: \"!bet red 100\"")
                        elif numParams == 2:
                            try:
                                amount = int(params[2])
                            except ValueError:
                                await sender(message.author.mention + " - You did not enter a valid bet amount. Ex: \"!bet blue 100\"")
                            else:
                                team = str(params[1].lower())
                                if any(char.isdigit() for char in team):
                                    await sender(message.author.mention + " - You did not enter a valid team name. Ex: \"!bet blue 100\"")
                                elif team == "blue" or team == "red":
                                    if self.matches[message.server.id] is None:
                                        await sender(message.author.mention + " - No matches have been started as of yet.")
                                    elif self.matches[message.server.id] is not None:
                                        if not self.matches[message.server.id].betted(message.author.id):
                                            if self.matches[message.server.id].addVote(message.author, team, amount):
                                                if team == "red":
                                                    icon = ":red_circle:"
                                                elif team == "blue":
                                                    icon = ":large_blue_circle:"
                                                else:
                                                    icon = ""
                                                await sender(icon + " - " + message.author.mention + " you have placed a bet on **" + team.upper() + "** for " + str(amount) + " points.")
                                            else:
                                                await sender(message.author.mention + " bets are no open at the moment.")
                                        else:
                                            await sender(message.author.mention + " you have already bet.")
                                    else:
                                        await sender(message.author.mention + " - You did not enter a valid team name. Ex: \"!bet blue 100\"")
                    elif command == "points":
                        if numParams >= 1:
                            if self.checkpower(message.author):
                                await deleter(message)
                                for user in message.mentions:
                                    await sender(message.author.mention + " has " + str(self.points.checkpoints(message.server.id, user.id)) + " points.")
                            else:
                                await sender(message.author.mention + " - Insufficient permissions.")
                        else:
                            await sender(message.author.mention + " has " + str(self.points.checkpoints(message.server.id, message.author.id)) + " points.")
                    elif command == "start":
                        await deleter(message)
                        if self.checkpower(message.author):
                            if self.matches[message.server.id] == None:
                                self.matches[message.server.id] = Match.Match(message.server.id)
                                await sendToBetting("@everyone\nBets are open for this round! Place your Bets with \"!bet red <amount>\" or \"!bet blue <amount>\"!!")
                            else:
                                await sender(message.author.mention + " - A match is already underway.")
                        else:
                            await sender(message.author.mention + " - Insufficient Permissions")
                    elif command == "match":
                        while True:
                            try:
                                await deleter(message)
                                if self.checkpower(message.author):
                                    if self.matches[message.server.id] == None:
                                        await sender(message.author.mention + " - A match has not been started yet.")
                                    else:
                                        self.matches[message.server.id].closeBetting()
                                        await sender("@everyone - Betting has closed for this match. Match is underway!")
                                else:
                                    await sender(message.author.mention + " - Insufficient Permissions")
                            except discord.HTTPException:
                                continue
                            break
                    elif command == "end":
                        await deleter(message)
                        if self.checkpower(message.author):
                            if self.matches[message.server.id] == None:
                                await sender(message.author.mention + " - There is no match to end.")
                            else:
                                self.matches[message.server.id] = None
                                await sender("This match has ended.")
                        else:
                            await sender(message.author.mention + " - Insufficient Permissions")
                    elif command.endswith("win"):
                        await deleter(message)
                        if self.checkpower(message.author):
                            if self.matches[message.server.id] == None:
                                await sender(message.author.mention + " - A match has not be started yet")
                            else:
                                if command == "redwin":
                                    winner = "red"
                                elif command == "bluewin":
                                    winner = "blue"
                                results = self.matches[message.server.id].cashout(winner)
                                results_message = ""
                                await sender("**" + winner.upper() + "** has won!")
                                for result in results:
                                    results_message = results_message + result.user.mention + " you have won " + str(result.winnings) + " points.\n"
                                await sender(results_message)
                                self.matches[message.server.id] = None
                                await sender("Match has ended.")
                    elif command == "give":
                        await deleter(message)
                        if self.checkpower(message.author):
                            if numParams < 0:
                                await sender("Give command requires parameters \"!give <mention> <points>\"")
                            else:
                                points = int(params[2])
                                person = message.mentions[0].id
                                self.points.givepoints(points, message.server.id, person)
                                await sendToBetting(str(points) + " points given to " + message.mentions[0].mention)
                        else:
                            await sender(message.author.mention + " - Insufficient Permissions")
                    elif command == "test":
                        await sender("Test")

        self.client.run(settings.DISCORD_USERNAME, settings.DISCORD_PASSWORD)

    def checkpower(self, author):
        if settings.Roles.check(author, settings.Roles.DEVELOPER) or settings.Roles.check(author, settings.Roles.ADMIN):
            return True
        else:
            return False

    def thread(self, function):
            t1 = threading.Thread(target=function)
            t1.daemon = True
            t1.start()

    def updateList(self):
        list_ids = dict()
        while True:
            servers = self.client.servers
            for server in servers:
                list_ids[server.id] = []
                members = server.members
                for member in members:
                    status = member.status.value
                    if status is not "offline":
                        list_ids[server.id].append(member.id)
                self.increment.updateList(list_ids)

    def updateMembers(self):
        conn = Database.DB()
        servers = self.client.servers
        for server in servers:
            print("Generating Missing Members for Server: " + server.name + "...")
            members = server.members
            for member in members:
                with conn.cursor() as cursor:
                    sql = "INSERT IGNORE INTO `points` SET `userid`={0}, `points`={1}, `server`={2};".format(member.id, 50, server.id)
                    cursor.execute(sql)
                    conn.commit()
                    print(cursor._last_executed)
        conn.close()