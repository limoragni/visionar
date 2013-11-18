from django.shortcuts import render
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.template  import RequestContext
from django.contrib.auth.models import User
from .models import External
from editor.models import Project, Media, Mediatype
from django.core.context_processors import csrf

def loginview(request):
    if request.user.is_authenticated():
        return redirect('/users/profile')
    else:
        return render(request, 'users/login.html')
    

def auth_and_login(request, onsuccess='/create', onfail="/users/login/"):
    user = authenticate(username=request.POST['username'], password=request.POST['password'])
    if user is not None:
        login(request, user)
        return redirect(onsuccess)
    else:
        return redirect(onfail)  

def create_user(username, email, password, first_name, last_name, company, phone):
	user = User(username=username, email=email, first_name=first_name, last_name=last_name)
	user.set_password(password)
	user.save()
	external = External(user=user ,company=company, phone=phone)
	external.save()
	return user

def user_exists(username):
    user_count = User.objects.filter(username=username).count()
    if user_count == 0:
        return False
    return True

def signup(request):
    post = request.POST
    if not user_exists(post['username']): 
        user = create_user(username=post['username'], email=post['email'], password=post['password'], first_name = post['first_name'], last_name = post['last_name'], company = post['company'], phone=post['phone'])
    	return auth_and_login(request)
    else:
    	return redirect("/users/login/")

def logoutview(request):
    logout(request)
    return redirect("/users/login/")

@login_required(login_url='/users/login/')
def profile(request):
    return render(request, "users/profile.html")

@login_required(login_url='/users/login/')
def video(request):
    projects = Project.objects.filter(user= request.user)
    return render(request, "users/video.html", {"projects": projects})


