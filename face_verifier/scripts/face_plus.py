import json
import requests
from mysite.settings import MEDIA_ROOT

#'image_file1': (MEDIA_ROOT + '/recognition/cropped/avatar_RfkOuJd.jpg', open(MEDIA_ROOT + '/recognition/cropped/avatar_RfkOuJd.jpg', 'rb')),
def get_face_plus(photo_first,photo_sec,keys):
    params = {
        'api_key': 'KAwADQ7Gsy4NzpHntT1uqkHwFoATumKU',
        'api_secret' : '0ShdzcQN3l6F8NB0VeYVi0IEa3n7ru_R',
    }

    try:
        files = {
            'image_file1': (keys[0], open(photo_first, 'rb')),
            'image_file2': (keys[1], open(photo_sec, 'rb'))
        }

        api_url = 'https://api-us.faceplusplus.com/facepp/v3/compare'

        r = requests.post(api_url, params, files=files)
        response = json.loads(r.text)
        x = response['confidence']
        if x > 70:
            return 'Совпадение'
        else:
            return 'Несовпадение'
    except:
        return "Ошибка!"