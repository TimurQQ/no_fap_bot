import dataclasses
import json
import datetime
from datetime import date

class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if dataclasses.is_dataclass(obj):
                return dataclasses.asdict(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, date):
                return obj.isoformat()
            return super().default(obj)
