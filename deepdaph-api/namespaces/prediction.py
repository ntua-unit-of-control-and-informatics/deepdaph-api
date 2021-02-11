from flask_restplus import Namespace, Resource
from models import models
from flask import request
from flask_restplus import fields
from flask import Response, abort
import json
from globals.globals import oidc, mongoClient
from functools import wraps
from .async_handler import async_handler
from multiprocessing import Process
from bson import json_util, ObjectId
from flask_restplus import reqparse
from datetime import datetime, timezone
import base64

epoch = datetime.utcfromtimestamp(0)


def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None).replace(tzinfo=None)


predictionNamespace = Namespace('prediction')

parser = reqparse.RequestParser()
parser.add_argument('skip', type=int, help='skip documents')
parser.add_argument('maximum', type=int, help='maximum documents returned')
parser.add_argument('id', type=str, help='entity id')
parser.add_argument('control', type=str, help='exposed or not')
parser.add_argument('exposed', type=str, help='exposed')
parser.add_argument('exposedAt', type=str, help='exposed at')
parser.add_argument('generation', type= str, help="generation of daphnia")
parser.add_argument('age', type=str, help="age of daphnia")
parser.add_argument('from', type=str, help="'from' date of prediction")
parser.add_argument('to', type=str, help="'to' date of prediction")


prediction_model = predictionNamespace.model('Prediction', {
    'id': fields.String(description='prediction id'),
    'imageId': fields.String(required=True, description='image id'),
    'date': fields.Integer(description='Date of the prediction'),
    'control': fields.String( description='Control or not'),
    'exposed': fields.String( description='Exposed or not'),
    'exposedAt': fields.String(description='Exposed at of exposed'),
    'age': fields.String(description='Age of Daphnia'),
    'generation': fields.String(description='Generation of daphnia'),
    'mm': fields.Integer(description='The μΜ of the scale per pixels'),
    'pixels': fields.Integer(description='The pixels of the scale'),
    'measurementsImageId': fields.String(description='Image id of the image with measurements rendered'),
    'abdomenImageId': fields.String(desription='Image id of the abdomen'),
    'heartImageId': fields.String(desription='Image id of the heart'),
    'abdomen5': fields.List(fields.Float, desription='5 class prediction of the lipids in abdomen'),
    'abdomen3': fields.List(fields.Float, desription='3 class prediction of the lipids in abdomen'),
    'heart3': fields.List(fields.Float, desription='3 class prediction of the lipids in heart')
})


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


