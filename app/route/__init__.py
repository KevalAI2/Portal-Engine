from app.core.app import app
from app.const.route import DS
from . import auth
from . import user
from . import scheduler
from . import content
from . import user_profile
from . import lis

app.include_router(auth.router, prefix=f"{DS}/auth", tags=["auth"])
app.include_router(user.router, prefix=f"{DS}/user", tags=["user"])
app.include_router(scheduler.router, prefix=f"{DS}/scheduler", tags=["scheduler"])
app.include_router(content.router, prefix=f"{DS}/content", tags=["content"])
app.include_router(user_profile.router, prefix=f"{DS}/user-profile", tags=["user-profiles"])
app.include_router(lis.router, prefix=f"{DS}/lis", tags=["lis"])
