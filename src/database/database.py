import json
import os
from .user_stat import UserStat
from datetime import datetime
from .states import UserContext
import dateutil.parser
from src.utils.json_encoder import EnhancedJSONEncoder
from src.utils.s3_backup import restore_database_from_s3, restore_memes_from_s3

class NoFapDB:
    def __init__(
            self,
            init_file = os.path.join("storage", "all_scores_saved.json"),
            memes_path = os.path.join("storage", "memes")
        ):
        self.data = dict()
        self.user_contexts = dict()
        self.cached_memes = dict()
        self.file_storage_path = init_file
        
        # Проверяем существование локального файла БД
        if not os.path.exists(init_file):
            # Пытаемся восстановить из S3
            self._try_restore_from_s3(init_file)
        
        # Проверяем существование папки с мемами
        if not os.path.exists(memes_path) or not os.listdir(memes_path):
            # Пытаемся восстановить мемы из S3
            self._try_restore_memes_from_s3(memes_path)
        
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
                    userContext = UserContext(int(uid))
                    userContext.addRefreshCallback(callback=self.refresh_user)
                    self.user_contexts[int(uid)] = userContext

        if (os.path.exists(memes_path)):
            for file_name in os.listdir(memes_path):
                day_of_file = int(file_name.split()[1].split("_")[0])
                if day_of_file not in self.cached_memes:
                    self.cached_memes[day_of_file] = [file_name]
                else:
                    self.cached_memes[day_of_file].append(file_name)

    def _try_restore_from_s3(self, database_path: str):
        """
        Пытается восстановить базу данных из S3 если локальный файл отсутствует.
        Падает с ошибкой если восстановление невозможно.
        
        Args:
            database_path: Путь к файлу базы данных
            
        Raises:
            RuntimeError: Если база данных не может быть восстановлена из S3
        """
        try:
            # Пытаемся восстановить из S3
            restore_database_from_s3(database_path)
            # Если дошли до сюда - восстановление успешно
                
        except Exception as e:
            # Любая ошибка при восстановлении - оборачиваем в понятное сообщение
            raise RuntimeError(
                f"❌ CRITICAL ERROR: Database file '{database_path}' not found locally "
                f"and S3 restoration failed: {e}. "
                f"Cannot start without database."
            )
    
    def _try_restore_memes_from_s3(self, memes_path: str):
        """
        Пытается восстановить папку с мемами из S3 если локальная папка пуста или отсутствует.
        
        Args:
            memes_path: Путь к папке с мемами
        """
        try:
            from logger import noFapLogger
            noFapLogger.info(f"🖼️ Memes folder is empty or missing: {memes_path}")
            noFapLogger.info("🔄 Attempting to restore memes from S3...")
            
            # Пытаемся восстановить мемы из S3
            restore_memes_from_s3(memes_path)
            
            # Проверяем что мемы восстановились
            if os.path.exists(memes_path) and os.listdir(memes_path):
                memes_count = len([f for f in os.listdir(memes_path) if os.path.isfile(os.path.join(memes_path, f))])
                noFapLogger.info(f"✅ Memes successfully restored from S3: {memes_count} files")
            else:
                noFapLogger.error("⚠️ Memes folder is still empty after S3 restoration")
                
        except Exception as e:
            from logger import noFapLogger
            noFapLogger.error(f"⚠️ Failed to restore memes from S3: {e}")
            noFapLogger.info("🎭 Bot will continue without memes (they can be restored later)")
            # Не падаем с ошибкой - мемы не критичны для работы бота
            # Создаем пустую папку чтобы избежать ошибок
            os.makedirs(memes_path, exist_ok=True)
    
    def getBlackList(self):
        bannedUIDs = map(lambda item: item[0], filter(lambda uStat: uStat[1].isBlocked, self.data.items()))
        return set(bannedUIDs)

    def __contains__(self, uid):
        return uid in self.data

    def addNewUser(self, uid, username, lastTimeFap):
        self.data[uid] = UserStat(uid, username, lastTimeFap, list(), False, False)
        userContext = UserContext(int(uid))
        userContext.addRefreshCallback(callback=self.refresh_user)
        self.user_contexts[int(uid)] = userContext
        with open(self.file_storage_path, "w") as f:
            json.dump(self.data, f, cls=EnhancedJSONEncoder, indent=4)

    def getStatById(self, uid):
        return self.data[uid]
    
    def refresh_user(self, uid):
        self.data[uid].lastTimeFap = datetime.now()

    def getUserIDFromNick(self, nickname):
        filtered = list(filter(lambda uStat: uStat[1].username == nickname, self.data.items()))
        if (len(filtered) == 0):
            return None
        firstFound = filtered[0]
        uid = firstFound[0]
        return uid

    def update(self, uid=None, lastTimeFap=None, newNickName=None, winnerFlag=None, bannedFlag=None):
        if lastTimeFap is not None:
            self.data[uid].lastTimeFap = lastTimeFap
            return
        if newNickName is not None:
            self.data[uid].username = newNickName
            return
        if winnerFlag is not None:
            self.data[uid].isWinner = winnerFlag
            return
        if bannedFlag is not None:
            self.data[uid].isBlocked = bannedFlag
            return
        with open(self.file_storage_path, "w") as f:
            json.dump(self.data, f, cls=EnhancedJSONEncoder, indent=4)

    def getTop(self, page = 0, caller=-1):
        filter_func = lambda user: not user.isBlocked and (user.username or user.uid == int(caller))
        filtered_data = filter(filter_func, self.data.values())
        sorted_data = sorted(filtered_data, key=lambda x: x.lastTimeFap)
        callerStat = None
        for i in range(len(sorted_data)):
            stat = sorted_data[i]
            if stat.uid == int(caller):
                callerStat = (i + 1, stat)
                break
        
        return sorted_data[page*10:(page+1)*10], callerStat

if __name__ == "__main__":
    testDB = NoFapDB()
    testDB.addNewUser(10, "timtim2379", datetime.now())
