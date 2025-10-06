from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm

def signup(request):
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('grants:apply')  # redirect to grant application page
		# If form is invalid, fall through to render with errors
	else:
		form = SignUpForm()
	return render(request, 'accounts/signup.html', {'form': form})
from django.shortcuts import render

# Create your views here.
