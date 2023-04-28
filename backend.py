import datetime as dt
import sqlite3
import requests
import prettytable
import matplotlib.pyplot as plt
import numpy as np


class backend:
    def __init__(self, homeCurrency: str, numOfDOGEToBuy: float, moneyToBuyDOGE: float, numOfLTCToBuy: float, moneyToBuyLTC: float) -> None:
        self.homeCurrency: str = homeCurrency
        self.numOfDOGEToBuy: float = numOfDOGEToBuy
        self.moneyToBuyDOGE: float = moneyToBuyDOGE
        self.numOfLTCToBuy: float = numOfLTCToBuy
        self.moneyToBuyLTC: float = moneyToBuyLTC
        print(f"constructed backend object with {homeCurrency}, {numOfDOGEToBuy}, {moneyToBuyDOGE}, {numOfLTCToBuy}, {moneyToBuyLTC}\n")

    def fetchRates(self, date: str = "latest") -> dict[str, str | float]:
        url: str = f"https://api.exchangerate.host/{date}"

        response: requests.Response = requests.get(url, params={"base": "USD", "symbols": "INR,EUR,GBP", "places": 4}, timeout=10)
        data: dict = response.json()
        rates: dict[str, float] = data["rates"]
        entry: dict[str, str | float] = {
            "time": data["date"],
            "INR": rates["INR"],
            "EUR": rates["EUR"],
            "GBP": rates["GBP"],
        }

        response = requests.get(url, params={"base": "USD", "source": "crypto", "symbols": "DOGE,LTC"}, timeout=10)
        data = response.json()
        rates = data["rates"]
        entry["DOGE"] = rates["DOGE"]
        entry["LTC"] = rates["LTC"]

        print(f"\nGET: {url}: {entry}\n")
        return entry

    def connect2cache(self) -> tuple[sqlite3.Cursor, sqlite3.Connection]:
        cachedRatesdb: sqlite3.Connection = sqlite3.connect("cachedRates.db")
        cursor: sqlite3.Cursor = cachedRatesdb.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS cache (
                timestamp text,
                INR real,
                EUR real,
                GBP real,
                DOGE real,
                LTC real
            )"""
        )
        return cursor, cachedRatesdb

    def compareTarget(self) -> dict[str, bool]:
        # self.test(1)
        cursor: sqlite3.Cursor
        cachedRatesdb: sqlite3.Connection
        cursor, cachedRatesdb = self.connect2cache()
        today: str = str(dt.date.today - dt.timedelta(days=1))

        cursor.execute("SELECT timestamp FROM cache")
        timestamps: list[str] = [row[0] for row in cursor.fetchall()]
        if today in timestamps:
            cursor.execute(f"SELECT * FROM cache WHERE timestamp = '{today}'")
            row = cursor.fetchone()
            rates = {"time": row[0], "INR": row[1], "EUR": row[2], "GBP": row[3], "DOGE": row[4], "LTC": row[5]}
            print(f"rates for {today} already in sqlite3 cache {rates}")
        else:
            rates: dict[str, str | float] = self.fetchRates()

        res: dict[str, bool] = {"DOGE": False, "LTC": False}
        if self.homeCurrency != "USD":
            res["DOGE"] = self.moneyToBuyDOGE / (rates[self.homeCurrency] * self.numOfDOGEToBuy) >= rates["DOGE"]
            res["LTC"] = self.moneyToBuyLTC / (rates[self.homeCurrency] * self.numOfLTCToBuy) >= rates["LTC"]
        else:
            res["DOGE"] = self.moneyToBuyDOGE / self.numOfDOGEToBuy >= rates["DOGE"]
            res["LTC"] = self.moneyToBuyLTC / self.numOfLTCToBuy >= rates["LTC"]

        cachedRatesdb.close()
        return res

    def ratesThisWeek(self) -> list[dict[str, str | float]]:
        cursor: sqlite3.Cursor
        cachedRatesdb: sqlite3.Connection
        cursor, cachedRatesdb = self.connect2cache()
        today: dt.date = dt.date.today()
        ratesThisWeekAsListOfDicts: list[dict[str, str | float]] = list(dict())

        cursor.execute("SELECT timestamp FROM cache")
        timestamps: list[str] = [row[0] for row in cursor.fetchall()]
        for i in range(7, 0, -1):
            date = str(today - dt.timedelta(days=i))
            if date not in timestamps:
                ratesThisWeekAsListOfDicts.append(self.fetchRates(date))
            else:
                print(f"rates for {date} already cached")

        cachedRatesdb.commit()
        cachedRatesdb.close()
        return ratesThisWeekAsListOfDicts

    def dbHandler(self) -> None:
        cursor: sqlite3.Cursor
        cachedRatesdb: sqlite3.Connection
        cursor, cachedRatesdb = self.connect2cache()
        weekRates: list[dict[str, str | float]] = self.ratesThisWeek()

        for dc in weekRates:
            cursor.execute(f"INSERT INTO cache VALUES ('{dc['time']}', {dc['INR']}, {dc['EUR']}, {dc['GBP']}, {dc['DOGE']}, {dc['LTC']})")
            print(f"cached {dc}")

        cachedRatesdb.commit()
        cachedRatesdb.close()
        self.printDB()

    def printDB(self) -> None:
        cursor: sqlite3.Cursor
        cachedRatesdb: sqlite3.Connection
        cursor, cachedRatesdb = self.connect2cache()

        cursor.execute("SELECT * FROM cache")
        table: prettytable.PrettyTable | None = prettytable.from_db_cursor(cursor)
        print(table)

        cachedRatesdb.close()

    def plot(self, coin: str) -> None:
        cursor: sqlite3.Cursor
        cachedRatesdb: sqlite3.Connection
        cursor, cachedRatesdb = self.connect2cache()

        cursor.execute(f"SELECT timestamp, {coin} FROM cache")
        result: list[tuple[str, float]] = cursor.fetchall()
        timestamps: np.ndarray[str, np.dtype[np.string_]] = np.array([result[0] for result in result])
        coinRates: np.ndarray[float, np.dtype[np.float64]] = np.array([result[1] for result in result])
        cachedRatesdb.close()

        plt.style.use("dark_background")
        plt.plot(timestamps, coinRates, color="#a01bf2")
        plt.title(f"Historical Exchange Rate Of {coin} in USD")
        plt.xlabel("Timestamps (in days)")
        plt.ylabel(f"{coin}'s exchange rate (in USD)")
        figManager: plt.FigureManagerBase = plt.get_current_fig_manager()
        figManager.window.state("normal")
        plt.show()

    def test(self, rowsTBDel: int) -> None:
        if rowsTBDel < 1:
            print("Bad Input: cache unchanged")
            return
        cursor: sqlite3.Cursor
        cachedRatesdb: sqlite3.Connection
        cursor, cachedRatesdb = self.connect2cache()

        cursor.execute("SELECT COUNT(*) FROM cache")
        num_rows: int = cursor.fetchone()[0]
        if num_rows >= rowsTBDel:
            cursor.execute(f"DELETE FROM cache WHERE ROWID IN (SELECT ROWID FROM cache ORDER BY ROWID DESC LIMIT {rowsTBDel})")
            cachedRatesdb.commit()
            print(f"Last {rowsTBDel} rows successfully deleted")
            cachedRatesdb.commit()
            self.printDB()
        else:
            print(f"There are not enough rows in cache to delete the last {rowsTBDel} rows")

        cachedRatesdb.close()


if __name__ == "__main__":
    instance = backend("INR", -1, -1, -1, -1)
    backend.dbHandler(self=instance)
    backend.compareTarget(self=instance)
