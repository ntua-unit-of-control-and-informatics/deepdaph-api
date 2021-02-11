# import minio
from minio import Minio

class MINIO(object):

    def __init__(self):
        print("Starting with minio")
        # self.URI = mongouri
        # self.mongopass = mongopass
        # self.mongousename = mongousername
        # self.database = database

    # @staticmethod
    def init(self, miniobase, minioaccess, miniosecret, miniosecure):
        print("Starting with minio at " + miniobase)
        return Minio(miniobase, access_key=minioaccess, secret_key=miniosecret, secure=miniosecure)

    # # @staticmethod
    # def insert(self, collection, data):
    #     DB.DATABASE[collection].insert(data)

    # # @staticmethod
    # def find_one(self, collection, query):
    #     return DB.DATABASE[collection].find_one(query)
