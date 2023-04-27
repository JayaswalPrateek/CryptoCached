import backend

testObj = backend.backend("INR", -1, -1, -1, -1)
print("Present Cache Status:")
testObj.printDB()
testObj.test(int(input("\n\nEnter how many rows to delete from the bottom of the Cache: ")))
