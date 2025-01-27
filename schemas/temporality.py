import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field, validator

from tools.dates import past_timestamp


class TempMappingModel(BaseModel):
    _now = dt.datetime.now()

    # Definición de la "t" temporalidades
    t_1w: Optional[int] = Field(
        default_factory=lambda: past_timestamp(
            400, "days", TempMappingModel._now.default
        )
    )
    t_1d: Optional[int] = Field(
        default_factory=lambda: past_timestamp(
            180, "days", TempMappingModel._now.default
        )
    )
    t_4h: Optional[int] = Field(
        default_factory=lambda: past_timestamp(
            30, "days", TempMappingModel._now.default
        )
    )
    t_1h: Optional[int] = Field(
        default_factory=lambda: past_timestamp(8, "days", TempMappingModel._now.default)
    )
    t_30m: Optional[int] = Field(
        default_factory=lambda: past_timestamp(4, "days", TempMappingModel._now.default)
    )
    t_15m: Optional[int] = Field(
        default_factory=lambda: past_timestamp(
            36, "hours", TempMappingModel._now.default
        )
    )
    t_5m: Optional[int] = Field(
        default_factory=lambda: past_timestamp(
            12, "hours", TempMappingModel._now.default
        )
    )

    @validator("*", pre=True)
    def validate_timestamps(cls, v):
        if v is not None and not isinstance(v, int):
            raise ValueError("El valor debe ser un entero.")
        return v

    def to_dict(self):
        return {
            "1w": self.t_1w,
            "1d": self.t_1d,
            "4h": self.t_4h,
            "1h": self.t_1h,
            "30m": self.t_30m,
            "15m": self.t_15m,
            "5m": self.t_5m,
        }
