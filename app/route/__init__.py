from app.core.app import app
from app.const.route import DS
from . import auth
from . import user
from . import scheduler

app.include_router(auth.router, prefix=f"{DS}/auth", tags=["auth"])
app.include_router(user.router, prefix=f"{DS}/user", tags=["user"])
app.include_router(scheduler.router, prefix=f"{DS}/scheduler", tags=["scheduler"])
