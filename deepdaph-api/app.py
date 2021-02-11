import httplib2
from flask import Flask, url_for
from flask_restplus import Api
h = httplib2.Http(".cache", disable_ssl_certificate_validation=True)
from flask_cors import CORS
from namespaces.image import imageNamespace as imageApi
from namespaces.prediction import predictionNamespace as predictApi
from namespaces.task import taskNamespace as taskApi
from globals.globals import oidc, clients, model_uris, mongoClient, minioClient, image_path
import os
import json
from werkzeug.middleware.proxy_fix import ProxyFix


# with open('/deepdaph-api/conf/client_s.json') as json_file:
#     data = json.load(json_file)

with open('./conf/client_s.json') as json_file:
    data = json.load(json_file)

# client_secret = '24c9410f-935f-499d-aca4-1e52ae496cbf'
client_secret = data['web']['client_secret']

try:
    daphobdmodel = os.environ['DAPHOBD']
except KeyError as ke:
    daphobdmodel = 'http://localhost:8501/v1/models/daphobd:predict'
try:
    heartmodel = os.environ['HEART3']
except KeyError as ke:
    heartmodel = 'http://localhost:8501/v1/models/heart3:predict'
try:
    abdomen3model = os.environ['ABDOMEN3']
except KeyError as ke:
    abdomen3model = 'http://localhost:8501/v1/models/abdomen3:predict'
try:
    abdomen5model = os.environ['ABDOMEN5']
except KeyError as ke:
    abdomen5model = 'http://localhost:8501/v1/models/abdomen5:predict'
try:
    quotas = os.environ['QUOTAS']
    if quotas == 'True':
        quotas = True
except KeyError as ke:
    quotas = True
try:
    imagepath = os.environ['IMAGE_PATH']
except KeyError as ke:
    imagepath = './'


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

CORS(app)

# app.config.update({
#     'SECRET_KEY': client_secret,
#     'TESTING': True,
#     'DEBUG': True,
#     'OIDC_CLIENT_SECRETS': "/deepdaph-api/conf/client_s.json",
#     'OIDC_ID_TOKEN_COOKIE_SECURE': False,
#     'OIDC_REQUIRE_VERIFIED_EMAIL': False,
#     'OIDC_USER_INFO_ENABLED': True,
#     'OIDC_OPENID_REALM': 'jaqpot',
#     'OIDC_SCOPES': ['openid', 'email', 'profile'],
#     'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
# })

app.config.update({
    'SECRET_KEY': client_secret,
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': "./conf/client_s.json",
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'jaqpot',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
})

authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

if os.environ.get('HTTPS'):
    @property
    def specs_url(self):
        return url_for(self.endpoint('specs'), _external=True, _scheme='https')

# Api.specs_url = specs_url


# Api.specs_url = specs_url
ddapi = Api(app=app, version='1.0'
            , title="Deep Daph"
            , description='Deep Daph API', authorizations=authorizations)

# ddapi.specs_url = specs_url()

ddapi.add_namespace(predictApi)
ddapi.add_namespace(imageApi)
ddapi.add_namespace(taskApi)

oidc.init_app(app)

clients['mongo'] = mongoClient
clients['minio'] = minioClient
model_uris['daphobd'] = daphobdmodel
model_uris['heartmodel'] = heartmodel
model_uris['abdomen3model'] = abdomen3model
model_uris['abdomen5model'] = abdomen5model
image_path['IMAGE_PATH'] = imagepath

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)


