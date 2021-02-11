from collections import namedtuple

Image = namedtuple('Image', {
    # '_id',
    'userId',
    'photo',
    'imageId',
    'control',
    'exposed',
    'exposedAt',
    'age',
    'generation',
    'mm',
    'pixels',
    'time',
    'type'
})

Image.__new__.__defaults__ = (None,) * len(Image._fields)

PredictionTask = namedtuple('Task', {
    'id',
    'userId',
    'date',
    'percentage',
    'comments',
    'predictionId',
    'error',
    'finishedWithError'
})

PredictionTask.__new__.__defaults__ = (None,) * len(Image._fields)

Prediction = namedtuple('Prediction', {
    'id'
    'userId',
    'imageId',
    'date',
    'control',
    'exposed',
    'exposedAt',
    'age',
    'generation',
    'measurementsPhotoId',
    'tailLength',
    'totalLength',
    'abdomenPhotoId',
    'heartPhotoId',
    'abdomen5',
    'abdomen3',
    'heart3'
})

Prediction.__new__.__defaults__ = (None,) * len(Image._fields)

# CanProceed = namedtuple('CanProceed', [
#     'userid',
#     'proceed'
# ])
#
# ErrorReport = namedtuple('ErrorReport', [
#     'message',
#     'status'
# ])


