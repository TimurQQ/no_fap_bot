import json
from typing import Callable

from logger import noFapLogger


class UserState:
    def __init__(self):
        pass

    def state_action(self, pong_flag=False):
        pass

    def __repr__(self):
        return f"{type(self).__name__} {json.dumps(self.__dict__)}"

    def _logInfo(self, context):
        noFapLogger.info(f"User {context.uid} in state: {self}")


class PingUserState(UserState):
    def __init__(self, default_count: int = 0, max_count: int = 3):
        self.count_pings = default_count
        self.max_count = max_count

    def ping(self, context):
        if self.count_pings >= self.max_count:
            context.change_state(RefreshUserState())
        self.count_pings += 1

    def pong(self):
        self.count_pings = 0  # Полный сброс при любом ответе

    def state_action(self, context, pong_flag=False):
        self._logInfo(context)
        if not pong_flag:
            self.ping(context)
        else:
            self.pong()


class UserContext:
    def __init__(self, uid, default_state=PingUserState()):
        self.uid = uid
        self.state = default_state
        self.refresh_callback = None

    def change_state(self, state: UserState):
        self.state = state

    def daily_check(self):
        noFapLogger.info(
            f"Daily check for {self.uid} user. ({self.state=}), pong_flag=False"
        )
        self.state.state_action(self)

    def getting_response(self):
        noFapLogger.info(
            f"Gettting response for {self.uid} user. ({self.state=}), pong_flag=True"
        )
        self.state.state_action(self, pong_flag=True)

    def addRefreshCallback(self, callback: Callable):
        self.refresh_callback = callback

    def refresh(self):
        self.refresh_callback(self.uid)

    def __repr__(self):
        return f"{type(self).__name__} {json.dumps(self.__dict__)}"


class RefreshUserState(UserState):
    def __init__(self):
        pass

    def state_action(self, context, pong_flag=False):
        self._logInfo(context)
        if pong_flag == False:
            context.refresh()
        context.change_state(PingUserState())
