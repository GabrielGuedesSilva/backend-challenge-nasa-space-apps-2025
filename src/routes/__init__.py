from re import I

from src.routes.asteroids import AsteroidRouter
from src.routes.impact import ImpactRouter as ImpactRouter
from src.routes.users import UserRouter

routers_class = [UserRouter, AsteroidRouter, ImpactRouter]
