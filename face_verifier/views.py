import itertools
import json

from actstream import action
from django.contrib.auth.decorators import permission_required, login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import render

from face_verifier.scripts.face_cut import get_faces, compare_faces
from face_verifier.scripts.face_plus import get_face_plus
from face_verifier.scripts.findclone_api.vk_faces import get_vk_matched

import logging

logger = logging.getLogger('Findclone')
logger.setLevel(logging.INFO)
fh = logging.FileHandler("media/findclone_log.txt")
fh.setLevel(logging.INFO)
formatter = logging.Formatter(
    '#######################################################################################\n%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


@permission_required('website.comparing')
@login_required(login_url='/login/')
def face_cut(request):
    fs = FileSystemStorage(location='media/recognition/cropped')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        try:
            dict_path = json.loads(request.POST.get('vk_data'))

            action.send(request.user, verb='Распознавание фото - findclone')

            path = dict_path['vk_path']

            try:
                data = get_vk_matched(path)
                if not data:
                    raise Exception

                try:
                    if data['no_money']:
                        return HttpResponse(data['no_money'], status=400)
                    else:
                        pass
                except:
                    pass
            except:
                return HttpResponse('Совпадений по фото не найдено!', status=400)
            return HttpResponse(json.dumps(data), content_type="application/json")
        except:
            pass

        try:
            dict_paths = json.loads(request.POST.get('data'))
            if len(dict_paths) < 2:
                return HttpResponse('Недостаточно фото для сравнения!', status=400)

            action.send(request.user, verb='Распознавание фото - Проверка выбранных фото')

            pairs = list(map(dict, itertools.combinations(dict_paths.items(), 2)))

            result = ''
            path = []
            keys = []

            for pair in pairs:
                for part in pair:
                    path.append(pair[part])
                    keys.append(part)
                result = result + 'Результат-1: Фото ' + keys[0] + ' и фото ' + keys[1] + ': ' \
                         + compare_faces(path[0], path[1], keys) + '\n'

                result = result + 'Результат-2: Фото ' + keys[0] + ' и фото ' + keys[1] + ': ' \
                         + get_face_plus(path[0], path[1], keys) + '\n'
                path = []
                keys = []
            return HttpResponse(result[:-1])
        except:
            pass

        try:
            file = request.FILES['avatar']
            action.send(request.user, verb='Распознавание фото - Обрезать фото')
            file_name = fs.save(file.name, file)
            file_path = fs.path(file_name)
            response_data = {}
            response_data['path_0'] = file_path[file_path.find('media') - 1:]
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        except:
            pass

        try:
            try:
                file_first = request.FILES['first_pic']
                file_name_fisrt = fs.save(file_first.name, file_first)
                path_first = fs.path(file_name_fisrt)

                result_1 = get_faces('1', path_first)
            except:
                result_1 = []

            try:
                file_second = request.FILES['second_pic']
                file_name_second = fs.save(file_second.name, file_second)
                path_second = fs.path(file_name_second)
                result_2 = get_faces('2', path_second)
            except:
                result_2 = []

            action.send(request.user, verb='Распознавание фото - Определить')

            result = result_1 + result_2

            response_data = {}
            i = 0
            if result:
                for path in result:
                    response_data['path_' + str(i)] = path[path.find('media') - 1:]
                    i = i + 1
            else:
                return HttpResponse('Фото не были определены!', status=400)

            return HttpResponse(json.dumps(response_data), content_type="application/json")
        except:
            pass
        action.send(request.user, verb='Распознавание фото - ошибка')
        return HttpResponse('Что-то пошло не так!', status=400)
    else:
        action.send(request.user, verb='переход в Распознавание фото')
        return render(request, 'face_cut.html')


@permission_required('website.comparing')
@login_required(login_url='/login/')
def findclone(request):
    fs = FileSystemStorage(location='media/recognition/cropped')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        try:
            file = request.FILES['avatar']
            action.send(request.user, verb='Распознавание фото - Обрезать фото')
            file_name = fs.save(file.name, file)
            file_path = fs.path(file_name)

            try:
                data = get_vk_matched(file_path)
                if not data:
                    raise Exception

                try:
                    if data['no_money']:
                        return HttpResponse(data['no_money'], status=400)
                    else:
                        pass
                except:
                    pass
            except Exception as e:
                logger.error(e)
                return HttpResponse('Совпадений по фото не найдено!', status=400)
            return HttpResponse(json.dumps(data), content_type="application/json")
        except Exception as e:
            logger.error(e)
            pass
        return HttpResponse('Что-то пошло не так!', status=400)
    else:
        action.send(request.user, verb='переход в findclone')
        return render(request, 'findclone.html')
