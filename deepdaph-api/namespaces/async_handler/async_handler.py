import requests
from bson import ObjectId
from globals.globals import mongoClient, minioClient, model_uris, image_path
from PIL import Image, ImageDraw
import os
import numpy as np
from multiprocessing import Queue, Process
import math
from help import randomString
import time


def handle_predictions(prediction, task):
    taskId = task.id
    predId = task.predictionId
    taskFound = mongoClient['task'].find_one({"_id": ObjectId(taskId)})
    predictionFound = mongoClient['prediction'].find_one({"_id": ObjectId(predId)})
    userid = taskFound['userId']
    imageid = predictionFound['imageId']
    onImage = mongoClient['image'].find_one({"$and": [{"userId": userid}, {"imageId": imageid}]})
    query_p = {"_id": ObjectId(predId)}

    date = int(round(time.time() * 1000))
    update_p = {"$set": {'control': onImage['control']
                , 'exposed': onImage['exposed']
                , 'exposedAt': onImage['exposedAt']
                , 'age': onImage['age']
                , 'generation': onImage['generation'], 'userId':userid, 'date':date}}
    mongoClient['prediction'].update_one(query_p, update_p)
    time_got = int(round(time.time() * 1000))
    update_t = {"$set": {"finished": False, 'predictionId':predId, 'time':time_got}}
    mongoClient['task'].update_one({"_id": ObjectId(taskId)}, update_t)
    # print("Task")
    # print(taskFound)
    # print("OnImage")
    # print(onImage)
    # print("Pρediction")
    # print(predictionFound)
    my_q0 = Queue()
    my_q1 = Queue()
    my_q2 = Queue()
    my_q3 = Queue()

    t1q = Queue()
    t2q = Queue()
    t3q = Queue()
    t4q = Queue()

    scale = {}
    photo_m = onImage['photo'].split("/")
    file = image_path['IMAGE_PATH'] + photo_m[1]
    minioClient.fget_object(photo_m[0], photo_m[1], image_path['IMAGE_PATH'] + photo_m[1])
    im = Image.open(image_path['IMAGE_PATH'] + photo_m[1])
    scale['pixels'] = onImage['pixels']
    scale['mm'] = onImage['mm']
    bucket_name = photo_m[0]
    userId = onImage['userId']
    if scale['mm'] == 'undefined' or scale['pixels'] == 'undefined':

        ar = np.array(im)
        p = Process(target=scale_f, args=(im, onImage, my_q0))
        p.start()

        p1 = Process(target=first_pred, args=(ar, my_q0, my_q1, my_q2, my_q3, t1q, t2q, t3q, t4q, task
                                              , predictionFound, bucket_name, photo_m[1]
                                              , userId))
        p1.daemon = True
        p1.start()
        p2 = Process(target=abdomen_3, args=(predictionFound, my_q1, t2q))
        p2.daemon = True
        p2.start()
        p3 = Process(target=abdomen_5, args=(predictionFound, my_q2, t3q))
        p3.daemon = True
        p3.start()
        p4 = Process(target=heart_3, args=(predictionFound, my_q3, t4q))
        p4.daemon = True
        p4.start()
        p5 = Process(target=task_process, args=(taskFound, predictionFound, t1q, t2q, t3q, t4q, p, p1, p2, p3, p4))
        p5.daemon = True
        p5.start()
        # p.join()
        # p1.join()
        # p2.join()
        # p3.join()
        # p4.join()
        p5.join()
    else:
        ar = np.array(im)
        p = Process(target=scale_f, args=(im, onImage, my_q0))
        p.start()
        p1 = Process(target=first_pred_with_scale, args=(ar, scale, my_q0, my_q1, my_q2, my_q3, t1q, t2q, t3q, t4q, task
                                              , predictionFound, bucket_name, photo_m[1]
                                              , userId))
        p1.daemon = True
        p1.start()
        p2 = Process(target=abdomen_3, args=( predictionFound, my_q1, t2q))
        p2.daemon = True
        p2.start()
        p3 = Process(target=abdomen_5, args=(predictionFound, my_q2, t3q))
        p3.daemon = True
        p3.start()
        p4 = Process(target=heart_3, args=(predictionFound, my_q3, t4q))
        p4.daemon = True
        p4.start()
        p5 = Process(target=task_process, args=(taskFound, predictionFound, t1q, t2q, t3q, t4q ,p, p1, p2, p3, p4))
        p5.daemon = True
        p5.start()
        p.join()
        # p1.join()
        # p2.join()
        # p3.join()
        # p4.join()
        p5.join()
    if os.path.exists(image_path['IMAGE_PATH'] + file):
        os.remove(image_path['IMAGE_PATH'] + file)


