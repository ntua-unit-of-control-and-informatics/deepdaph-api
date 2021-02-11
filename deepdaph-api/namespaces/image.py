from flask_restplus import Namespace, Resource
from minio.error import ( BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)
from models import models
from flask import request
import werkzeug
from flask_restplus import reqparse, fields
from help import randomString
import os
from flask import send_file, after_this_request, Response, abort
import json
from globals.globals import oidc, mongoClient, minioClient, image_path
from functools import wraps
import time
from bson import json_util
from PIL import Image

imageNamespace = Namespace('image')


parser = reqparse.RequestParser()
parser.add_argument('skip', type=int, help='skip documents')
parser.add_argument('maximum', type=int, help='maximum documents returned')
parser.add_argument('id', type=str, help='entity id')
parser.add_argument('thumbnail', type=bool, help='thumbnail')


image_model = imageNamespace.model('Image', {
     'imageId': fields.String(required=True, description='image id'),
     'control': fields.String(description='Control or not'),
     'exposed': fields.String(description='Exposed or not'),
     'exposedAt': fields.String(description='Exposed at of exposed'),
     'age': fields.String(description='Age of Daphnia'),
     'generation': fields.String(description='Generation of daphnia'),
     'mm': fields.Integer(description='The μΜ of the scale per pixels'),
     'pixels': fields.Integer(description='The pixels of the scale'),
})

file_upload = reqparse.RequestParser()
file_upload.add_argument('file',
                         type=werkzeug.datastructures.FileStorage,
                         location='files',
                         required=True,
                         help='file')
file_upload.add_argument('save')
file_upload.add_argument('date')
file_upload.add_argument('control')
file_upload.add_argument('exposed')
file_upload.add_argument('exposedAt')
file_upload.add_argument('age')
file_upload.add_argument('generation')
file_upload.add_argument('mm')
file_upload.add_argument('pixels')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            token = token.split(" ")[1]
        if not token:
            return {'message': 'Token is missing.'}, 401
        if oidc.validate_token(token) is True:
            # try:
            #     userid = oidc.user_getfield('sub', token)
            #     qug = pyquots.get_user(userid=userid)
            # except quotserrors.UserNotFound as unf:
            #     quouser = pyquots_named_tuples.QuotsUser(id=userid
            #                                           , email=oidc.user_getfield('email', token)
            #                                           , username=oidc.user_getfield('preferred_username', token))
            #     pyquots.create_user(quouser)
            return f(*args, **kwargs)
        else:
            return {'message': 'Token is not validating.'}, 401
    return decorated


