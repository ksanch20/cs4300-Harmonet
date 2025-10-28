from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages


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
        else:
            messages.error(request, "Invalid username or password")
            
    form = AuthenticationForm()
    return render(request, 'user/login.html', {'form': form, 'title':'log in'})


@login_required
def dashboard(request):
    return render(request, 'user/dashboard.html', {'title': 'Dashboard'})

# ---------------- Logout -----------------
def user_logout(request):
    auth_logout(request)
    return redirect('index')




def profile(request):
    return render(request, 'user/profile.html', {'title': 'profile'})

def analytics(request):
    return render(request, 'user/analytics.html', {'title': 'analytics'})

def AI_Recommendation(request):
    return render(request, 'user/AI_Recommendation.html', {'title': 'AI_Recommendation'})



# Add this function to your views.py
@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update the session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Your password was successfully updated!')
            return redirect('password_change')  # Redirect to same page to show message
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'user/password_change.html', {
        'form': form,
        'title': 'Change Password'
    })

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        auth_logout(request) #Log user out
        user.delete() #Delete user account
        return redirect('index') #Redirect user to home page
    return redirect('profile') 