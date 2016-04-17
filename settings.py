import configparser, os

config = configparser.RawConfigParser()
config.read('config.ini')

# Discord Account Information
DISCORD_USERNAME = config.get("DISCORD", "BOT_USERNAME")
DISCORD_PASSWORD = config.get("DISCORD", "BOT_PASSWORD")
DISCORD_OWNER_USERNAME = config.get("DISCORD", "OWNER_USERNAME")
DISCORD_OWNER_PASSWORD = config.get("DISCORD", "OWNER_PASSWORD")
DISCORD_TOKEN = config.get("DISCORD", "TOKEN")

# MySQL Database Information
DBHOST = config.get("DATABASE", "DBHOST")
DBUSER = config.get("DATABASE", "DBUSER")
DBPASS = config.get("DATABASE", "DBPASS")
DATABASE = config.get("DATABASE", "DATABASE")

# Discord Roles for Imperial
class Roles:
    ADMIN = "114150403280470021"
    STREAMER = "115891747459956737"
    SHOUTCASTER = "119089556770390016"
    CHAMPION = "121308109460340737"
    MODERATOR = "123858658634235904"
    NCSOFT = "128153441456488448"
    CM = "131935192158830592"
    SPONSOR = "141330757921669121"
    PARTICIPANT = "142152148002668544"
    WAITING = "143053355927732224"
    SUBSCRIBER = "148128215972577280"
    DEVELOPER = "148557963366367232"
    BOT = "148512660365770753"

    def check(member, check):
        for role in member.roles:
            if role.id == check:
                return True
            else:
                continue
        return False

class Channels:
    LF_SPAR = "153017412940201986"
    BETTING = "153034096925343744"
    WELCOME = "122523621246631939"
    RULES = "123898108865282050"
    WB_REPORT_SCORES = "145539691335122944"
    LB_REPORT_SCORES = "150761179130626048"
    LFG_3V3 = "153017367457169408"
    NOTICE_BOARD = "114150403280470021"
    WAITING_ROOM = "114166560171491335"
    ADMIN = "123907533550125056"
    FEEDBACK = "122187541104427008"
    TESTING = "153072010598154240"
    NSTRUCTIONS = "124175939973283840"

