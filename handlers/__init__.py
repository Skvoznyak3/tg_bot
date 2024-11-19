from aiogram import Router
from .asset_handlers import router as asset_router
from .chart_handlers import router as chart_router
from .favorite_handlers import router as favorite_router
from .main_menu import router as main_router
from .subscription_handlers import router as subscription_router

# Создаем общий роутер
router = Router()

# Включаем роутеры из разных файлов
router.include_router(asset_router)
router.include_router(chart_router)
router.include_router(favorite_router)
router.include_router(main_router)
router.include_router(subscription_router)
