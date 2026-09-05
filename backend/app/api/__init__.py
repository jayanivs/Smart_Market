from fastapi import APIRouter
from .auth import router as auth_router
from .simulator import router as sim_router
from .stocks import router as stock_router
from .watchlists import router as watchlist_router
from .pulse import router as pulse_router
from .missed import router as missed_router
from .smart_watch import router as smart_watch_router
from .market import router as market_router
from .notifications import router as notifications_router
from .quick_groups import router as quick_groups_router
from .reports import router as reports_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(sim_router, prefix="/simulator", tags=["simulator"])
api_router.include_router(stock_router, prefix="/stocks", tags=["stocks"])
api_router.include_router(watchlist_router, prefix="/watchlists", tags=["watchlists"])
api_router.include_router(pulse_router, prefix="/pulse", tags=["pulse"])
api_router.include_router(missed_router, prefix="/what-you-missed", tags=["what-you-missed"])
api_router.include_router(smart_watch_router, prefix="/smart-watch", tags=["smart-watch"])
api_router.include_router(market_router, prefix="/market", tags=["market"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(quick_groups_router, prefix="/quick-groups", tags=["quick-groups"])
api_router.include_router(reports_router, prefix="/reports/weekly", tags=["reports"])

