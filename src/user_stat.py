from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserStat:
    uid: int
    username: str
    lastTimeFap: datetime
    collectedMemes: list