@imageNamespace.route('/', methods=['POST', 'PUT', 'GET', 'DELETE'])
class MainClass(Resource):
    @imageNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    @imageNamespace.expect(file_upload)
    @token_required
    def post(self):
        args = file_upload.parse_args()
        # token = request.headers['Authorization']
        # userid = oidc.user_getfield('sub', token)
        # canpr = pyquots.can_user_proceed(userid=userid, usagetype='PREDICTION', usagesize="1")
        # if canpr.proceed is not True:
        #     abort(402, "Not enough credits available")
        if args['file'].mimetype == 'image/jpeg' or args['file'].mimetype == 'image/png' or args['file'].mimetype == 'application/octet-stream':
            token = request.headers['Authorization']
            token = token.split(" ")[1]
            userid = oidc.user_getfield('sub', token)
            file = request.files['file']
            control = args['control']
            exposed = args['exposed']
            exposedAt = args['exposedAt']
            age = args['age']
            generation = args['generation']
            mm = args['mm']
            pixels = args['pixels']
            time_got = int(round(time.time() * 1000))
            filename = file.filename
            file.save(image_path['IMAGE_PATH'] + filename)
            # filename = image_path['IMAGE_PATH'] + filename
            # im = Image.open("./" + file.filename)
                # pyquots.can_user_proceed(userid=userid, usagetype='SAVEIMAGE', usagesize="-1")
            users_bucket = userid + "-deepdaph"
            photoid = randomString(12)
            image = models.Image(userId=userid, photo=users_bucket + "/" + filename
                                 , imageId=photoid, control=control, exposed=exposed
                                 , exposedAt=exposedAt, age=age, generation=generation
                                 , mm=mm, pixels=pixels, time=time_got)
            mongoClient['image'].insert_one(image._asdict())
            try:
                minioClient.make_bucket(users_bucket)
            except BucketAlreadyOwnedByYou as err:
                minioClient.fput_object(users_bucket, filename, image_path['IMAGE_PATH'] + filename)
                os.remove(image_path['IMAGE_PATH'] + filename)
            except BucketAlreadyExists as err:
                minioClient.fput_object(users_bucket, filename, image_path['IMAGE_PATH'] + filename)
                os.remove(image_path['IMAGE_PATH'] + filename)
            resp = Response(json.dumps(image._asdict()))
            resp.headers["Access-Control-Expose-Headers"] = '*'
            return resp
        else:
            abort(404)

    @imageNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    @imageNamespace.expect(image_model)
    # @imageNamespace.model(models.Image)
    @token_required
    def put(self):
        token = request.headers['Authorization']
        token = token.split(" ")[1]
        userid = oidc.user_getfield('sub', token)
        image = request.json
        myquery = {"$and": [{"userId": userid}, {"imageId": image['photoId']}]}
        update = {"$set": {"exposed": image['exposed'], "exposedAt": image["exposedAt"], "age": image["age"]
            , "generation": image["generation"], "mm": image["mm"], "pixels": image["pixels"]}}
        try:
            mongoClient['image'].update_one(myquery,update=update)
        except Exception as e:
            abort(404, "Could not update image")
        image_updated = mongoClient['image'].find_one(myquery)
        resp = Response(json_util.dumps(image_updated))
        resp.headers["Access-Control-Expose-Headers"] = '*'
        return resp

    @imageNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    # @imageNamespace.
    @imageNamespace.param('skip', 'skip')
    @imageNamespace.param('max', 'max')
    @imageNamespace.param('thumbnail', 'thumbnail')
    @imageNamespace.param('id', 'id')
    # @imageNamespace.model(models.Image)
    @token_required
    # @imageNamespace.marshal_with(image_model, as_list=True)
    # @imageNamespace.produces(["application/json", 'application/octet-stream'])
    @imageNamespace.produces(["application/json", 'application/octet-stream'])

    def get(self):
        args = parser.parse_args()
        image_id = args.get('id')
        skip = args.get('skip')
        maximum = args.get('maximum')
        thumb = args.get('thumbnail')
        token = request.headers['Authorization']
        token = token.split(" ")[1]
        userid = oidc.user_getfield('sub', token)
        if request.headers.get('accept') == 'application/json':
            if skip is None:
                skip = 0
            if maximum is None:
                max = 20
            if image_id is None:
                myquery = {"userId": userid}
                found = []
                try:
                    cursor = mongoClient['image'].find(myquery).skip(skip).limit(maximum)
                    for f in cursor:
                        found.append(json_util.dumps(f))
                    resp = Response(json_util.dumps(found))
                    resp.headers["Access-Control-Expose-Headers"] = '*'
                    return resp
                except Exception as e:
                    abort(404, "Could not get images")
            if image_id is not None:
                myquery = {"$and": [{"userId": userid}, {"imageId": image_id}]}
                found = mongoClient['image'].find_one(myquery)
                resp = Response(json_util.dumps(found))
                resp.headers["Access-Control-Expose-Headers"] = '*'
                return resp
        if request.headers.get('accept') == 'application/octet-stream':

            query = {"$and": [{"userId": userid}, {"imageId": image_id}]}
            found = mongoClient['image'].find_one(query)
            if found:
                photo = found['photo']
                bucket = photo.split("/")[0]
                name = photo.split("/")[1]

                @after_this_request
                def save_or_delete_file(response):
                    try:
                        if os.path.exists(image_path['IMAGE_PATH'] + name):
                            os.remove(image_path['IMAGE_PATH'] + name)
                        return response
                    except Exception:
                        return response
                try:
                    minioClient.fget_object(bucket, name, image_path['IMAGE_PATH'] + name)
                except Exception:
                    abort(500, "Could not find image")
                if thumb is not None:
                    im = Image.open(image_path['IMAGE_PATH'] + name)
                    size = 128, 128
                    im.thumbnail(size)
                    im.save(image_path['IMAGE_PATH'] + name, "JPEG")
                    try:
                        return send_file(image_path['IMAGE_PATH'] + name)
                    except Exception:
                        abort(404)
                else:
                    return send_file(image_path['IMAGE_PATH'] + name)


    @imageNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    @imageNamespace.expect(fields=image_model)
    # @imageNamespace.model(models.Image)
    @token_required
    def delete(self):
        token = request.headers['Authorization']
        token = token.split(" ")[1]
        userid = oidc.user_getfield('sub', token)
        image = request.json
        delete = {"$and": [{"userId": userid}, {"imageId": image['photoId']}]}
        try:
            mongoClient['image'].delete_one(delete)
        except Exception as e:
            abort(404, "Could not delete image")
        resp = Response({"deleted": 1})
        resp.headers["Access-Control-Expose-Headers"] = '*'
        return resp


#
#
# @imageNamespace.route('/<id>', methods=['GET', 'DELETE'])
# @imageNamespace.param('id', 'Image identifier')
# @imageNamespace.param('thumbnail', 'image thumbnail')
# @imageNamespace.param('meta', 'get meta of image or not')
# class MainClass(Resource):
#     @imageNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
#     @token_required
#     def post(self):
#         args = file_upload.parse_args()
#         # token = request.headers['Authorization']
#         # userid = oidc.user_getfield('sub', token)
#         # canpr = pyquots.can_user_proceed(userid=userid, usagetype='PREDICTION', usagesize="1")
#         # if canpr.proceed is not True:
#         #     abort(402, "Not enough credits available")
#         if args['file'].mimetype == 'image/jpeg' or args['file'].mimetype == 'image/png' or args['file'].mimetype == 'application/octet-stream':
#             token = request.headers['Authorization']
#             userid = oidcHelper.user_getfield('sub', token)
#             file = request.files['file']
#             control = args['control']
#             exposed = args['exposed']
#             exposedAt = args['exposedAt']
#             age = args['age']
#             generation = args['generation']
#             mm = args['mm']
#             pixels = args['pixels']
#             filename = file.filename
#             file.save("./" + filename)
#             # im = Image.open("./" + file.filename)
#                 # pyquots.can_user_proceed(userid=userid, usagetype='SAVEIMAGE', usagesize="-1")
#             users_bucket = userid + "-deepdaph"
#             photoid = randomString(12)
#             image = models.Image(userid=userid, photo=users_bucket + "/" + filename
#                                  , photoid=photoid, control=control, exposed=exposed
#                                  , exposedAt=exposedAt, age=age, generation=generation
#                                  , mm=mm, pixels=pixels)
#             mongoClient['images'].insert_one(image._asdict())
#             try:
#                 minioClient(users_bucket)
#             except BucketAlreadyOwnedByYou as err:
#                 minioClient(users_bucket, filename, filename)
#                 os.remove(filename)
#             except BucketAlreadyExists as err:
#                 minioClient(users_bucket, filename, filename)
#                 os.remove(filename)
#             resp = Response(json.dumps(image._asdict()))
#             resp.headers["Access-Control-Expose-Headers"] = '*'
#             return resp
#         else:
#             abort(404)
