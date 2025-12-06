"""Data models for trading data foundation.

Models represent database entities in memory with type safety.
All models map 1:1 with database tables.
"""

import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Transaction:
    """Transaction model - unified across all sources.

    Attributes:
        id: Unique identifier (UUID as string)
        source: Data source (e.g., 'robinhood', 'ibkr')
        source_id: Original ID from source
        type: Transaction type (e.g., 'stock', 'option', 'crypto', 'dividend', 'transfer')
        created_at: ISO timestamp string
        account_id: Account identifier (optional)
        raw_data: JSON blob of original data
    """

    id: str
    source: str
    source_id: str
    type: str
    created_at: str
    account_id: Optional[str]
    raw_data: str

    @classmethod
    def from_db_row(cls, row: tuple) -> "Transaction":
        """Create Transaction from database row.

        Args:
            row: Database row tuple in order:
                (id, source, source_id, type, created_at, account_id, raw_data)

        Returns:
            Transaction instance
        """
        return cls(
            id=row[0],
            source=row[1],
            source_id=row[2],
            type=row[3],
            created_at=row[4],
            account_id=row[5],
            raw_data=row[6],
        )

    def to_db_tuple(self) -> tuple:
        """Convert Transaction to database tuple.

        Returns:
            Tuple in order: (id, source, source_id, type, created_at, account_id, raw_data)
        """
        return (
            self.id,
            self.source,
            self.source_id,
            self.type,
            self.created_at,
            self.account_id,
            self.raw_data,
        )

    def get_raw_data_dict(self) -> dict[str, Any]:
        """Parse raw_data JSON string to dictionary.

        Returns:
            Parsed JSON data as dictionary
        """
        result: dict[str, Any] = json.loads(self.raw_data)
        return result


@dataclass
class OptionOrder:
    """Option order model.

    Attributes:
        id: Foreign key to transactions.id
        chain_symbol: Option chain symbol
        opening_strategy: Opening strategy (e.g., 'vertical_call_spread')
        closing_strategy: Closing strategy (optional)
        direction: Order direction ('debit' or 'credit')
        premium: Option premium
        net_amount: Net amount of the order
    """

    id: str
    chain_symbol: str
    opening_strategy: Optional[str]
    closing_strategy: Optional[str]
    direction: Optional[str]
    premium: Optional[float]
    net_amount: Optional[float]

    @classmethod
    def from_db_row(cls, row: tuple) -> "OptionOrder":
        """Create OptionOrder from database row.

        Args:
            row: Database row tuple in order:
                (id, chain_symbol, opening_strategy, closing_strategy,
                 direction, premium, net_amount)

        Returns:
            OptionOrder instance
        """
        return cls(
            id=row[0],
            chain_symbol=row[1],
            opening_strategy=row[2],
            closing_strategy=row[3],
            direction=row[4],
            premium=row[5],
            net_amount=row[6],
        )

    def to_db_tuple(self) -> tuple:
        """Convert OptionOrder to database tuple.

        Returns:
            Tuple in order:
                (id, chain_symbol, opening_strategy, closing_strategy,
                 direction, premium, net_amount)
        """
        return (
            self.id,
            self.chain_symbol,
            self.opening_strategy,
            self.closing_strategy,
            self.direction,
            self.premium,
            self.net_amount,
        )


@dataclass
class OptionLeg:
    """Option leg model.

    Attributes:
        id: Unique identifier (UUID as string)
        order_id: Foreign key to option_orders.id
        strike_price: Strike price
        expiration_date: Expiration date (ISO format string)
        option_type: Option type ('call' or 'put')
        side: Side ('buy' or 'sell')
        position_effect: Position effect ('open' or 'close')
        ratio_quantity: Ratio quantity (integer)
    """

    id: str
    order_id: str
    strike_price: float
    expiration_date: str
    option_type: str
    side: str
    position_effect: str
    ratio_quantity: int

    @classmethod
    def from_db_row(cls, row: tuple) -> "OptionLeg":
        """Create OptionLeg from database row.

        Args:
            row: Database row tuple in order:
                (id, order_id, strike_price, expiration_date, option_type,
                 side, position_effect, ratio_quantity)

        Returns:
            OptionLeg instance
        """
        return cls(
            id=row[0],
            order_id=row[1],
            strike_price=row[2],
            expiration_date=row[3],
            option_type=row[4],
            side=row[5],
            position_effect=row[6],
            ratio_quantity=row[7],
        )

    def to_db_tuple(self) -> tuple:
        """Convert OptionLeg to database tuple.

        Returns:
            Tuple in order:
                (id, order_id, strike_price, expiration_date, option_type,
                 side, position_effect, ratio_quantity)
        """
        return (
            self.id,
            self.order_id,
            self.strike_price,
            self.expiration_date,
            self.option_type,
            self.side,
            self.position_effect,
            self.ratio_quantity,
        )


