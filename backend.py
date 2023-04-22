import datetime as dt
import sqlite3
from typing import Any
import requests
import prettytable
import matplotlib.pyplot as plt
import numpy as np


class backend:
    """
    homeCurrency can be: "INR", "EUR", "GBP" or "USD"
    numOfTokensToBuy is the number of tokens you are willing to buy with the total budget of moneyToBuyTokens
    numOfTokensToBuy should never be 0 otherwise it will lead to ZeroDivisionError
    """
    def __init__(self, homeCurrency: str, numOfTokensToBuy: int, moneyToBuyTokens: float) -> None:
        self.homeCurrency: str = homeCurrency
        self.numOfTokensToBuy: int = numOfTokensToBuy
        self.moneyToBuyTokens: float = moneyToBuyTokens

    def fetchRates(self, date: str = "latest") -> dict[str, str | float]:  # BY DEFAULT IT FETCHES THE LATEST RATES, ARG CAN OVERRIDE THIS BEHAVIOUR
        url: str = f"https://api.exchangerate.host/{date}"

        # GET FIAT CURRENCY EXCHANGE RATES
        response: requests.Response = requests.get(url, params={"base": "USD", "symbols": "INR,EUR,GBP", "places": 4}, timeout=10)
        data: Any = response.json()  # TRANSFORM RESPONSE OBJ INTO JSON OBJ
        rates: dict[str, float] = data["rates"]  # EXTRACT RATES DICT FROM JSON OBJ
        # CREATE DICT WITH TIMESTAMPS + FIAT CURRENCY RATES
        entry: dict[str, str | float] = {
            "time": data["date"],
            "INR": rates["INR"],
            "EUR": rates["EUR"],
            "GBP": rates["GBP"],
        }

        # GET CRYPTO CURRENCY EXCHANGE RATES
        response = requests.get(
            url,
            params={"base": "USD", "source": "crypto", "symbols": "DOGE"},
            timeout=10,
        )
        data = response.json()  # TRANSFORM RESPONSE OBJ INTO JSON OBJ
        rates = data["rates"]  # EXTRACT RATES DICT FROM JSON OBJ
        # APPEND THE RATE TO ENTRY DICT
        entry["DOGE"] = rates["DOGE"]

        return entry  # {TIMESTAMP, FIAT RATE, CRYPTO RATE}
        # SAMPLE {'time': '2023-04-22', 'INR': 81.9716, 'EUR': 0.9008, 'GBP': 0.8039, 'DOGE': 0.064192}

    def compareTarget(self, rates: dict[str, str | float]) -> bool:  # RETURNS TRUE IF CURRENT CRYPTO RATE >= TARGET
        if self.homeCurrency != "USD" and self.moneyToBuyTokens / (rates[self.homeCurrency] * self.numOfTokensToBuy) >= rates["DOGE"]:
            return True
        if self.moneyToBuyTokens / self.numOfTokensToBuy >= rates["DOGE"]:
            return True
        return False

    def ratesThisWeek(self) -> list[dict[str, str | float]]:
        today: dt.date = dt.date.today()
        ratesThisWeekAsListOfDicts: list[dict[str, str | float]] = list(dict())
        cachedRatesdb: sqlite3.Connection = sqlite3.connect("cachedRates.db")
        cursor: sqlite3.Cursor = cachedRatesdb.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS cache (
                timestamp text,
                INR real,
                EUR real,
                GBP real,
                DOGE real
            )"""
        )

        cursor.execute("SELECT timestamp FROM cache")
        timestamps: list[str] = [row[0] for row in cursor.fetchall()]

        for i in range(7, -1, -1):
            date = str(today - dt.timedelta(days=i))
            if date not in timestamps:  # IF THE TIMESTAMP CACHED IN DB, DONT FETCH IT AGAIN
                ratesThisWeekAsListOfDicts.append(self.fetchRates(date))

        cachedRatesdb.commit()
        cachedRatesdb.close()

        return ratesThisWeekAsListOfDicts

    def dbHandler(self) -> None:
        cachedRatesdb: sqlite3.Connection = sqlite3.connect("cachedRates.db")
        weekRates: list[dict[str, str | float]] = self.ratesThisWeek()
        cursor: sqlite3.Cursor = cachedRatesdb.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS cache (
                timestamp text,
                INR real,
                EUR real,
                GBP real,
                DOGE real
            )"""
        )
        for dc in weekRates:
            cursor.execute(
                f"INSERT INTO cache VALUES ('{dc['time']}', {dc['INR']}, {dc['EUR']}, {dc['GBP']}, {dc['DOGE']})"
            )
        # cursor.execute("SELECT * FROM cache")
        # print(cursor.fetchall())

        cachedRatesdb.commit()
        cachedRatesdb.close()

    def printDB(self) -> None:
        cachedRatesdb: sqlite3.Connection = sqlite3.connect("cachedRates.db")
        cursor: sqlite3.Cursor = cachedRatesdb.cursor()
        cursor.execute('SELECT * FROM cache')
        table: prettytable.PrettyTable | None = prettytable.from_db_cursor(cursor)
        print(table)

    def plot(self) -> None:
        cachedRatesdb: sqlite3.Connection = sqlite3.connect("cachedRates.db")
        cursor: sqlite3.Cursor = cachedRatesdb.cursor()
        cursor.execute("SELECT timestamp, DOGE FROM cache")
        result: list[tuple[str, float]] = cursor.fetchall()
        timestamps = np.array([result[0] for result in result])
        doge = np.array([result[1] for result in result])
        cachedRatesdb.close()
        plt.plot(timestamps, doge)
        plt.title("Historical Exchange Rate Of DOGE in USD")
        plt.xlabel('Timestamps (in days)')
        plt.ylabel('DOGE\'s exchange rate (in USD)')
        plt.show()


if __name__ == "__main__":
    instance = backend("INR", 600, 8100)
    rate: dict[str, str | float] = backend.fetchRates(self=instance)
    # backend.compareTarget(self=instance, rates=rate)
    backend.dbHandler(self=instance)
    backend.printDB(self=instance)
    backend.plot(self=instance)
