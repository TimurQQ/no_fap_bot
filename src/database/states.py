from src.logger import noFapLogger
import json

class UserState:
    def __init__(self):
        pass

    def state_action(self, pong_flag = False):
        pass

    def __repr__(self):
        return f"{type(self.__name__)}"

    def _logInfo(self, uid, pong_flag = False):
        noFapLogger.info(f"User {uid} in state: {self}")

class PingUserState(UserState):
    def __init__(self, default_count = 0, max_count = 3):
        self.count_pings = default_count
        self.max_count = max_count

    def ping(self, context):
        if (self.count_pings >= self.max_count):
            context.change_state(RefreshUserState())
        self.count_pings += 1

    def pong(self):
        self.count_pings = max(0, self.count_pings - 1)

    def state_action(self, context, pong_flag = False):
        super()._logInfo(context.uid, pong_flag)
        if (not pong_flag):
            self.ping(context)
        else:
            self.pong()

    def __repr__(self):
        return f"{type(self).__name__} {json.dumps(self.__dict__)}"

class UserContext:
    def __init__(self, uid, default_state=PingUserState()):
        self.uid = uid
        self.state = default_state
        self.refresh_callback = None

    def change_state(self, state: UserState):
        self.state = state

    def daily_check(self):
        noFapLogger.info(f"Daily check for {self.uid} user. ({self.state=}), pong_flag=False")
        self.state.state_action(self)
    
    def getting_response(self):
        noFapLogger.info(f"Gettting response for {self.uid} user. ({self.state=}), pong_flag=True")
        self.state.state_action(self, pong_flag=True)

    def addRefreshCallback(self, callback):
        self.refresh_callback = callback
    
    def refresh(self):
        self.refresh_callback(self.uid)

    def __repr__(self):
        return f"{type(self).__name__} {json.dumps(self.__dict__)}"


class RefreshUserState(UserState):
    def __init__(self):
        pass

    def state_action(self, context, pong_flag = False):
        noFapLogger.info(f"State action for {context.uid} user. {self.state=},"
                     f"{self=}")
        if (pong_flag):
            context.change_state(PingUserState())
        else:
            context.refresh()
