from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel


class TradeParams(BaseModel):
    atr: float
    real_price: Optional[float] = None
    market_spread: Optional[float] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.market_spread = self.market_spread or 0.09 * self.atr


class TargetResults(BaseModel):
    market: Dict[str, List[Tuple[float, ...]]]
    limit: Dict[str, List[Tuple[float, ...]]]

    @classmethod
    def calculate(cls, df, real_price: Optional[float] = None, precision: int = 2):
        atr = df["atr"].iloc[-1]
        close_price = df["close"].iloc[-1]
        params = TradeParams(atr=atr, real_price=real_price or close_price)

        return cls(
            market={
                "long": cls._calculate_market_long(params, precision),
                "short": cls._calculate_market_short(params, precision),
            },
            limit={
                "long": cls._calculate_limit_long(params, precision),
                "short": cls._calculate_limit_short(params, precision),
            },
        )

    @staticmethod
    def _calculate_market_long(
        params: TradeParams, precision: int
    ) -> List[Tuple[float, ...]]:
        entry_1 = params.real_price - params.market_spread
        sl_1 = params.real_price - 2.22 * params.atr
        tp_1 = entry_1 + 0.8 * (entry_1 - sl_1)
        tp_2 = params.real_price + 2 * params.atr
        return [
            (round(sl_1, precision),),  # Stop-loss
            (round(entry_1, precision),),  # Entry
            (
                round(tp_1, precision),
                round(tp_2, precision),
            ),  # Take-profit
        ]

    @staticmethod
    def _calculate_market_short(
        params: TradeParams, precision: int
    ) -> List[Tuple[float, ...]]:
        entry_1 = params.real_price + params.market_spread
        sl_1 = params.real_price + 2.22 * params.atr
        tp_1 = entry_1 - 0.8 * (sl_1 - entry_1)
        tp_2 = params.real_price - 2 * params.atr
        return [
            (round(sl_1, precision),),  # Stop-loss
            (round(entry_1, precision),),  # Entry
            (
                round(tp_1, precision),
                round(tp_2, precision),
            ),  # Take-profit
        ]

    @staticmethod
    def _calculate_limit_long(
        params: TradeParams, precision: int
    ) -> List[Tuple[float, ...]]:
        entry_1 = params.real_price - 0.25 * params.atr
        entry_2 = params.real_price - params.atr
        sl_1 = params.real_price - 2.5 * params.atr
        sl_2 = params.real_price - 3.5 * params.atr
        tp_1_1 = entry_1 + 0.8 * (entry_1 - sl_1)
        tp_1_2 = entry_1 + 1.16 * (entry_1 - sl_1)
        tp_1_3 = entry_1 + 2 * (entry_1 - sl_1)
        tp_2_3 = entry_2 + 5 * params.atr

        return [
            (
                round(sl_1, precision),
                round(sl_2, precision),
            ),  # Stop-loss
            (
                round(entry_1, precision),
                round(entry_2, precision),
            ),  # Entry
            (
                round(tp_1_1, precision),
                round(tp_1_2, precision),
                round(tp_1_3, precision),
                round(tp_1_1, precision),
                round(tp_1_2, precision),
                round(tp_2_3, precision),
            ),  # Take-profit
        ]

    @staticmethod
    def _calculate_limit_short(
        params: TradeParams, precision: int
    ) -> List[Tuple[float, ...]]:
        entry_1 = params.real_price + 0.25 * params.atr
        entry_2 = params.real_price + params.atr
        sl_1 = params.real_price + 2.5 * params.atr
        sl_2 = params.real_price + 3.5 * params.atr
        tp_1_1 = entry_1 - 0.8 * (sl_1 - entry_1)
        tp_1_2 = entry_1 - 1.16 * (sl_1 - entry_1)
        tp_1_3 = entry_1 - 2 * (sl_1 - entry_1)
        tp_2_3 = entry_2 - 5 * params.atr
        return [
            (
                round(sl_1, precision),
                round(sl_2, precision),
            ),  # Stop-loss
            (
                round(entry_1, precision),
                round(entry_2, precision),
            ),  # Entry
            (
                round(tp_1_1, precision),
                round(tp_1_2, precision),
                round(tp_1_3, precision),
                round(tp_1_1, precision),
                round(tp_1_2, precision),
                round(tp_2_3, precision),
            ),  # Take-profit
        ]