@dataclass
class Execution:
    """Execution model.

    Attributes:
        id: Unique identifier (UUID as string)
        order_id: Foreign key to transactions.id
        leg_id: Foreign key to option_legs.id (optional, nullable)
        price: Execution price
        quantity: Execution quantity
        timestamp: Execution timestamp (ISO format string)
        settlement_date: Settlement date (ISO format string, optional)
    """

    id: str
    order_id: str
    leg_id: Optional[str]
    price: float
    quantity: float
    timestamp: str
    settlement_date: Optional[str]

    @classmethod
    def from_db_row(cls, row: tuple) -> "Execution":
        """Create Execution from database row.

        Args:
            row: Database row tuple in order:
                (id, order_id, leg_id, price, quantity, timestamp, settlement_date)

        Returns:
            Execution instance
        """
        return cls(
            id=row[0],
            order_id=row[1],
            leg_id=row[2],
            price=row[3],
            quantity=row[4],
            timestamp=row[5],
            settlement_date=row[6],
        )

    def to_db_tuple(self) -> tuple:
        """Convert Execution to database tuple.

        Returns:
            Tuple in order: (id, order_id, leg_id, price, quantity, timestamp, settlement_date)
        """
        return (
            self.id,
            self.order_id,
            self.leg_id,
            self.price,
            self.quantity,
            self.timestamp,
            self.settlement_date,
        )


@dataclass
class StockOrder:
    """Stock order model.

    Attributes:
        id: Foreign key to transactions.id
        symbol: Stock symbol
        side: Order side ('buy' or 'sell')
        quantity: Order quantity
        price: Order price (optional)
        average_price: Average execution price (optional)
    """

    id: str
    symbol: str
    side: str
    quantity: float
    price: Optional[float]
    average_price: Optional[float]

    @classmethod
    def from_db_row(cls, row: tuple) -> "StockOrder":
        """Create StockOrder from database row.

        Args:
            row: Database row tuple in order: (id, symbol, side, quantity, price, average_price)

        Returns:
            StockOrder instance
        """
        return cls(
            id=row[0],
            symbol=row[1],
            side=row[2],
            quantity=row[3],
            price=row[4],
            average_price=row[5],
        )

    def to_db_tuple(self) -> tuple:
        """Convert StockOrder to database tuple.

        Returns:
            Tuple in order: (id, symbol, side, quantity, price, average_price)
        """
        return (
            self.id,
            self.symbol,
            self.side,
            self.quantity,
            self.price,
            self.average_price,
        )


@dataclass
class Position:
    """Position model.

    Attributes:
        id: Unique identifier (UUID as string)
        source: Data source (e.g., 'robinhood', 'ibkr')
        account_id: Account identifier (URL/last4) if available
        symbol: Symbol or option identifier
        quantity: Position quantity
        cost_basis: Cost basis (optional)
        current_price: Current price (cached, optional)
        unrealized_pnl: Unrealized P&L (optional)
        last_updated: Last update timestamp (ISO format string)
    """

    id: str
    source: str
    account_id: Optional[str]
    symbol: str
    quantity: float
    cost_basis: Optional[float]
    current_price: Optional[float]
    unrealized_pnl: Optional[float]
    last_updated: str

    @classmethod
    def from_db_row(cls, row: tuple) -> "Position":
        """Create Position from database row.

        Args:
            row: Database row tuple in order:
                (id, source, account_id, symbol, quantity, cost_basis, current_price,
                 unrealized_pnl, last_updated)

        Returns:
            Position instance
        """
        return cls(
            id=row[0],
            source=row[1],
            account_id=row[2],
            symbol=row[3],
            quantity=row[4],
            cost_basis=row[5],
            current_price=row[6],
            unrealized_pnl=row[7],
            last_updated=row[8],
        )

    def to_db_tuple(self) -> tuple:
        """Convert Position to database tuple.

        Returns:
            Tuple in order:
                (id, source, account_id, symbol, quantity, cost_basis, current_price,
                 unrealized_pnl, last_updated)
        """
        return (
            self.id,
            self.source,
            self.account_id,
            self.symbol,
            self.quantity,
            self.cost_basis,
            self.current_price,
            self.unrealized_pnl,
            self.last_updated,
        )


@dataclass
class TransactionLink:
    """Transaction link model.

    Attributes:
        id: Unique identifier (UUID as string)
        opening_transaction_id: Foreign key to transactions.id (opening)
        closing_transaction_id: Foreign key to transactions.id (closing)
        link_type: Link type (e.g., 'spread', 'covered_call')
        created_at: When link was established (ISO format string)
    """

    id: str
    opening_transaction_id: str
    closing_transaction_id: str
    link_type: Optional[str]
    created_at: str

    @classmethod
    def from_db_row(cls, row: tuple) -> "TransactionLink":
        """Create TransactionLink from database row.

        Args:
            row: Database row tuple in order:
                (id, opening_transaction_id, closing_transaction_id, link_type, created_at)

        Returns:
            TransactionLink instance
        """
        return cls(
            id=row[0],
            opening_transaction_id=row[1],
            closing_transaction_id=row[2],
            link_type=row[3],
            created_at=row[4],
        )

    def to_db_tuple(self) -> tuple:
        """Convert TransactionLink to database tuple.

        Returns:
            Tuple in order:
                (id, opening_transaction_id, closing_transaction_id, link_type, created_at)
        """
        return (
            self.id,
            self.opening_transaction_id,
            self.closing_transaction_id,
            self.link_type,
            self.created_at,
        )
