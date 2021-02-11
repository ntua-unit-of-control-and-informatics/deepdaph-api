import os
from minio import Minio
from .mongodb import MONGO
from flask_oidc import OpenIDConnect



try:
    mongouri = os.environ['MONGO_URI']
except KeyError as ke:
    mongouri = 'mongodb://127.0.0.1:27017'
try:
    daphobdmodel = os.environ['DAPHOBD']
except KeyError as ke:
    daphobdmodel = 'http://localhost:8501/v1/models/daphobd/versions/1'
try:
    heartmodel = os.environ['HEART3']
except KeyError as ke:
    heartmodel = 'http://localhost:8501/v1/models/heart3/versions/1'
try:
    abdomen3model = os.environ['ABDOMEN3']
except KeyError as ke:
    abdomen3model = 'http://localhost:8501/v1/models/abdomen3/versions/1'
try:
    abdomen5model = os.environ['ABDOMEN5']
except KeyError as ke:
    abdomen5model = 'http://localhost:8510/v1/models/abdomen5/versions/1'
try:
    miniobase = os.environ['MINIO_BASE']
except KeyError as ke:
    miniobase = '127.0.0.1:9000'
try:
    minioaccess = os.environ['MINIO_ACCESS_KEY']
except KeyError as ke:
    minioaccess = 'minio'
try:
    miniosecret = os.environ['MINIO_SECRET_KEY']
except KeyError as ke:
    miniosecret = 'miniolocal'
try:
    miniosecure = os.environ['MINIO_SECURE']
    if miniosecure == "True":
        miniosecure = True
except KeyError as ke:
    miniosecure = False

oidc = OpenIDConnect()
props = {}


mongoClient = MONGO(mongouri=mongouri).init()
minioClient = Minio(miniobase, access_key=minioaccess, secret_key=miniosecret, secure=miniosecure)

clients = {}
model_uris = {}
image_path = {}



# def run_mongo():
#     mongoClient = MONGO(props['mongouri'])
#
# def run_minio():
#     minioClient = Minio(props['miniobase'], access_key=props['minioaccess'], secret_key=props['miniosecret'], secure=props['miniosecure'])

# def singleton(cls):
#     instances = {}
#     def wrapper(*args, **kwargs):
#         if cls not in instances:
#           instances[cls] = cls(*args, **kwargs)
#         return instances[cls]
#     return wrapper
#
#
# @singleton
# class Globals:
#
#     # minioClient = {}
#     # mongoClient = {}
#     # oidc = {}
#
#     def __init__(self):
#         self.client_secret = '24c9410f-935f-499d-aca4-1e52ae496cbf'
#         try:
#             self.mongouri = os.environ['MONGO_URI']
#         except KeyError as ke:
#             self.mongouri = 'mongodb://127.0.0.1:27017'
#         try:
#             self.daphheatmodel = os.environ['DAPHOBD']
#         except KeyError as ke:
#             self.daphheatmodel = 'http://localhost:8501/v1/models/daphobd/versions/1'
#         try:
#             self.deepdaphmodel = os.environ['HEART3']
#         except KeyError as ke:
#             self.deepdaphmodel = 'http://localhost:8501/v1/models/heart3/versions/1'
#         try:
#             self.daphheatmodel = os.environ['ABDOMEN3']
#         except KeyError as ke:
#             self.daphheatmodel = 'http://localhost:8501/v1/models/abdomen3/versions/1'
#         try:
#             self.deepdaphmodel = os.environ['ABDOMEN5']
#         except KeyError as ke:
#             self.deepdaphmodel = 'http://localhost:8510/v1/models/abdomen5/versions/1'
#         try:
#             miniobase = os.environ['MINIO_BASE']
#         except KeyError as ke:
#             miniobase = '127.0.0.1:9000'
#         try:
#             minioaccess = os.environ['MINIO_ACCESS_KEY']
#         except KeyError as ke:
#             minioaccess = 'minio'
#         try:
#             miniosecret = os.environ['MINIO_SECRET_KEY']
#         except KeyError as ke:
#             miniosecret = 'miniolocal'
#         try:
#             miniosecure = os.environ['MINIO_SECURE']
#             if miniosecure == "True":
#                 miniosecure = True
#         except KeyError as ke:
#             miniosecure = False
#         try:
#             quotas = os.environ['QUOTAS']
#             if quotas == 'True':
#                 quotas = True
#         except KeyError as ke:
#             quotas = True
#
#         self.mongoClient = MONGO(mongouri=self.mongouri, database="deepdaph").init()
#         self.minioClient = Minio(miniobase, access_key=minioaccess, secret_key=miniosecret, secure=miniosecure)
#         # pyquots = Pyquots('127.0.0.1:8000', 'DEEPDAPH', '&dphkI$BUSfZ&5gg^h')
#
#     # @property
#     def mongo_client(self):
#         return self.mongoClient
#
#     # @property
#     def minio_client(self):
#         return self.minioClient
#
#     # @property
#     def get_oidc(self):
#         return self.oidc

    # def reset(self):
    #     self.oidc = {}
    #     self.minioClient = {}
    #     self.mongoClient = {}
