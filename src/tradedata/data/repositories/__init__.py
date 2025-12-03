"""Repository pattern for data access.

Repositories abstract database operations from business logic,
providing clean, typed APIs for CRUD operations.
"""

from tradedata.data.repositories.base import BaseRepository
from tradedata.data.repositories.execution import ExecutionRepository
from tradedata.data.repositories.option_leg import OptionLegRepository
from tradedata.data.repositories.option_order import OptionOrderRepository
from tradedata.data.repositories.position import PositionRepository
from tradedata.data.repositories.stock_order import StockOrderRepository
from tradedata.data.repositories.transaction import TransactionRepository
from tradedata.data.repositories.transaction_link import TransactionLinkRepository

__all__ = [
    "BaseRepository",
    "ExecutionRepository",
    "OptionLegRepository",
    "OptionOrderRepository",
    "PositionRepository",
    "StockOrderRepository",
    "TransactionRepository",
    "TransactionLinkRepository",
]