# fileNamespace = Namespace('file')
#
# ddapi.add_namespace(fileNamespace)
#
# parser = reqparse.RequestParser()
# parser.add_argument('id', type=str, help='entity id')
# parser.add_argument('thumbnail', type=bool, help='thumbnail')
#
# @fileNamespace.route('/image', methods=['GET'])
# class MainClass(Resource):
#
#     @fileNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
#     # @imageNamespace.
#     # @imageNamespace.param('skip', 'skip')
#     # @imageNamespace.param('max', 'max')
#     @fileNamespace.param('thumbnail', 'thumbnail')
#     @fileNamespace.param('id', 'id')
#         # @imageNamespace.model(models.Image)
#     # @token_required
#     # @imageNamespace.marshal_with(image_model, as_list=True)
#     @fileNamespace.produces(['application/octet-stream'])
#     @ddapi.representation('image/jpeg')
#     def get(self):
#         args = parser.parse_args()
#         image_id = args.get('id')
#         # skip = args.get('skip')
#         # maximum = args.get('maximum')
#         thumb = args.get('thumbnail')
#         token = request.headers['Authorization']
#         token = token.split(" ")[1]
#         userid = "2425d760-018d-408a-ae0b-cde4c56354b9"
#
#         @after_this_request
#         def save_or_delete_file(response):
#                 if os.path.exists('./' + name):
#                     os.remove('./' + name)
#
#         query = {"$and": [{"userId": userid}, {"imageId": image_id}]}
#         found = mongoClient['image'].find_one(query)
#         photo = found['photo']
#         bucket = photo.split("/")[0]
#         name = photo.split("/")[1]
#         minioClient.fget_object(bucket, name, './' + name)
#         if thumb is not None:
#             im = Image.open('./' + name)
#             size = 128, 128
#             im.thumbnail(size)
#             im.save(name, "JPEG")
#             try:
#                 return send_from_directory(directory="./", filename=name, mimetype='image/jpeg',
#                                            conditional=True)
#             except Exception:
#                 abort(404)
#         else:
#             return send_from_directory(directory="./", filename=name, mimetype='image/jpeg', conditional=True)


# props['mongouri'] = mongouri
# props['miniobase'] = miniobase
# props['minioaccess'] = minioaccess
# props['miniosecret'] = miniosecret
# props['secure'] = miniosecure

# mongoClient = MONGO(mongouri=mongouri)
# minioClient = Minio(miniobase, access_key=minioaccess, secret_key=miniosecret, secure=miniosecure)

# app = Flask(__name__)
# CORS(app)
#
# app.config.update({
#     'SECRET_KEY': gl.client_secret,
#     'TESTING': True,
#     'DEBUG': True,
#     'OIDC_CLIENT_SECRETS': "client_s.json",
#     'OIDC_ID_TOKEN_COOKIE_SECURE': False,
#     'OIDC_REQUIRE_VERIFIED_EMAIL': False,
#     'OIDC_USER_INFO_ENABLED': True,
#     'OIDC_OPENID_REALM': 'jaqpot',
#     'OIDC_SCOPES': ['openid', 'email', 'profile'],
#     'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
# })
#
# authorizations = {
#     'Bearer': {
#         'type': 'apiKey',
#         'in': 'header',
#         'name': 'Authorization'
#     }
# }
#
# ddapi = Api(app=app, version='1.0'
#                            , title="Deep Daph"
#                            , description='Deep Daph API', authorizations=authorizations)
#
# ddapi.add_namespace(historyApi)
# ddapi.add_namespace(imageApi)
#
# oidc = OpenIDConnect(app=app)


# app.wsgi_app = authentication.Auth(app.wsgi_app, app)

# deepdaphapi = ddapi.namespace('deepdaphapi')
# loginapi = ddapi.namespace('login')



# min_max = reqparse.RequestParser()
# min_max.add_argument('skip')
# min_max.add_argument('max')
#
#
# prediction = ddapi.model('Prediction',
#                        {'type': 'object',
#                         'properties': {
#                             '_id': {'type': 'string', 'minLength': 3, 'maxLength': 82},
#                             'userid': {'type': 'string', 'minLength': 3, 'maxLength': 82},
#                             "prediction": {'type': 'string', 'pattern': '[0-9A-F]{64}'},
#                             "inputphoto":{'type': 'string', 'pattern': '[0-9A-F]{64}'},
#                             "forpredphoto":{'type': 'string', 'pattern': '[0-9A-F]{64}'},
#                             "date":{'type': 'string', 'pattern': '[0-9A-F]{64}'}
#                         }})
#
# login_dto = ddapi.model('logindto',
#                   {'username': fields.String(required=True, description="Name of the person")},
#                   {'password': fields.String(required=True, description="Users password")})

# predict = app.namespace('predict')


# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = None
#         if 'Authorization' in request.headers:
#             token = request.headers['Authorization']
#         if not token:
#             return {'message': 'Token is missing.'}, 401
#         if oidc.validate_token(token) is True:
#             # try:
#             #     userid = oidc.user_getfield('sub', token)
#             #     qug = pyquots.get_user(userid=userid)
#             # except quotserrors.UserNotFound as unf:
#             #     quouser = pyquots_named_tuples.QuotsUser(id=userid
#             #                                           , email=oidc.user_getfield('email', token)
#             #                                           , username=oidc.user_getfield('preferred_username', token))
#             #     pyquots.create_user(quouser)
#             return f(*args, **kwargs)
#         else:
#             return {'message': 'Token is not validating.'}, 401
#     return decorated

#
# @deepdaphapi.route("/")
# class MainClass(Resource):
#     @token_required
#     def get(self):
#         return {
#             "pong": "Got ping"
#         }


# @loginapi.route("/")
# class LoginApi(Resource):
#     @loginapi.expect(login_dto)
#     def post(self):
#         oidc.get_access_token()
#         return {"asf":"asdf"}


# @deepdaphapi.route('/headstails/', methods=['POST'])
# class MainClass(Resource):
#     @api.representation('image/jpeg')
#     @deepdaphapi.expect(file_upload)
#     @deepdaphapi.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
#     @token_required
#     def post(self):
#         args = file_upload.parse_args()
#         token = request.headers['Authorization']
#         userid = oidc.user_getfield('sub', token)
#         # canpr = pyquots.can_user_proceed(userid=userid, usagetype='PREDICTION', usagesize="1")
#         # if canpr.proceed is not True:
#         #     abort(402, "Not enough credits available")
#         if args['file'].mimetype == 'image/jpeg' or args['file'].mimetype == 'image/png' or args['file'].mimetype == 'application/octet-stream':
#             file = request.files['file']
#             filename = file.filename
#             file.save("./" + filename)
#             im = Image.open("./" + file.filename)
#             imar = np.asarray(im)
#             payload = {"instances": [imar.tolist()]}
#             res = requests.post(daphheatmodel, json=payload)
#             # res = requests.post("http://localhost:8501/v1/models/daphheat:predict", json=payload)
#             resp = res.json()
#             head = []
#             tail = []
#             for respon in resp['predictions']:
#                 if respon['num_detections'] > 1:
#                     i = 0
#                     for clas in respon['detection_classes']:
#                         if clas == 3:
#                             tail = respon['detection_boxes'][i]
#                         if clas == 2:
#                             head = respon['detection_boxes'][i]
#                         i += 1
#             im_width, im_height = im.size
#             if len(head) > 2 and len(tail) > 2:
#                 head = [int(head[1] * im_width), int(head[3] * im_width),
#                         int(head[0] * im_height), int(head[2] * im_height)]
#                 tail = [int(tail[1] * im_width), int(tail[3] * im_width),
#                         int(tail[0] * im_height), int(tail[2] * im_height)]
#                 if tail[0] < head[0]:
#                     x_min = tail[0]
#                 else:
#                     x_min = head[0]
#
#                 if tail[1] > head[1]:
#                     x_max = tail[1]
#                 else:
#                     x_max = head[1]
#                 if tail[2] < head[2]:
#                     y_min = tail[2]
#                 else:
#                     y_min = head[2]
#                 if tail[3] > head[3]:
#                     y_max = tail[3]
#                 else:
#                     y_max = head[3]
#                 area = (x_min, y_min, x_max, y_max)
#                 (dx, dy) = (((area[2] + area[0]) / 2) - ((head[1] + head[0]) / 2),
#                             ((head[3] + head[2]) / 2) - ((area[3] + area[1]) / 2))
#                 try:
#                     angle = degrees(atan(float(dy) / float(dx)))
#                 except ZeroDivisionError:
#                     abort(404, "Could not process image for prediction")
#                 if angle < 0:
#                     angle += 180
#                 ima_c = im.crop((area[0] * 0.7, area[1] * 0.7, area[2] * 1.2, area[3] * 1.2))
#                 imr = ima_c.rotate(180 - angle, expand=True)
#                 imr.thumbnail((512, 512), Image.ANTIALIAS)
#                 # outfile1 = './processed/' + filename.split(".")[0] + '_forprediction.jpeg'
#                 outfile1 = filename.split(".")[0] + '_forprediction.jpeg'
#                 # imr.save(outfile1, "JPEG")
#                 img_w, img_h = imr.size
#                 background = Image.new('RGB', (512, 512), (0, 0, 0))
#                 bg_w, bg_h = background.size
#                 offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
#                 # imr = imr.filter(ImageFilter.SHARPEN)
#                 background.paste(imr, offset)
#                 background.save(outfile1, "JPEG")
#
#                 @after_this_request
#                 def save_or_delete_file(response):
#                     if args.get('save') == 'false':
#                         if os.path.exists(outfile1):
#                             os.remove(outfile1)
#                             os.remove(filename)
#                     else:
#                         pyquots.can_user_proceed(userid=userid, usagetype='SAVEIMAGE', usagesize="1")
#                         users_bucket = userid + '-deepdaph'
#                         try:
#                             minio.make_bucket(users_bucket)
#                         except BucketAlreadyOwnedByYou as err:
#                             minio.fput_object(users_bucket, filename, filename)
#                             minio.fput_object(users_bucket, outfile1, outfile1)
#                             quer = users_bucket + "/" + filename
#                             found = mongo['predictions'].find_one({"inputphoto":quer})
#                             if found is None:
#                                 pred = models.Predictions(userid=userid, inputphoto=users_bucket + "/" + filename
#                                                           , forpredphoto=users_bucket + "/" + outfile1, date=args.get('date'))
#                                 mongo['predictions'].insert_one(pred._asdict())
#                             os.remove(filename)
#                             os.remove(outfile1)
#                         except BucketAlreadyExists as err:
#                             minio.fput_object(users_bucket, filename, filename)
#                             minio.fput_object(users_bucket, outfile1, outfile1)
#                             quer = users_bucket + "/" + filename
#                             found = mongo['predictions'].find_one({"inputphoto":quer})
#                             if found is None:
#                                 pred = models.Predictions(userid=userid, inputphoto=users_bucket + "/" + filename
#                                                           , forpredphoto=users_bucket + "/" + outfile1, date=args.get('date'))
#                                 mongo['predictions'].insert_one(pred._asdict())
#                             os.remove(filename)
#                             os.remove(outfile1)
#                         except ResponseError as err:
#                             print(err)
#                             os.remove(filename)
#                             os.remove(outfile1)
#                     return response
#
#                 return send_file(outfile1)
#             else:
#                 abort(404, "Could not process image for prediction")
#         else:
#             abort(404)
#         return {'status': 'Done'}
#
#
# @deepdaphapi.route('/class/', methods=['POST'])
# class MainClass(Resource):
#     @api.representation('image/jpeg')
#     @deepdaphapi.expect(file_upload)
#     @deepdaphapi.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
#     @token_required
#     def post(self):
#         args = file_upload.parse_args()
#         token = request.headers['Authorization']
#         userid = oidc.user_getfield('sub', token)
#         canpr = pyquots.can_user_proceed(userid=userid, usagetype='PREDICTION', usagesize="1")
#         if canpr.proceed is not True:
#             abort(402, "Not enough credits available")
#         if args['file'].mimetype == 'image/jpeg' or args['file'].mimetype == 'image/png' or args['file'].mimetype == 'application/octet-stream':
#             file = request.files['file']
#             filename = file.filename
#             file.save("./" + filename)
#             imar = Image.open("./" + file.filename)
#             imar = np.asarray(imar)
#             payload = {"instances": [imar.tolist()]}
#             res = requests.post(deepdaphmodel, json=payload)
#             resp = res.json()
#             preds = resp['predictions']
#             pred = preds[0]
#             if pred[0] > pred[1]:
#                 clas = 'Damaged'
#             else:
#                 clas = 'Non damaged'
#             @after_this_request
#             def update_prediction(response):
#                 querys = userid + "-deepdaph/" + filename
#                 findpred = {"forpredphoto": querys}
#                 update = {"$set":{"prediction":clas}}
#                 mongo['predictions'].update_one(findpred, update)
#                 os.remove(filename)
#                 return response
#             return {'Class': clas}