def scale_f(im, onImage, que):
    pixels = im.load()
    width, height = im.size
    coords = []
    scale = {}
    for x in range(width):
        for y in range(height):
            # if pixels[x, y] == (255, 0, 0):
            #     coords.append((x, y))
            if pixels[x, y][0] > 200 and pixels[x, y][1] < 80 and pixels[x, y][2] < 80:
                coords.append((x, y))
    if len(coords) > 2:
        min = coords[0][0] + 1
        max = coords[len(coords) - 1][0] - 1
        pix = max - min
        scale['pixels'] = pix
        scale['mm'] = 500
    try:
        onImage['pixels'] = scale['pixels']
        onImage['mm'] = scale['mm']
        onImage = update_image(onImage)
        que.put({'scale': scale})
    except KeyError:
        que.put("ERROR NO SCALE AVAILABLE")
    return


def update_image(image):
    query = {"_id": ObjectId(image['_id'])}
    update = {"$set": {"pixels": image['pixels'], "mm": image["mm"]}}
    mongoClient['image'].update_one(query, update)


def first_pred(ar, que, my_q1, my_q2, my_q3, t1q, t2q, t3q, t4q, task, predictionFound, bucket, imageName, user_id):
    payload = {"instances": [ar.tolist()]}
    res = requests.post(model_uris['daphobd'], json=payload)
    resp = res.json()
    im = Image.fromarray(ar)
    t1q.put("Starting predictions")
    while True:
        scale_cacl = que.get()
        if scale_cacl != "ERROR NO SCALE AVAILABLE":
            # scale_cacl['scale']
            pred_query = {"_id": ObjectId(predictionFound['_id'])}
            scale = scale_cacl['scale']
            for respon in resp['predictions']:
                if respon['num_detections'] > 1:
                    eye = []
                    head = []
                    heart = []
                    abdomen = []
                    tail = []
                    tail_tip = []
                    tail_base = []
                    i = 0
                    for clas in respon['detection_classes']:
                        if clas == 3:
                            eye.append(respon['detection_boxes'][i])
                        if clas == 2:
                            head.append(respon['detection_boxes'][i])
                        if clas == 4:
                            heart.append(respon['detection_boxes'][i])
                        if clas == 5:
                            abdomen.append(respon['detection_boxes'][i])
                        if clas == 6:
                            tail.append(respon['detection_boxes'][i])
                        if clas == 7:
                            tail_base.append(respon['detection_boxes'][i])
                        if clas == 8:
                            tail_tip.append(respon['detection_boxes'][i])
                        i += 1

                    im_width, im_height = im.size

                    if len(abdomen) > 0:
                        abdomen = abdomen[0]
                        abdomen = [int(abdomen[1] * im_width), int(abdomen[3] * im_width),
                                   int(abdomen[0] * im_height), int(abdomen[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((abdomen[0], abdomen[2], abdomen[1], abdomen[3]), outline=(180, 180, 180))
                        crop = (abdomen[0], abdomen[2], abdomen[1], abdomen[3])
                        cropped_abd = im.crop(crop)
                        name = imageName.split(".")[0] + "_abdomen" + ".jpeg"
                        abd_image = cropped_abd.save(image_path['IMAGE_PATH'] + name)
                        abd_image = image_path['IMAGE_PATH'] + name
                        minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
                        photoid = randomString(12)
                        image = {'userId': user_id, 'photo': bucket + "/" + name
                                             ,'imageId': photoid, 'type': 'Predicted'}
                        mongoClient['image'].insert_one(image)
                        update = {"$set": {'abdomenPhotoId': photoid}}
                        mongoClient['prediction'].update_one(pred_query, update)
                        my_q1.put({"abd_arr": np.asarray(cropped_abd)})
                        my_q2.put({"abd_arr": np.asarray(cropped_abd)})
                        os.remove( abd_image)
                        t2q.put("Abdomen 3 predictions")
                        t3q.put("Abdomen 5 predictions")
                    if len(abdomen) == 0:
                        t2q.put("No abdomen prediction")
                        t3q.put("No abdomen prediction")
                    if len(heart) > 0:
                        heart = heart[0]
                        heart = [int(heart[1] * im_width), int(heart[3] * im_width),
                                 int(heart[0] * im_height), int(heart[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((heart[0], heart[2], heart[1], heart[3]), outline=(20, 20, 20))
                        crop = (heart[0], heart[2], heart[1], heart[3])
                        cropped_h = im.crop(crop)
                        name = imageName.split(".")[0] + "_heart" + ".jpeg"
                        h_image = cropped_h.save(image_path['IMAGE_PATH'] + name)
                        h_image = image_path['IMAGE_PATH'] + name
                        minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
                        photoid = randomString(12)
                        image ={'userId':user_id, 'photo':bucket + "/" + name
                                             , 'imageId':photoid, 'type':'Predicted'}
                        mongoClient['image'].insert_one(image)
                        update = {"$set": {'heartPhotoId': photoid}}
                        mongoClient['prediction'].update_one(pred_query, update)
                        my_q3.put({"heart_arr": np.asarray(cropped_h)})
                        os.remove(h_image)
                        t4q.put("Heart prediction")
                        if len(heart) == 0:
                            t4q.put("No heart prediction")
                    if len(head) > 0:
                        head = head[0]
                        head = [int(head[1] * im_width), int(head[3] * im_width),
                                int(head[0] * im_height), int(head[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((head[0], head[2], head[1], head[3]), outline=(128, 0, 0))
                    if len(tail) > 0:
                        tail = tail[0]
                        tail = [int(tail[1] * im_width), int(tail[3] * im_width),
                                int(tail[0] * im_height), int(tail[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((tail[0], tail[2], tail[1], tail[3]), outline=(128, 128, 0))
                    if len(eye) > 0:
                        eye = eye[0]
                        eye = [int(eye[1] * im_width), int(eye[3] * im_width),
                               int(eye[0] * im_height), int(eye[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((eye[0], eye[2], eye[1], eye[3]), outline=(128, 128, 128))
                    if len(tail_base) > 0:
                        tail_base = tail_base[0]
                        tail_base = [int(tail_base[1] * im_width), int(tail_base[3] * im_width),
                                     int(tail_base[0] * im_height), int(tail_base[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((tail_base[0], tail_base[2], tail_base[1], tail_base[3]),
                                       outline=(240, 240, 240))
                    if len(tail_tip) > 0:
                        tail_tip = tail_tip[0]
                        tail_tip = [int(tail_tip[1] * im_width), int(tail_tip[3] * im_width),
                                    int(tail_tip[0] * im_height), int(tail_tip[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((tail_tip[0], tail_tip[2], tail_tip[1], tail_tip[3]), outline=(40, 40, 40))
                    if len(tail_tip) == 0:
                        t1q.put("No measurement predictions")
                    if len(tail_base) > 0 and len(tail_tip) > 0:
                        t1q.put("Tail measurements")
                        x1 = (tail_base[0] + tail_base[1])/2
                        y1 = (tail_base[2] + tail_base[3])/2
                        x2 = (tail_tip[0] + tail_tip[1])/2
                        y2 = (tail_tip[2] + tail_tip[3])/2
                        draw = ImageDraw.Draw(im)
                        draw.line([(x1, y1), (x2, y2)], fill=0)
                        if min != 0 and max != 0:
                            tail = math.sqrt(math.pow((x1-x2), 2) + math.pow((y1-y2), 2))
                            tail_length = (scale['mm'] * tail) / scale['pixels']
                            update = {"$set": {'tailLength': tail_length}}
                            mongoClient['prediction'].update_one(pred_query, update)
                    if len(tail_base) == 0 and len(tail_tip) == 0:
                        t1q.put("No tail measurement")
                    if len(tail_tip) > 0 and len(eye) > 0:
                        t1q.put("Total measurements")
                        x1 = (eye[0] + eye[1])/2
                        y1 =(eye[2] + eye[3])/2
                        x2 = (tail_tip[0] + tail_tip[1])/2
                        y2 =(tail_tip[2] + tail_tip[3])/2
                        draw = ImageDraw.Draw(im)
                        draw.line([(x1, y1), (x2, y2)], fill=255)
                        if min != 0 and max != 0:
                            size = math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2))
                            size_length = (scale['mm'] * size) / scale['pixels']
                            update = {"$set": {"mm": size_length}}
                            mongoClient['prediction'].update_one(pred_query, update)
                    if len(tail_tip) == 0 and len(eye) == 0:
                        t1q.put("No total measurement")

            name = imageName.split(".")[0] + "_predictions" + ".jpeg"
            pred_image = im.save(image_path['IMAGE_PATH'] + name)
            minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
            photoid = randomString(12)
            image = {'userId': user_id, 'photo': bucket + "/" + name
                    , 'imageId': photoid, 'type': 'Predicted'}
            mongoClient['image'].insert_one(image)
            minioClient.fput_object(bucket, name,image_path['IMAGE_PATH'] + name)
            update = {"$set": {'measurementsPhotoId': photoid}}
            mongoClient['prediction'].update_one(pred_query, update)
            if os.path.exists(image_path['IMAGE_PATH'] + name):
                os.remove(image_path['IMAGE_PATH'] + name)
            t1q.put("Finished")
        else:
            pred_query = {"_id": ObjectId(predictionFound['_id'])}
            for respon in resp['predictions']:
                if respon['num_detections'] > 1:
                    eye = []
                    head = []
                    heart = []
                    abdomen = []
                    tail = []
                    tail_tip = []
                    tail_base = []
                    i = 0
                    for clas in respon['detection_classes']:
                        if clas == 3:
                            eye.append(respon['detection_boxes'][i])
                        if clas == 2:
                            head.append(respon['detection_boxes'][i])
                        if clas == 4:
                            heart.append(respon['detection_boxes'][i])
                        if clas == 5:
                            abdomen.append(respon['detection_boxes'][i])
                        if clas == 6:
                            tail.append(respon['detection_boxes'][i])
                        if clas == 7:
                            tail_base.append(respon['detection_boxes'][i])
                        if clas == 8:
                            tail_tip.append(respon['detection_boxes'][i])
                        i += 1
                    im_width, im_height = im.size
                    if len(abdomen) > 0:
                        abdomen = abdomen[0]
                        abdomen = [int(abdomen[1] * im_width), int(abdomen[3] * im_width),
                                   int(abdomen[0] * im_height), int(abdomen[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((abdomen[0], abdomen[2], abdomen[1], abdomen[3]), outline=(180, 180, 180))
                        crop = (abdomen[0], abdomen[2], abdomen[1], abdomen[3])
                        cropped_abd = im.crop(crop)
                        name = imageName.split(".")[0] + "_abdomen" + ".jpeg"
                        abd_image = cropped_abd.save(image_path['IMAGE_PATH'] + name)
                        abd_image = image_path['IMAGE_PATH'] + name
                        minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
                        photoid = randomString(12)
                        image = {'userId': user_id, 'photo': bucket + "/" + name
                                             ,'imageId': photoid, 'type': 'Predicted'}
                        mongoClient['image'].insert_one(image)
                        update = {"$set": {'abdomenPhotoId': photoid}}
                        mongoClient['prediction'].update_one(pred_query, update)
                        my_q1.put({"abd_arr": np.asarray(cropped_abd)})
                        my_q2.put({"abd_arr": np.asarray(cropped_abd)})
                        os.remove(abd_image)
                        t2q.put("Abdomen 3 predictions")
                        t3q.put("Abdomen 5 predictions")
                    if len(abdomen) == 0:
                        t2q.put("No abdomen 3 class  prediction")
                        t3q.put("No abdomen 5 class prediction")
                    if len(heart) > 0:
                        heart = heart[0]
                        heart = [int(heart[1] * im_width), int(heart[3] * im_width),
                                 int(heart[0] * im_height), int(heart[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((heart[0], heart[2], heart[1], heart[3]), outline=(20, 20, 20))
                        crop = (heart[0], heart[2], heart[1], heart[3])
                        cropped_h = im.crop(crop)
                        name = imageName.split(".")[0] + "_heart" + ".jpeg"
                        h_image = cropped_h.save(image_path['IMAGE_PATH'] + name)
                        h_image = image_path['IMAGE_PATH'] + name
                        minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
                        photoid = randomString(12)
                        image ={'userId':user_id, 'photo':bucket + "/" + name
                                             , 'imageId':photoid, 'type':'Predicted'}
                        mongoClient['image'].insert_one(image)
                        update = {"$set": {'heartPhotoId': photoid}}
                        mongoClient['prediction'].update_one(pred_query, update)
                        my_q3.put({"heart_arr": np.asarray(cropped_h)})
                        os.remove(h_image)
                        t4q.put("Heart prediction")
                        if len(heart) == 0:
                            t4q.put("No heart prediction")
                    if len(head) > 0:
                        head = head[0]
                        head = [int(head[1] * im_width), int(head[3] * im_width),
                                int(head[0] * im_height), int(head[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((head[0], head[2], head[1], head[3]), outline=(128, 0, 0))
                    if len(tail) > 0:
                        tail = tail[0]
                        tail = [int(tail[1] * im_width), int(tail[3] * im_width),
                                int(tail[0] * im_height), int(tail[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((tail[0], tail[2], tail[1], tail[3]), outline=(128, 128, 0))
                    if len(eye) > 0:
                        eye = eye[0]
                        eye = [int(eye[1] * im_width), int(eye[3] * im_width),
                               int(eye[0] * im_height), int(eye[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((eye[0], eye[2], eye[1], eye[3]), outline=(128, 128, 128))
                    if len(tail_base) > 0:
                        tail_base = tail_base[0]
                        tail_base = [int(tail_base[1] * im_width), int(tail_base[3] * im_width),
                                     int(tail_base[0] * im_height), int(tail_base[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((tail_base[0], tail_base[2], tail_base[1], tail_base[3]),
                                       outline=(240, 240, 240))
                    if len(tail_tip) > 0:
                        tail_tip = tail_tip[0]
                        tail_tip = [int(tail_tip[1] * im_width), int(tail_tip[3] * im_width),
                                    int(tail_tip[0] * im_height), int(tail_tip[2] * im_height)]
                        draw = ImageDraw.Draw(im)
                        draw.rectangle((tail_tip[0], tail_tip[2], tail_tip[1], tail_tip[3]), outline=(40, 40, 40))
            name = imageName.split(".")[0] + "_predictions" + ".jpeg"
            pred_image = im.save(image_path['IMAGE_PATH'] + name)
            minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
            photoid = randomString(12)
            image = {'userId': user_id, 'photo': bucket + "/" + name
                    , 'imageId': photoid, 'type': 'Predicted'}
            mongoClient['image'].insert_one(image)
            minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
            update = {"$set": {'measurementsPhotoId': photoid}}
            mongoClient['prediction'].update_one(pred_query, update)
            if os.path.exists(image_path['IMAGE_PATH'] + name):
                try:
                    os.remove(image_path['IMAGE_PATH'] + name)
                except Exception:
                    continue
            t1q.put("No measurements. No scale on photo")
            t1q.put("Finished")


def abdomen_3(prediction, que, t2):
    q = que.get()
    im = Image.fromarray(q['abd_arr'])
    im = im.resize((128, 128))
    im = np.asarray(im)
    payload = {"instances": [im.tolist()]}
    res = requests.post(model_uris['abdomen3model'], json=payload)
    resp = res.json()
    try:
        preds = resp['predictions']
        pred = preds[0]
        pred_query = {"_id": ObjectId(prediction['_id'])}
        update = {"$set": {'abdomen3': pred}}
        mongoClient['prediction'].update_one(pred_query, update)
        t2.put("Abdomen 3 class predictions finished")
        t2.put("Finished")
    except Exception:
        t2.put("Could not generate predictions for abdomen 3")
        t2.put("Finished")
    return


def abdomen_5(prediction, que, t3):
    q = que.get()
    im = Image.fromarray(q['abd_arr'])
    im = im.resize((128, 128))
    im = np.asarray(im)
    payload = {"instances": [im.tolist()]}
    res = requests.post(model_uris['abdomen5model'], json=payload)
    try:
        resp = res.json()
        preds = resp['predictions']
        pred = preds[0]
        pred_query = {"_id": ObjectId(prediction['_id'])}
        update = {"$set": {'abdomen5': pred}}
        mongoClient['prediction'].update_one(pred_query, update)
        t3.put("Abdomen 5 class predictions finished")
        t3.put("Finished")
    except Exception:
        t3.put("Could not generate predictions for abdomen 5 class")
        t3.put("Finished")
    return


def heart_3(prediction, que, t4):
    q = que.get()
    im = Image.fromarray(q['heart_arr'])
    im = im.resize((128, 128))
    im = np.asarray(im)
    payload = {"instances": [im.tolist()]}
    res = requests.post(model_uris['heartmodel'], json=payload)
    resp = res.json()
    try:
        preds = resp['predictions']
        pred = preds[0]
        pred_query = {"_id": ObjectId(prediction['_id'])}
        update = {"$set": {'heart3': pred}}
        mongoClient['prediction'].update_one(pred_query, update)
        t4.put("Heart predictions finished")
        t4.put("Finished")
    except Exception:
        t4.put("Could not generate predictions for heart")
        t4.put("Finished")
    return


def first_pred_with_scale(ar, scale
                          , que, my_q1, my_q2, my_q3, t1q, t2q, t3q, t4q, task, predictionFound
                          , bucket, imageName, user_id):
    try:
        payload = {"instances": [ar.tolist()]}
        res = requests.post(model_uris['daphobd'], json=payload)
        resp = res.json()
        im = Image.fromarray(ar)
        pred_query = {"_id": ObjectId(predictionFound['_id'])}
        t1q.put("Starting prediction")
        for respon in resp['predictions']:
            if respon['num_detections'] > 1:
                eye = []
                head = []
                heart = []
                abdomen = []
                tail = []
                tail_tip = []
                tail_base = []
                i = 0
                for clas in respon['detection_classes']:
                    if clas == 3:
                        eye.append(respon['detection_boxes'][i])
                    if clas == 2:
                        head.append(respon['detection_boxes'][i])
                    if clas == 4:
                        heart.append(respon['detection_boxes'][i])
                    if clas == 5:
                        abdomen.append(respon['detection_boxes'][i])
                    if clas == 6:
                        tail.append(respon['detection_boxes'][i])
                    if clas == 7:
                        tail_base.append(respon['detection_boxes'][i])
                    if clas == 8:
                        tail_tip.append(respon['detection_boxes'][i])
                    i += 1

                im_width, im_height = im.size

                if len(abdomen) > 0:
                    abdomen = abdomen[0]
                    abdomen = [int(abdomen[1] * im_width), int(abdomen[3] * im_width),
                               int(abdomen[0] * im_height), int(abdomen[2] * im_height)]
                    draw = ImageDraw.Draw(im)
                    draw.rectangle((abdomen[0], abdomen[2], abdomen[1], abdomen[3]), outline=(180, 180, 180))
                    crop = (abdomen[0], abdomen[2], abdomen[1], abdomen[3])
                    cropped_abd = im.crop(crop)
                    name = imageName.split(".")[0] + "_abdomen" + ".jpeg"
                    abd_image = cropped_abd.save(image_path['IMAGE_PATH'] + name)
                    abd_image = image_path['IMAGE_PATH'] + name
                    minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
                    photoid = randomString(12)
                    image = {'userId': user_id, 'photo': bucket + "/" + name
                        , 'imageId': photoid, 'type': 'Predicted'}
                    mongoClient['image'].insert_one(image)
                    update = {"$set": {'abdomenPhotoId': photoid}}
                    mongoClient['prediction'].update_one(pred_query, update)
                    my_q1.put({"abd_arr": np.asarray(cropped_abd)})
                    my_q2.put({"abd_arr": np.asarray(cropped_abd)})
                    os.remove(abd_image)
                    t2q.put("Abdomen 3 predictions")
                    t3q.put("Abdomen 5 predictions")
                if len(abdomen) == 0:
                    t2q.put("No abdomen prediction")
                    t3q.put("No abdomen prediction")
                if len(heart) > 0:
                    heart = heart[0]
                    heart = [int(heart[1] * im_width), int(heart[3] * im_width),
                             int(heart[0] * im_height), int(heart[2] * im_height)]
                    draw = ImageDraw.Draw(im)
                    draw.rectangle((heart[0], heart[2], heart[1], heart[3]), outline=(20, 20, 20))
                    crop = (heart[0], heart[2], heart[1], heart[3])
                    cropped_h = im.crop(crop)
                    name = imageName.split(".")[0] + "_heart" + ".jpeg"
                    h_image = cropped_h.save(image_path['IMAGE_PATH'] + name)
                    h_image = image_path['IMAGE_PATH'] + name
                    minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
                    photoid = randomString(12)
                    image = {'userId': user_id, 'photo': bucket + "/" + name
                        , 'imageId': photoid, 'type': 'Predicted'}
                    mongoClient['image'].insert_one(image)
                    update = {"$set": {'heartPhotoId': photoid}}
                    mongoClient['prediction'].update_one(pred_query, update)
                    my_q3.put({"heart_arr": np.asarray(cropped_h)})
                    os.remove(h_image)
                    t4q.put("Heart prediction")
                    if len(heart) == 0:
                        t4q.put("No heart prediction")
                if len(head) > 0:
                    head = head[0]
                    head = [int(head[1] * im_width), int(head[3] * im_width),
                            int(head[0] * im_height), int(head[2] * im_height)]
                    draw = ImageDraw.Draw(im)
                    draw.rectangle((head[0], head[2], head[1], head[3]), outline=(128, 0, 0))
                if len(tail) > 0:
                    tail = tail[0]
                    tail = [int(tail[1] * im_width), int(tail[3] * im_width),
                            int(tail[0] * im_height), int(tail[2] * im_height)]
                    draw = ImageDraw.Draw(im)
                    draw.rectangle((tail[0], tail[2], tail[1], tail[3]), outline=(128, 128, 0))
                if len(eye) > 0:
                    eye = eye[0]
                    eye = [int(eye[1] * im_width), int(eye[3] * im_width),
                           int(eye[0] * im_height), int(eye[2] * im_height)]
                    draw = ImageDraw.Draw(im)
                    draw.rectangle((eye[0], eye[2], eye[1], eye[3]), outline=(128, 128, 128))
                if len(tail_base) > 0:
                    tail_base = tail_base[0]
                    tail_base = [int(tail_base[1] * im_width), int(tail_base[3] * im_width),
                                 int(tail_base[0] * im_height), int(tail_base[2] * im_height)]
                    draw = ImageDraw.Draw(im)
                    draw.rectangle((tail_base[0], tail_base[2], tail_base[1], tail_base[3]),
                                   outline=(240, 240, 240))
                if len(tail_tip) > 0:
                    tail_tip = tail_tip[0]
                    tail_tip = [int(tail_tip[1] * im_width), int(tail_tip[3] * im_width),
                                int(tail_tip[0] * im_height), int(tail_tip[2] * im_height)]
                    draw = ImageDraw.Draw(im)
                    draw.rectangle((tail_tip[0], tail_tip[2], tail_tip[1], tail_tip[3]), outline=(40, 40, 40))
                if len(tail_tip) == 0:
                    t1q.put("No measurement predictions")
                if len(tail_base) > 0 and len(tail_tip) > 0:
                    t1q.put("Tail measurements")
                    x1 = (tail_base[0] + tail_base[1]) / 2
                    y1 = (tail_base[2] + tail_base[3]) / 2
                    x2 = (tail_tip[0] + tail_tip[1]) / 2
                    y2 = (tail_tip[2] + tail_tip[3]) / 2
                    draw = ImageDraw.Draw(im)
                    draw.line([(x1, y1), (x2, y2)], fill=0)
                    if min != 0 and max != 0:
                        tail = math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2))
                        tail_length = (int(scale['mm']) * tail) / int(scale['pixels'])
                        update = {"$set": {'tailLength': tail_length}}
                        mongoClient['prediction'].update_one(pred_query, update)
                if len(tail_base) == 0 and len(tail_tip) == 0:
                    t1q.put("No tail measurement")
                if len(tail_tip) > 0 and len(eye) > 0:
                    t1q.put("Total measurements")
                    x1 = (eye[0] + eye[1]) / 2
                    y1 = (eye[2] + eye[3]) / 2
                    x2 = (tail_tip[0] + tail_tip[1]) / 2
                    y2 = (tail_tip[2] + tail_tip[3]) / 2
                    draw = ImageDraw.Draw(im)
                    draw.line([(x1, y1), (x2, y2)], fill=255)
                    if min != 0 and max != 0:
                        size = math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2))
                        size_length = (int(scale['mm']) * size) / int(scale['pixels'])
                        update = {"$set": {"mm": size_length}}
                        mongoClient['prediction'].update_one(pred_query, update)
                if len(tail_tip) == 0 and len(eye) == 0:
                    t1q.put("No total measurement")

        name = imageName.split(".")[0] + "_predictions" + ".jpeg"
        pred_image = im.save(image_path['IMAGE_PATH'] + name)
        minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
        photoid = randomString(12)
        image = {'userId': user_id, 'photo': bucket + "/" + name
            , 'imageId': photoid, 'type': 'Predicted'}
        mongoClient['image'].insert_one(image)
        minioClient.fput_object(bucket, name, image_path['IMAGE_PATH'] + name)
        update = {"$set": {'measurementsPhotoId': photoid}}
        mongoClient['prediction'].update_one(pred_query, update)
        if os.path.exists(image_path['IMAGE_PATH'] + name):
            os.remove(image_path['IMAGE_PATH'] + name)
        t1q.put("Finished")
    except Exception as e:
        t1q.put(str("Finished with error. Cannot create predictions "))
        t1q.put("Finished")


def task_process(task, pred_id, t1q, t2q, t3q, t4q, pm, p1, p2, p3, p4):
    # print(task)
    task_query = {"_id": ObjectId(task['_id'])}
    task_f = mongoClient['task'].find_one(task_query)
    p = True
    comments = []
    comments.append(task_f['comments'])
    t1f = False
    t2f = False
    t3f = False
    t4f = False
    while p:
        if t1f is False:
            t1m = t1q.get()
            if t1m != 'Finished':
                comments.append(t1m)
                update = {"$set": {"comments": comments}}
                mongoClient['task'].update_one(task_query, update)
            if t1m == 'Finished':
                t1f = True
        if t2f is False:
            t2m = t2q.get()
            if t2m != 'Finished':
                comments.append(t2m)
                update = {"$set": {"comments": comments}}
                mongoClient['task'].update_one(task_query, update)
            if t2m == 'Finished':
                t2f = True
        if t3f is False:
            t3m = t3q.get()
            if t3m != 'Finished':
                comments.append(t3m)
                update = {"$set": {"comments": comments}}
                mongoClient['task'].update_one(task_query, update)
            if t3m == 'Finished':
                t3f = True
        if t4f is False:
            t4m = t4q.get()
            if t4m != 'Finished':
                comments.append(t4m)
                update = {"$set": {"comments": comments}}
                mongoClient['task'].update_one(task_query, update)
            if t4m == 'Finished':
                t4f = True
        if t1f and t2f and t3f and t4f:
            comments.append('Finished')
            update = {"$set": {"finished": True, "comments": comments}}
            mongoClient['task'].update_one(task_query, update)
            p = False
            break
    return
# def measurements():



