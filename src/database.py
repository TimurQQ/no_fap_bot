import json
import os
from .user_stat import UserStat
from datetime import datetime
from datetime import date
import dateutil.parser
import dataclasses

class NoFapDB:
    def __init__(
            self,
            init_file = os.path.join("storage", "all_scores_saved.json"),
            memes_path = os.path.join("storage", "memes")
        ):
        self.data = dict()
        self.cached_memes = dict()
        self.file_storage_path = init_file
        if (os.path.exists(init_file)):
            with open(init_file, "r") as f:
                data = json.load(f)
                for uid in data.keys():
                    user_data = data[uid]
                    memes = user_data.get("collectedMemes", list())
                    isBlocked = user_data.get("isBlocked", False)
                    isWinner = user_data.get("isWinner", False)
                    self.data[int(uid)] = UserStat(
                        uid = user_data["uid"],
                        username = user_data["username"],
                        lastTimeFap = dateutil.parser.isoparse(user_data["lastTimeFap"]),
                        collectedMemes = memes,
                        isBlocked = isBlocked, 
                        isWinner = isWinner
                    )
        if (os.path.exists(memes_path)):
            for file_name in os.listdir(memes_path):
                day_of_file = int(file_name.split()[1].split("_")[0])
                if day_of_file not in self.cached_memes:
                    self.cached_memes[day_of_file] = [file_name]
                else:
                    self.cached_memes[day_of_file].append(file_name)

    def getBlackList(self):
        self.data[1271420441].isBlocked = True
        return {1271420441,}

    def __contains__(self, uid):
        return uid in self.data

    def addNewUser(self, uid, username, lastTimeFap):
        self.data[uid] = UserStat(uid, username, lastTimeFap, list(), False)
        with open(self.file_storage_path, "w") as f:
            json.dump(self.data, f, cls=EnhancedJSONEncoder)

    def getStatById(self, uid):
        return self.data[uid]

    def update(self, uid=None, lastTimeFap=None, newNickName=None, winnerFlag=None):
        if lastTimeFap is not None:
            self.data[uid].lastTimeFap = lastTimeFap
            return
        if newNickName is not None:
            self.data[uid].username = newNickName
            return
        if winnerFlag is not None:
            self.data[uid].isWinner = winnerFlag
            return
        with open(self.file_storage_path, "w") as f:
            json.dump(self.data, f, cls=EnhancedJSONEncoder)

    def getTop(self, page = 0):
        filtered_data = filter(lambda user: not user.isBlocked, self.data.values())
        sorted_data = sorted(filtered_data, key=lambda x: x.lastTimeFap)
        return sorted_data[page*10:(page+1)*10]

class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if dataclasses.is_dataclass(obj):
                return dataclasses.asdict(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, date):
                return obj.isoformat()
            return super().default(obj)

if __name__ == "__main__":
    testDB = NoFapDB()
    testDB.addNewUser(10, "timtim2379", datetime.now())