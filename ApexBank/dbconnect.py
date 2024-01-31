from pymongo import MongoClient

def get_db_handle(dbName):
    client = MongoClient("mongodb://localhost:27017")
    db = client[dbName]
    return db

def get_collection_handle(db, collectionName):
    return db[collectionName]

