import pymongo


class MONGO(object):

    URI = ""
    mongousename = ""
    mongopass = ""
    database = ""

    def __init__(self , mongouri=None, mongopass=None, mongousername=None, database=None):
        print("Starting with mongo at " + mongouri)
        self.URI = mongouri
        self.mongopass = mongopass
        self.mongousename = mongousername
        self.database = database

    # @staticmethod
    def init(self):
        client = pymongo.MongoClient(self.URI)
        if self.database is not None:
            client = client[self.database]
        else:
            client = client['deepdaph']
        return client

    # # @staticmethod
    # def insert(self, collection, data):
    #     DB.DATABASE[collection].insert(data)

    # # @staticmethod
    # def find_one(self, collection, query):
    #     return DB.DATABASE[collection].find_one(query)
