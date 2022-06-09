from actstream import action
from django.shortcuts import render
from .forms import UserForm
from django.http import HttpResponse
from django.contrib import messages
from .get_graph import FindLinks
from .get_graph import GetInfo

def search(request):
    if request.method == "POST":
        action.send(request.user, verb='графы - send')
        peoplemain_id = request.POST.get("id")
        lvl = int(request.POST.get("levels"))
        check_phone = request.POST.get("check_phone")
        check_card = request.POST.get("check_card")
        check_ip = request.POST.get("check_ip")
        check_email = request.POST.get("check_email")
        path = FindLinks(peoplemain_id, lvl,check_phone,check_card,check_ip,check_email)
        if(path == 'Error'):
            messages.info(request, 'Не удалось построить граф. Попробуйте изменить исходные данные.')
            userform = UserForm()
            return render(request, "sigma/search.html", {"form": userform})
        else:
            context = {'filepath': path}
            return render(request, 'sigma/main.html', context)
    else:
        action.send(request.user, verb='переход в графы')
        userform = UserForm()
        return render(request, "sigma/search.html", {"form": userform})



def node_info(request):
    node_id = request.POST['node_id'] #
    response = GetInfo(node_id)
    ## Send the response

    return HttpResponse(response)