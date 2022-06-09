from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required(login_url='/login/')
def redirect_view(request):
    return redirect('/profile')


def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    return render(request, 'errors/50x.html', status=500)
