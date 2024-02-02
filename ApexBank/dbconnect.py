from pymongo import MongoClient

def get_db_handle(dbName):
    client = MongoClient("mongodb://3.136.254.218:27017")
    db = client[dbName]
    return db

def get_collection_handle(db, collectionName):
    return db[collectionName]

