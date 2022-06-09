#*- coding: utf-8 -*-
from PIL import Image
from . my_cropper import Cropper

import face_recognition

import logging

logger = logging.getLogger('logs')
logger.setLevel(logging.INFO)
fh = logging.FileHandler("face_verifier/scripts/log.txt")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('#######################################################################################\n%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# python3 /srv/project/ganymede/face_verifier/scripts/face_cut.py
# /srv/project/ganymede/media/recognition/cropped/firt_pic_OXdaFas_first.jpg
def compare_faces(photo_first, photo_sec, keys):
    try:
        known_image = face_recognition.load_image_file(photo_first)
    except:
        return 'Ошибка загрузки ' +keys[0] + ' фото!'

    try:
        unknown_image = face_recognition.load_image_file(photo_sec)
    except:
        return 'Ошибка загрузки ' + keys[1] + ' фото!'

    try:
        one_encoding = face_recognition.face_encodings(known_image)[0]
    except Exception as e:
        return 'Фото ' +keys[0] + ' не было распознано!'
    try:
        another_encoding = face_recognition.face_encodings(unknown_image)[0]
    except Exception as e:
        return 'Фото ' +keys[1] + ' не было распознано!'

    try:
        results = face_recognition.compare_faces([one_encoding], another_encoding)
    except Exception as e:
        return 'Не удается сравнить фото!'

    #try:
    #    face_distances = face_recognition.face_distance([another_encoding], one_encoding)
    #except Exception as e:
    #    return 'Не удается получить рейтинг фото!'
    if(results[0]):
        str_res = 'Совпадение'
    else:
        str_res = 'Несовпадение'

    return str_res #+ ', уверенность = ' + str(face_distances[0])

def cropper_devider(path):
    name = path.replace('.jpg', '')
    cropper = Cropper()
    cropped_tuple = cropper.crop(path)

    path_list = []
    try:
        for face_id in range(len(cropped_tuple[0])):
            cropped_array = cropper.cropping(
                cropped_tuple[0],
                cropped_tuple[1],
                cropped_tuple[2],
                cropped_tuple[3],
                cropped_tuple[4],
                face_id
            )
            cropped_image = Image.fromarray(cropped_array)

            if face_id == 0:
                type_id = "first"
            else:
                type_id = "second"
            cropped_image.save(name + '_{}.jpg'.format(type_id))
            path_list.append(name + '_{}.jpg'.format(type_id))
    except TypeError:
        print('No faces were found')
        pass
    return path_list

def get_faces(path_first, path_sec):
    try:
        first_getted = cropper_devider(path_first)[::-1]  # self (2)
        len_first_getted = len(first_getted)
        res = ' len=' + str(len_first_getted)
    except Exception as e:
        return '1', '1' + str(e)

    try:
        sec_getted = cropper_devider(path_sec)[::-1]  # doc (1)
        len_sec_getted = len(sec_getted)
        res = res + ', ' + ' len=' + str(len_sec_getted)
        full_list = first_getted + sec_getted
    except Exception as e:
        return '2', '2' + str(e)

    return res, full_list