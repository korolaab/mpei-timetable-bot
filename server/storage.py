from config import MONGO_URI
from pymongo import MongoClient

connection = MongoClient(MONGO_URI)
db = connection.mpeitt