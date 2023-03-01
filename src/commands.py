#This file contains constants for command representation in bot
class Commands:
    def __init__(self):
        self.HelpCommand = "help"
        self.StartCommand = "start"
        self.StatisticsCommand = "stat"
        self.BlacklistCommand = "blacklist"
        self.SuggestMemeCommand = "suggest_meme"
        self.BanCommand = "ban (only for admins)"

    def getAllCommands(self) -> str:
        return "".join(map(lambda x: f"\n/{x}", self.__dict__.values()))
