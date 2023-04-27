import backend

if __name__ == "__main__":
    testObj = backend.backend("INR", -1, -1, -1, -1)
    print("Current Cache Status:")
    testObj.printDB()
    rowsToBeDeleted = int(input("\n\nEnter how many rows to delete from the bottom: "))
    testObj.test(rowsToBeDeleted)
