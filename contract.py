"""
HOW FRONTEND SHOULD USE BACKEND:

below i specified how each function can be called from the backend,
remove the interface function and create an object of the backend to call its function

READ THE CODE FIRST AND THEN PROCEED FURTHER

now i will specify the particular order in which it should be called
    example, you cannot plot without creating the database

as soon as the app starts call backendObj.dbHandler() after creating backendObj = backend.backend("INR", 10, 100, 50, 500)
this will create a database if it doesnt exists, if it does it will make sure it has the rates for the lasst seven days
it will automatically use API if the the data is not in the cache

after backendObj.dbHandler() ran successfully, frontend should expose buttons for compareTarget and plot

but we also need to demonstrate caching, so after calling backendObj.dbHandler() once call backendObj.test(2)
which will remove the rates for last 2 days(today and yesterday) from the cache
then it will call backendObj.dbHandler() internally which will use API to get rates for today and yesterday
it wont get the rates for the entire week as the rates for 5 out of 7 days are already in the cache
so there should preferably be a test button to run test()

suggestion: call fetchrates() in the start of the program to dispay the current rates
"""


import backend

if __name__ != "__main__":
    # (homeCurrency: str, numOfDOGEToBuy: float, moneyToBuyDOGE: float, numOfLTCToBuy: float, moneyToBuyLTC: float)
    backendObj = backend.backend("INR", 10, 100, 50, 500)  # this creates an object of backend that exposes the functions of the backend class

    # fetchrates returns something like {'time': '2023-04-27', 'INR': 81.6231, 'EUR': 0.9044, 'GBP': 0.8016, 'DOGE': 0.065553, 'LTC': 72.966157}
    backendObj.fetchRates()  # is an internal function that returns the current rates by default, you can pass a date to get rates on that day
    # this function is used to populate the database with the rates of the previous week and is used by compareTarget internally
    # it can be used by the fronted to show current rates

    # returns {'DOGE': True/False, 'LTC': True/False}
    backendObj.compareTarget()

    # returns a tuple of results of fetchRates() for the entire week API if not in cache
    backendObj.ratesThisWeek()  # used internally and should not be called from the frontend

    backendObj.dbHandler()  # accepts the tuple of rates from ratesThisWeek() and inserts it into the database

    backendObj.printDB()  # prints the contents of the cache database as a table and is called internally

    backendObj.plot("DOGE")  # plots graph for change in rate for DOGE coin
    backendObj.plot("LTC")  # plots graph for change in rate for LTC coin

    backendObj.test(2)  # is an internal function that deletes the last 2 entries from the cache(for today and yesterday)
    # internal function, should not be called from backend