@predictionNamespace.route('/', methods=['POST', 'PUT', 'GET', 'DELETE'])
class MainClass(Resource):
    @predictionNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    @predictionNamespace.expect(prediction_model)
    # @predictionNamespace.response(task_model)
    @token_required
    def post(self):
        token = request.headers['Authorization']
        token = token.split(" ")[1]
        userid = oidc.user_getfield('sub', token)
        prediction = request.json
        newTask = models.PredictionTask(userId=userid)
        _predid = mongoClient['prediction'].insert_one(prediction).inserted_id
        _taskid = mongoClient['task'].insert_one(newTask._asdict()).inserted_id
        taskStored = models.PredictionTask(userId=userid, predictionId=_predid, id=_taskid)
        p = Process(target=async_handler.handle_predictions, args=(prediction, taskStored))
        p.start()
        resp = Response(json_util.dumps(taskStored._asdict()))
        resp.headers["Access-Control-Expose-Headers"] = '*'
        return resp
    # else:
    #     abort(404)

    @predictionNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    @predictionNamespace.expect(fields=prediction_model)
    # @imageNamespace.model(models.Image)
    @token_required
    def put(self):
        token = request.headers['Authorization']
        token = token.split(" ")[1]
        userid = oidc.user_getfield('sub', token)
        resp = Response({"Updated": "Nothing updated"})
        resp.headers["Access-Control-Expose-Headers"] = '*'
        return resp

    @predictionNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    # @imageNamespace.
    @predictionNamespace.param('skip', 'skip')
    @predictionNamespace.param('maximum', 'maximum')
    @predictionNamespace.param('id', 'id')
    @predictionNamespace.param('control', 'control')
    @predictionNamespace.param('exposed', 'exposed')
    @predictionNamespace.param('generation', 'generation')
    @predictionNamespace.param('age', 'age')
    @predictionNamespace.param('from', 'from')
    @predictionNamespace.param('to', 'to')
    # @imageNamespace.model(models.Image)
    @token_required
    # @predictionNamespace.marshal_with(prediction_model, as_list=True)
    def get(self):
        args = parser.parse_args()
        id = args.get('id')
        skip = args.get('skip')
        maximum = args.get('maximum')
        control = args.get('control')
        exposed = args.get('exposed')
        exposedAt = args.get('exposedAt')
        generation = args.get('generation')
        age = args.get('age')
        from_d = args.get('from')
        to_d = args.get('to')
        if id is None:
            if skip is None:
                skip = 0
            if maximum is None:
                maximum = 20
            token = request.headers['Authorization']
            token = token.split(" ")[1]
            userid = oidc.user_getfield('sub', token)
            query_u = {"userId": str(userid)}
            q_ar = []
            if age != 'undefined' and age is not None:
                a = {'age': age}
                q_ar.append(a)
            if generation != 'undefined' and generation is not None:
                g = {'generation': generation}
                q_ar.append(g)
            if exposed != 'false' and exposed is not None and exposed != 'undefined':
                ex = {'exposed': 'true'}
                q_ar.append(ex)
            if control != 'false' and control is not None and control != 'undefined':
                co = {'control': 'true'}
                q_ar.append(co)
            if exposedAt != 'undefined' and exposedAt is not None:
                co = {'exposedAt': exposedAt}
                q_ar.append(co)
            if from_d is not None:
                from_d = base64.b64decode(from_d).decode('utf-8')
                if from_d != 'undefined' and from_d is not None:
                    from_d = unix_time_millis(utc_to_local(datetime.strptime(from_d, '%a %b %d %Y %H:%M:%S %Z%z')))
                    # from_d = unix_time_millis(datetime.strptime(from_d, "%a %b %d %H:%M:%S %Y (%Z)"))
                    f_d = {'date': {'$gt': from_d}}
                    q_ar.append(f_d)
            if to_d is not None:
                to_d = base64.b64decode(to_d).decode('utf-8')
                if to_d != 'undefined' and to_d is not None:
                    to_d = unix_time_millis(utc_to_local(datetime.strptime(to_d, '%a %b %d %Y %H:%M:%S %Z%z')))
                    # to_d = unix_time_millis(datetime.strptime(to_d, "%a %b %d %H:%M:%S %Y (%Z)"))
                    t_d = {'date': {'$lt': to_d}}
                    q_ar.append(t_d)
            q_ar.append(query_u)
            query = {"$and": q_ar}
            # query = {"$and": [{"userId": userid}, {"imageId": image_id}]}

            found = mongoClient['prediction'].find(query).skip(skip).limit(maximum)
            total = mongoClient['prediction'].count(query)
            f_ar = []
            for f in found:
                f_ar.append(json_util.dumps(f))
            resp = Response(json.dumps(f_ar))
            resp.headers['total'] = total
            resp.headers["Access-Control-Expose-Headers"] = '*'

            # found = mongoClient['prediction'].find(query_u).skip(skip).limit(maximum)
            # total = mongoClient['prediction'].count(query_u)
            # found_j = []
            # for f in found:
            #     found_j.append(json_util.dumps(f))
            # resp = Response(json.dumps(found_j), mimetype='application/json')
            # resp.headers["Access-Control-Expose-Headers"] = '*'
            # resp.headers["Access-Control-Allow-Headers"] = '*'
            resp.headers["total"] = total
            return resp
        elif id is not None:
            query = {"_id": ObjectId(id)}
            found = mongoClient['prediction'].find_one(query)
            resp = Response(json_util.dumps(found))
            resp.headers["Access-Control-Expose-Headers"] = '*'
            # resp.headers["Access-Control-Allow-Headers"] = '*'
            return resp
        # else:
        #     q_ar = []
        #     if age is not None:
        #         a = {'age': age}
        #         q_ar.append(a)
        #     if generation is not None:
        #         g = {'generation':generation}
        #         q_ar.append(g)
        #     if exposed is not None:
        #         ex = {'exposedAt': exposed}
        #         q_ar.append(ex)
        #     if control is not None:
        #         co = {'control', control}
        #         q_ar.append(co)
        #     if from_d is not None:
        #         f_d = {'from': {'$gt': from_d}}
        #         q_ar.append(f_d)
        #     if to_d is not None:
        #         t_d = {'from': {'$gt': to_d}}
        #         q_ar.append(t_d)
        #     query = {"$and": q_ar}
        #     # query = {"$and": [{"userId": userid}, {"imageId": image_id}]}
        #     found = mongoClient['prediction'].find(query)
        #     total = mongoClient['prediction'].count(query)
        #     f_ar = []
        #     for f in found:
        #         f_ar.append(json_util.dumps(f))
        #     resp = Response(json.dumps(f_ar))
        #     resp.headers['total'] = total
        #     resp.headers["Access-Control-Expose-Headers"] = '*'
        #     # resp.headers["Access-Control-Allow-Headers"] = '*'
        #     return resp

    @predictionNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    # @predictionNamespace.expect(fields=prediction_model)
    # @imageNamespace.model(models.Image)
    @predictionNamespace.param('id', 'id')
    @token_required
    def delete(self):
        args = parser.parse_args()
        id = args.get('id')
        token = request.headers['Authorization']
        token = token.split(" ")[1]
        userid = oidc.user_getfield('sub', token)
        pred = mongoClient['prediction'].find_one({'_id': ObjectId(id)})
        if pred is None:
            abort(400, 'Not found')
        if pred['userId'] == userid:
            mongoClient['prediction'].delete_one({'_id': ObjectId(id)})
            resp = Response({"deleted": 1})
            resp.headers["Access-Control-Expose-Headers"] = '*'
            return resp
        else:
            abort(403, 'No right to delete the prediction')
