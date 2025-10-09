from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required


#################### index ####################################### 
def index(request):
    return render(request, 'index.html', {'title':'index'})

########### register here ##################################### 
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')

            # Automatically log the user in after signup (optional)
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'user/register.html', {'form': form, 'title':'register here'})

################ login forms ################################################### 
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
            
    form = AuthenticationForm()
    return render(request, 'user/login.html', {'form': form, 'title':'log in'})


@login_required
def dashboard(request):
    return render(request, 'user/dashboard.html', {'title': 'Dashboard'})

# ---------------- Logout -----------------
def user_logout(request):
    auth_logout(request)
    return redirect('index')