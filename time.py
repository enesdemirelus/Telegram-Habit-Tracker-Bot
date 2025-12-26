from datetime import datetime, date
from zoneinfo import ZoneInfo


now = datetime.now(ZoneInfo("America/Chicago"))
now_hour = (now.strftime("%H:%M"))

if now_hour == "09:00":
    print("yehu!!")
