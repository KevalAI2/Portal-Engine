from app.core.database import Base, engine
from . import user
from . import schedule

Base.metadata.create_all(bind=engine)
