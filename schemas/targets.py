from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel


class TradeParams(BaseModel):
    atr: float
    real_price: Optional[float] = None
    market_spread: Optional[float] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.market_spread = self.market_spread or 0.01 * self.atr


class TargetResults(BaseModel):
    market: Dict[str, List[Tuple[float, ...]]]
    limit: Dict[str, List[Tuple[float, ...]]]

    @classmethod
    def calculate(cls, df, real_price: Optional[float] = None):
        atr = df["atr"].iloc[-1]
        close_price = df["close"].iloc[-1]
        params = TradeParams(atr=atr, real_price=real_price or close_price)

        return cls(
            market={
                "long": cls._calculate_market_long(params),
                "short": cls._calculate_market_short(params),
            },
            limit={
                "long": cls._calculate_limit_long(params),
                "short": cls._calculate_limit_short(params),
            },
        )

    @staticmethod
    def _calculate_market_long(params: TradeParams) -> List[Tuple[float, ...]]:
        return [
            (params.real_price - 0.9 * params.atr,),  # Stop-loss
            (params.real_price - params.market_spread,),  # Entry
            (
                params.real_price + 0.3 * params.atr,
                params.real_price + params.atr,
            ),  # Take-profit
        ]

    @staticmethod
    def _calculate_market_short(params: TradeParams) -> List[Tuple[float, ...]]:
        return [
            (params.real_price + 0.9 * params.atr,),  # Stop-loss
            (params.real_price + params.market_spread,),  # Entry
            (
                params.real_price - 0.3 * params.atr,
                params.real_price - params.atr,
            ),  # Take-profit
        ]

    @staticmethod
    def _calculate_limit_long(params: TradeParams) -> List[Tuple[float, ...]]:
        return [
            (
                params.real_price - 2.5 * params.atr,
                params.real_price - 3.5 * params.atr,
            ),  # Stop-loss
            (
                entry_1 := params.real_price - 0.25 * params.atr,
                entry_2 := params.real_price - params.atr,
            ),  # Entry
            (
                entry_1 + 0.3 * params.atr,
                entry_1 + params.atr,
                entry_1 + 5 * params.atr,
                entry_2 + 0.3 * params.atr,
                entry_2 + params.atr,
                entry_2 + 5 * params.atr,
            ),  # Take-profit
        ]

    @staticmethod
    def _calculate_limit_short(params: TradeParams) -> List[Tuple[float, ...]]:
        return [
            (
                params.real_price + 2.5 * params.atr,
                params.real_price + 3.5 * params.atr,
            ),  # Stop-loss
            (
                entry_1 := params.real_price + 0.25 * params.atr,
                entry_2 := params.real_price + params.atr,
            ),  # Entry
            (
                entry_1 - 0.3 * params.atr,
                entry_1 - params.atr,
                entry_1 - 5 * params.atr,
                entry_2 - 0.3 * params.atr,
                entry_2 - params.atr,
                entry_2 - 5 * params.atr,
            ),  # Take-profit
        ]
