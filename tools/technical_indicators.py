import numpy as np


def true_range_(df):
    data = df.copy()
    data["tr0"] = abs(df["high"] - df["low"])
    data["tr1"] = abs(df["high"] - df["close"].shift())
    data["tr2"] = abs(df["low"] - df["close"].shift())
    return data[["tr0", "tr1", "tr2"]].max(axis=1)


def avg_true_range(df, n=14, use_EMA=True):
    data = df.copy()
    tr = true_range_(df)
    if use_EMA:
        data["atr"] = tr.ewm(span=n, adjust=False).mean()
    else:
        data["atr"] = tr.rolling(window=n).mean()
    return data


def squeeze_momentum_indicator(
    df, length=20, mult=2, length_KC=20, mult_KC=1.5, n_atr=10, use_EMA=True
):
    data = df.copy()
    # calculate BB
    m_avg = data["close"].rolling(window=length).mean()
    m_std = data["close"].rolling(window=length).std(ddof=0)
    data["upper_BB"] = m_avg + mult * m_std
    data["lower_BB"] = m_avg - mult * m_std

    # calculate true range
    data["tr"] = true_range_(data)

    # calculate KC
    if use_EMA:
        atr = data["tr"].ewm(span=n_atr, adjust=False).mean()
    else:
        atr = data["tr"].rolling(window=n_atr).mean()
    data["upper_KC"] = m_avg + atr * mult_KC
    data["lower_KC"] = m_avg - atr * mult_KC

    # calculate bar value
    highest = data["high"].rolling(window=length_KC).max()
    lowest = data["low"].rolling(window=length_KC).min()
    m1 = (highest + lowest) / 2
    data["SQZMOM_value"] = data["close"] - (m1 + m_avg) / 2
    fit_y = np.array(range(0, length_KC))
    data["SQZMOM_value"] = (
        data["SQZMOM_value"]
        .rolling(window=length_KC)
        .apply(
            lambda x: np.polyfit(fit_y, x, 1)[0] * (length_KC - 1)
            + np.polyfit(fit_y, x, 1)[1],
            raw=True,
        )
    )

    # check for 'squeeze'
    def in_squeeze(data):
        return (
            data["lower_BB"] > data["lower_KC"] and data["upper_BB"] < data["upper_KC"]
        )

    data["squeeze_on"] = data.apply(in_squeeze, axis=1)

    return data


def moving_averages(df, price="close", n=55):
    data = df.copy()
    data[f"SMA_{n}"] = data[price].rolling(n).mean()

    def wma(serie):
        n = len(serie)
        f = [i / sum(range(n + 1)) for i in range(1, n + 1)]
        return np.array(serie).dot(f)

    data[f"EMA_{n}"] = data[price].ewm(span=n).mean()
    data[f"WMA_{n}"] = data[price].rolling(n).apply(wma)
    data[f"DEMA_{n}"] = data[f"EMA_{n}"] * 2 - data[f"EMA_{n}"].ewm(span=n).mean()
    data[f"TRIMA_L_{n}"] = data[f"SMA_{n}"].rolling(n).mean()
    data[f"TRIMA_E_{n}"] = data[f"EMA_{n}"].ewm(span=n).mean()
    data[f"TEMA_{n}"] = (
        data[f"EMA_{n}"] * 3
        - data[f"TRIMA_E_{n}"] * 3
        + data[f"TRIMA_E_{n}"].ewm(span=n).mean()
    )

    data.drop(columns=f"TRIMA_E_{n}", inplace=True)
    return data
