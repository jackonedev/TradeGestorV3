import os

import numpy as np

from tools.plots import (
    add_signals,
    create_bar,
    create_bar_figure,
    create_candlestick,
    create_price_figure,
    create_scatter,
    create_SQZMOM_bar,
    download_html,
    make_3r_subplots,
)


def load_3r_plots(df, activo, temporalidad, path):
    # Figure 1
    candlestick = create_candlestick(df)
    upper_band = create_scatter(df, "upper_BB", "upper_BB", "red")
    lower_band = create_scatter(df, "lower_BB", "lower_BB", "red")
    upper_KC = create_scatter(df, "upper_KC", "upper_KC", "blue")
    lower_KC = create_scatter(df, "lower_KC", "lower_KC", "blue")
    WMA_12 = create_scatter(df, "WMA_12", "WMA_12", "yellow")
    DEMA_12 = create_scatter(df, "DEMA_12", "DEMA_12", "yellow")
    TEMA_12 = create_scatter(
        df,
        "TEMA_12",
        "TEMA_12",
        "yellow",
        hover=True,
    )
    EMA_55 = create_scatter(df, "EMA_55", "EMA_55", "brown", hover=True)
    TRIMA_L_55 = create_scatter(df, "TRIMA_L_55", "TRIMA_L_55", "brown")
    objects1 = [
        candlestick,
        upper_band,
        lower_band,
        upper_KC,
        lower_KC,
        WMA_12,
        DEMA_12,
        TEMA_12,
        EMA_55,
        TRIMA_L_55,
    ]
    fig1 = create_price_figure(
        data=df,
        graph_objects=objects1,
        title=f"{activo} {temporalidad}",
    )
    fig1.update_yaxes(autorange=False)

    # Figure 2
    volume = create_bar(df, "volume", "Volume", "blue", hover=True)
    objects2 = [volume]
    fig2 = create_bar_figure(
        data=df,
        graph_objects=objects2,
        title=f"{activo} {temporalidad}",
    )
    fig2.update_yaxes(autorange=False)

    # Figure 3
    sqzm_bar = create_SQZMOM_bar(df, normalize=True)
    adx_line = create_scatter(df - 50, "adx", "ADX", "black", hover=True)
    plus_di = create_scatter(
        df - 50,
        "plus_di",
        "plus_DI",
        "green",
        hover=True,
    )
    minus_di = create_scatter(
        df - 50,
        "minus_di",
        "minus_DI",
        "red",
        hover=True,
    )
    # Definicion de señal de squeeze
    df["squeeze_on"] = np.where(df["squeeze_on"] == 1, 0, None)
    sqz_signal = create_scatter(
        df,
        "squeeze_on",
        "SQZ Signal",
        "blue",
        hover=True,
    )
    # Definicion del cruce de DIs
    df["cross_di_up"] = np.where(
        (df["plus_di"] > df["minus_di"])
        & (df["plus_di"].shift(1) < df["minus_di"].shift(1)),
        1,
        None,
    )
    df["cross_di_down"] = np.where(
        (df["plus_di"] < df["minus_di"])
        & (df["plus_di"].shift(1) > df["minus_di"].shift(1)),
        1,
        None,
    )
    cruce_up = add_signals(df["cross_di_up"], "green")
    cruce_down = add_signals(df["cross_di_down"], "red")
    objects3 = (
        [sqzm_bar, adx_line, plus_di, minus_di, sqz_signal] + cruce_up + cruce_down
    )
    fig3 = create_bar_figure(data=df, graph_objects=objects3)
    fig3.update_yaxes(autorange=False)

    # Subplot
    last_atr = df["atr"].iloc[-1]
    plot_name = f"{activo}_{temporalidad} - [ATR] = {last_atr}"
    subplot_fig = make_3r_subplots([fig1, fig2, fig3], title=plot_name)

    filename = f"{plot_name.split('-')[0].strip()}.html"
    download_html(
        subplot_fig,
        os.path.join(path, os.path.join(path, filename)),
    )
