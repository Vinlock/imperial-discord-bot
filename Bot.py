import threading

import discord
# Import Local Files
import settings
from BettingSystem import PointsManager as Points, ImpMatch as Match, AutoIncrement as Increment
import Database
from Tournament import Tournament as T
import ObjectDict

from time import sleep

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

            self.thread(self.updateMembers)

            print("Finished creating dictionaries for Roles, Channels, and Possible Match Servers.")

            self.points = Points.PointsManager(self.client)

            self.increment = Increment.Increment()
            self.increment.start()

            for server in self.client.servers:
                self.client.send_message(self.channels[server.id]["testing"], "ONLINE")

            self.thread(self.updateList)

        @self.client.event
        async def on_member_join(member):
            if self.points.insertNewMember(member.id, member.server.id):
                self.client.send_message(member, "Welcome to the Imperial Server!\n"
                                                 "You have started out with 50 points for betting in matches.\n"
                                                 "Check your points with **!points**.\n"
                                                 "Type **!help** for more information on commands!")
            else:
                print("Failed to add new member points.")

        @self.client.event
        async def on_message(message):
            print(message.author.id, ":", message.content)
            info = {
                "channel": message.channel,
                "author": message.author,
                "server": message.server,
                "mentions": message.mentions
                }
            # if "Kappa" in message.content:
            #     await self.client.send_file(message.channel, "files/kappa1.png")
            if message.content is "!":
                print("Nothing happened.")
            elif message.content.startswith("!"):
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
                        return self.client.send_message(info['channel'], "Betting Channel does not exist on this "
                                                                         "server.")

                # ! Commands
                if command == "help" or command == "commands":
                    await sender("**COMMANDS**\n"
                                 "If bets are open:\n"
                                 "**!bet <red or blue> <points>** - *Bet on a team.*\n"
                                 "**!points** - *Check how many points you have.*")
                elif command == "purge":
                    await deleter(message)
                    if self.checkpower(message.author):
                        if numParams < 1:
                            sender("Please specify how many messages to purge.")
                        elif numParams == 1:
                            async for log in self.client.logs_from(message.channel, limit=int(params[1])):
                                await deleter(log)
                        elif numParams == 2:
                            numDelete = int(params[2])
                            async for log in self.client.logs_from(message.channel, limit=numDelete*100):
                                if log.author == message.mentions[0]:
                                    if numDelete > 0:
                                        await deleter(log)
                                        numDelete -= 1
                        elif numParams > 2:
                            sender("Invalid Command Parameters")
                elif command == "version":
                    await sender("Imperial Bot v0.1b - Created By: Vinlock")
                elif command == "admin":
                    if self.checkpower(message.author):
                        await self.client.send_message(message.author, "__**COMMANDS**__\n**!purge <number of messages>"
                                                                       " <mention user ***OPTIONAL***>** - Purges X "
                                                                       "number of messages in the channel. Optionally "
                                                                       "mention a user to purge only their messages.\n"
                                                                       "**!give <mention user> <points>** - Give a user"
                                                                       " a certain number of points. (Cap: 50000)\n"
                                                                       "**!start** - Start a round of betting.\n"
                                                                       "**!set <team> <mention user>** - Give each "
                                                                       "team a name.\n**!match** - Ends bettings "
                                                                       "and announces that the match is underway.\n"
                                                                       "**!points <mention user>** - Check a users "
                                                                       "points total.")
                    else:
                        print("Nope")
                elif command == "tournament":
                    if self.checkpower(message.author):
                        if numParams < 1 or numParams > 1:
                            await sender(message.author.mention + " - You did not input the correct parameters."
                                                                  " **Example:** !tournament <start or end>")
                        todo = params[1]
                        if todo == "start":
                            if self.tournaments[message.server.id] is None:
                                self.tournaments[message.server.id] = T.Tournament(message.server.id, message.author)
                                if self.tournaments[message.server.id].start():
                                    await self.client.send_message(self.channels[message.server.id]["waiting-room"],
                                                                   message.author.mention + " has started a new tournament. "
                                                                                            "Please use **!checkin** to "
                                                                                            "check in or **!waitlist** "
                                                                                            "if you are waitlisted.")
                            else:
                                await sender(message.author.mention + " - A tournament has already been started by " +
                                             self.tournaments[message.server.id].starter.mention + ".")
                        elif todo == "end":
                            if self.tournaments[message.server.id] is None:
                                await sender(message.author.mention + " - There is no tournament started to end.")
                            else:
                                self.tournaments[message.server.id] = None
                                await sender("@everyone - The tournaments has ended. Thank you for your support and "
                                             "cooperation. We appreciate it and hope to see you next time!")
                        else:
                            await sender(message.author.mention + " - You did not input the correct parameters."
                                                                  " **Example:** !tournament <start or end>")
                    else:
                        await sender("")
                elif command == "checkedin":
                    if self.checkpower(message.author):
                        if self.tournaments[message.server.id] is not None:
                            i = 0
                            checked = ""
                            for user in self.tournaments[message.server.id].checkin:
                                checked = checked + user.name + ", "
                                i += 1
                            checked = checked[:-2]
                            j = 0
                            wait = ""
                            for user in self.tournaments[message.server.id].waitinglist:
                                wait = wait + user.name + ", "
                                j += 1
                            wait = wait[:-2]
                            await sender(str(i) + " users have checked in.\n" + checked)
                            await sender(str(j) + " users have checked in on the waitlist.\n" + wait)
                        else:
                            await sender(message.author.mention + " - No tournament has been started yet.")
                elif command == "game":
                    if self.checkpower(message.author):
                        game = rest
                        newgame = {"name": game}
                        newgame = ObjectDict.ObjectDict(newgame)
                        self.client.change_status(newgame)
                    else:
                        await sender(message.author.mention + " - Insufficient Permissions")
                elif command == "join":
                    await deleter(message)
                    if self.checkpower(message.author):
                        url = params[1]
                        invite = self.client.accept_invite(url)
                        await sender("I have joined " + invite.server.name)

                # Betting Commands
                if message.channel == self.channels[message.server.id]["betting"]:
                    if command == "bet":
                        if self.matches[message.server.id] is None:
                            await sender(message.author.mention + " - No match has been started yet.")
                        elif self.matches[message.server.id] is not None:
                            if numParams < 2:
                                await sender(message.author.mention + " - You did not enter enough parameters. "
                                                                      "**Example:** \"!bet red 100\"")
                            elif numParams > 2:
                                await sender(message.author.mention + " - You have used too many parameter for this "
                                                                      "command. Ex: \"!bet red 100\"")
                            elif numParams == 2:
                                try:
                                    amount = int(params[2])
                                except ValueError:
                                    await sender(message.author.mention + " - You did not enter a valid bet amount. "
                                                                          "Ex: \"!bet blue 100\"")
                                else:
                                    team = str(params[1].lower())
                                    if any(char.isdigit() for char in team):
                                        await sender(message.author.mention + " - You did not enter a valid team name. "
                                                                              "Ex: \"!bet blue 100\"")
                                    elif team == "blue" or team == "red":
                                        if not self.matches[message.server.id].bettingOpen:
                                            await sender(message.author.mention + " - Betting has been closed")
                                        elif self.matches[message.server.id].bettingOpen:
                                            if not self.matches[message.server.id].betted(message.author.id):
                                                if self.matches[message.server.id].addVote(message.author,
                                                                                           team,
                                                                                           amount):
                                                    if team == "red":
                                                        icon = ":red_circle:"
                                                    elif team == "blue":
                                                        icon = ":large_blue_circle:"
                                                    else:
                                                        icon = ""
                                                    await sender(icon +
                                                                 " - " +
                                                                 message.author.mention +
                                                                 " you have placed a bet on **" +
                                                                 team.upper() +
                                                                 "** for " +
                                                                 str(amount) +
                                                                 " points.")
                                                else:
                                                    await sender(message.author.mention + " insufficient points to bet "
                                                                                          "that amount. You only have "
                                                                 + str(self.points.checkpoints(message.server.id,
                                                                                               message.author.id)) +
                                                                 " points.")
                                            else:
                                                await sender(message.author.mention + " you have already bet.")
                                        else:
                                            await sender(message.author.mention +
                                                         " - You did not enter a valid team name. "
                                                         "Ex: \"!bet blue 100\"")
                    elif command == "points":
                        if numParams == 1:
                            if self.checkpower(message.author):
                                await deleter(message)
                                for user in message.mentions:
                                    await sender(user.mention +
                                                 " has **" +
                                                 str(self.points.checkpoints(message.server.id, user.id)) +
                                                 "** points.")
                            else:
                                await sender(message.author.mention + " - Insufficient permissions.")
                        else:
                            await sender(message.author.mention +
                                         " has **" +
                                         str(self.points.checkpoints(message.server.id, message.author.id)) +
                                         "** points.")
                    elif command == "start":
                        await deleter(message)
                        if self.checkpower(message.author):
                            if self.matches[message.server.id] is None:
                                self.matches[message.server.id] = Match.Match(message.server.id)
                                await sendToBetting("@everyone\n\n**Bets are open for this round! Place your Bets with "
                                                    "\"!bet red <amount>\" or \"!bet blue <amount>\"!!**\n"
                                                    "------------------------------------------------------------------"
                                                    "-------")
                            else:
                                await sender(message.author.mention + " - A match is already underway.")
                        else:
                            await sender(message.author.mention + " - Insufficient Permissions")
                    elif command == "match":
                        while True:
                            try:
                                await deleter(message)
                                if self.checkpower(message.author):
                                    if self.matches[message.server.id] is None:
                                        await sender(message.author.mention + " - A match has not been started yet.")
                                    else:
                                        self.matches[message.server.id].closeBetting()
                                        await sender("@everyone - Betting has closed for this match. "
                                                     "Match is underway!")
                                else:
                                    await sender(message.author.mention + " - Insufficient Permissions")
                            except discord.HTTPException:
                                continue
                            break
                    elif command == "end":
                        await deleter(message)
                        if self.checkpower(message.author):
                            if self.matches[message.server.id] is None:
                                await sender(message.author.mention + " - There is no match to end.")
                            else:
                                self.matches[message.server.id] = None
                                await sender("This match has ended.")
                        else:
                            await sender(message.author.mention + " - Insufficient Permissions")
                    elif command.endswith("win"):
                        await deleter(message)
                        if self.checkpower(message.author):
                            if self.matches[message.server.id] is None:
                                await sender(message.author.mention + " - A match has not be started yet")
                            else:
                                if command == "redwin":
                                    winner = "red"
                                elif command == "bluewin":
                                    winner = "blue"
                                results = self.matches[message.server.id].cashout(winner)
                                # results_message = ""
                                await sender("**" + self.matches[message.server.id].getName(winner, True) +
                                             "** has won!")
                                for result in results:
                                    await sender(result.user.mention + " you have won **" + str(result.winnings) +
                                                 "** points.")
                                self.matches[message.server.id] = None
                                await sender("Match has ended.")
                    elif command == "give":
                        await deleter(message)
                        if numParams < 2:
                            await sender(message.author.mention + " - Give command requires parameters "
                                                                  "\"**Example:** !give <mention> <points>\"")
                        else:
                            try:
                                points = int(params[2])
                            except ValueError:
                                await sender("Invalid points amount. Be sure to **not** use commas.")
                            else:
                                if points > 500000:
                                    sender(message.author.mention + " - You cannot give that many points. "
                                                                    "Must be 500,000 or under")
                                else:
                                    person = message.mentions[0].id
                                    if not self.checkpower(message.author):
                                        if self.points.minusPoints(points, message.server.id, message.author.id):
                                            if self.points.givepoints(points, message.server.id, person):
                                                await sendToBetting(message.author.mention + " gave " + str(points) +
                                                                    " points to " + message.mentions[0].mention)
                                            else:
                                                self.points.givepoints(points, message.server.id, message.author.id)
                                        else:
                                            await sender(message.author.mention +
                                                         " insufficient points to bet that amount. You only have " +
                                                         str(self.points.checkpoints(message.server.id,
                                                                                     message.author.id)) + " points.")
                                    elif self.checkpower(message.author):
                                        if self.points.givepoints(points, message.server.id, person):
                                            await sendToBetting(message.author.mention + " gave " + str(points) +
                                                                " points to " + message.mentions[0].mention)
                                        else:
                                            await sender("Give Failed")
                    elif command == "take":
                        await deleter(message)
                        if self.checkpower(message.author):
                            if numParams < 2 or numParams > 2:
                                await sender(message.author.mention + " - Take command requires parameters. "
                                                                      "\"**Example:** !take <mention> <points>\"")
                            else:
                                try:
                                    points = int(params[2])
                                    who = message.mentions[0]
                                except ValueError:
                                    await sender("Invalid points amount. Be sure to **not** use commas.")
                                else:
                                    available_points = self.points.checkpoints(message.server.id, who.id)
                                    if points > available_points:
                                        await sender(message.author.mention + " - " + who.mention + " only has " +
                                                     str(available_points) + " points, therefore not enough to take " +
                                                     str(points) + " points.")
                                    elif available_points > points:
                                        if self.points.minusPoints(points, message.server.id, who.id):
                                            await sender(message.author.mention + " has taken " + str(points) +
                                                         " points from " + who.mention + ".")
                                        else:
                                            await sender(message.author.mention + " Take failed!")
                        else:
                            await sender(message.author.mention + " - Insufficient permissions.")
                    elif command == "giveall":
                        await deleter(message)
                        if self.checkpower(message.author):
                            if numParams < 1 or numParams > 1:
                                await sender(message.author.mention + " - You must declare the number of points.")
                            else:
                                try:
                                    points = int(params[1])
                                except ValueError:
                                    await sender(message.author.mention +
                                                 " - You must declare a number for points parameter.")
                                else:
                                    list_ids = []
                                    members = message.server.members
                                    for member in members:
                                        status = member.status.value
                                        if status is not "offline":
                                            list_ids.append(member.id)
                                    if self.points.massGive(message.server.id, list_ids, points):
                                        await sender(message.author.mention + " gave " + str(points) +
                                                     " points to @everyone!!\n\n:moneybag: :moneybag: :moneybag: "
                                                     ":moneybag: :moneybag: :moneybag: :moneybag: :moneybag: "
                                                     ":moneybag: :moneybag: :moneybag: :moneybag: ")
                    elif command == "percent":
                        red = self.matches[message.server.id].redPercent()
                        blue = self.matches[message.server.id].bluePercent()
                        await sender(":large_blue_circle: **" + self.matches[message.server.id].getName("blue") +
                                     "** - " + str(round(blue, 1)) + "% vs. " + str(round(red, 1)) + "% - **" +
                                     self.matches[message.server.id].getName("red") + "** :red_circle:")
                    elif command == "test":
                        await sender("Test")
                    elif command.startswith("set"):
                        if self.checkpower(message.author):
                            if not self.matches[message.server.id] is None:
                                if numParams < 2 or numParams > 2:
                                    await sender(message.author.mention + " - Incorrect number of parameters. "
                                                                          "!set <team> <mention user>")
                                else:
                                    team = params[1]
                                    user = message.mentions[0]
                                    if team == "red":
                                        self.matches[message.server.id].redName = user
                                        await sender(":red_circle: - You have set **RED**'s name to " +
                                                     self.matches[message.server.id].getName("red"))
                                    elif team == "blue":
                                        self.matches[message.server.id].blueName = user
                                        await sender(":large_blue_circle: - You have set **BLUE**'s name to " +
                                                     self.matches[message.server.id].getName("blue"))
                                    else:
                                        await sender(message.author.mention + " - Invalid Team.")
                            else:
                                await sender(message.author.mention + " - A match must be started first.")
                        else:
                            await sender(message.author.mention + " - Insufficient Permissions")
                    elif command == "who":
                        if not self.matches[message.server.id] is None:
                            team = params[1]
                            team = team.lower()
                            if team == "red" or team == "blue":
                                name = self.matches[message.server.id].getName(team)
                                if team == "red":
                                    icon = ":red_circle:"
                                elif team == "blue":
                                    icon = ":large_blue_circle:"
                                else:
                                    icon = ""
                                if name == "RED" or name == "BLUE":
                                    await sender(message.author.mention + " - Team name not set for " + team)
                                else:
                                    await sender(icon + " **" + team.upper() + "** = " + name)
                            else:
                                await sender(message.author.mention + " - You did not input a valid team.")
                        else:
                            await sender(message.author.mention + " - No match has been started.")
                elif message.channel == self.channels[message.server.id]["waiting-room"]:
                    if command == "checkin":
                        if self.tournaments[message.server.id] is not None:
                            if self.tournaments[message.server.id].addCheckIn(message.author):
                                await sender(message.author.mention + " has checked in.")
                            else:
                                await sender(message.author.mention + " - Failed to check in.")
                        else:
                            await sender(message.author.mention + " - No tournament has been started yet.")
                    elif command == "waitlist":
                        if self.tournaments[message.server.id] is not None:
                            if self.tournaments[message.server.id].addWaitingList(message.author):
                                await sender(message.author.mention + " has checked in for the waitlist.")
                            else:
                                await sender(message.author.mention + " - Failed to check in on waitlist")
                        else:
                            await sender(message.author.mention + " - No tournament has been started yet.")


        self.client.run(settings.DISCORD_USERNAME, settings.DISCORD_PASSWORD)

    def checkpower(self, author):
        for role in author.roles:
            check = role.permissions.manage_channels
            if check:
                return True
            else:
                continue
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
            sleep(7)

    def updateMembers(self):
        conn = Database.DB()
        servers = self.client.servers
        for server in servers:
            print("Generating Missing Members for Server: " + server.name + "...")
            members = server.members
            for member in members:
                with conn.cursor() as cursor:
                    sql = "INSERT IGNORE INTO `points` SET `userid`={0}, `points`={1}, `server`={2};".format(member.id,
                                                                                                             50,
                                                                                                             server.id)
                    cursor.execute(sql)
                    conn.commit()
                    print(cursor._last_executed)
        conn.close()