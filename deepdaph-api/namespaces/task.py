from flask_restplus import Namespace, Resource
from flask import request
from flask_restplus import reqparse, fields
from flask import Response
from globals.globals import oidc, mongoClient
from functools import wraps
from bson import json_util, ObjectId


taskNamespace = Namespace('task')

parser = reqparse.RequestParser()
parser.add_argument('skip', type=int, help='skip tasks')
parser.add_argument('maximum', type=int, help='maximum tasks returned')
parser.add_argument('id', type=str, help='task id')

task_model = taskNamespace.model('Task', {
    'taskId': fields.String(description="Tasks id"),
    'userId': fields.String(description='users id'),
    'date': fields.Integer(description='Date of thetask'),
    'percentage': fields.Float(description='Percentage completed'),
    'comments': fields.Arbitrary(description='Comments on the Taks'),
    'predictionId': fields.String(description='Prediction Id when completed'),
    'error': fields.String(description='Error if Task completed with Error'),
    'finishedWithError': fields.Boolean(description='Finished with error or not')
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


@taskNamespace.route('/', methods=['POST', 'PUT', 'GET', 'DELETE'])
class MainClass(Resource):

    @taskNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    # @taskNamespace.model(task_model)
    @taskNamespace.param('id', 'id')
    @token_required
    # @taskNamespace.marshal_with(task_model, as_list=True)
    def get(self,):
        args = parser.parse_args()
        id = args.get('id')
        skip = args.get('skip')
        maximum = args.get('maximum')
        if skip is None:
            skip = 0
        if maximum is None:
            maximum = 20
        token = request.headers['Authorization']
        token = token.split(" ")[1]
        userid = oidc.user_getfield('sub', token)
        if id is None:
            query = {"userId": userid}
            tasks_c = mongoClient['task'].find(query).skip(skip).limit(maximum)
            total = mongoClient['task'].count(query)
            tasks = []
            for t in tasks_c:
                tasks.append(json_util.dumps(t))
            resp = Response(tasks)
            resp.headers["Access-Control-Expose-Headers"] = '*'
            resp.headers["Access-Control-Expose-Headers"] = total
            return resp
        else:
            query = {"_id": ObjectId(id)}
            task = mongoClient['task'].find_one(query)
            resp = Response(json_util.dumps(task))
            resp.headers["Access-Control-Expose-Headers"] = '*'
            return resp

    @taskNamespace.doc(responses={200: 'OK', 400: 'Bad request', 500: 'Server Error'}, security='Bearer')
    @taskNamespace.expect(task_model)
    # @imageNamespace.model(models.Image)
    @token_required
    def delete(self):
        token = request.headers['Authorization']
        token = token.split(" ")[1]
        userid = oidc.user_getfield('sub', token)
        resp = Response({"deleted": 1})
        resp.headers["Access-Control-Expose-Headers"] = '*'
        return resp