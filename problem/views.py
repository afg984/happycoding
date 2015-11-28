from django.shortcuts import render, get_object_or_404 as go404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from .models import Problem, Code
import oj
# Create your views here.


class SearchForm(forms.Form):

    oj_id = forms.IntegerField(label='Online Judge ID', widget=forms.TextInput)


def index(request):
    if request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            try:
                problem = Problem.objects.get(**form.cleaned_data)
            except Problem.DoesNotExist:
                if oj.test_problem_existence(form.cleaned_data['oj_id']):
                    return redirect('problem:problem', oj_id=form.cleaned_data['oj_id'])
                messages.warning(request, 'The problem id={} does not exist'.format(form.cleaned_data['oj_id']))
            else:
                return redirect(problem)
    else:
        form  = SearchForm()
    return render(
        request,
        'index.html',
        {
            'form': form
        }
    )


def problem(request, oj_id):
    problem, created = Problem.objects.get_or_create(oj_id=oj_id)
    if (
        request.user.is_authenticated() and
        Code.objects.filter(problem=problem, user=request.user).exists()
    ):
        shared = True
    else:
        shared = False
    code_list = Code.objects.filter(problem=problem)
    return render(
        request,
        'problem.html',
        {
            'problem': problem,
            'problem_id': oj_id,
            'shared': shared,
            'code_list': code_list
        }
    )


@login_required
def problem_share(request, oj_id):
    problem = go404(Problem, oj_id=oj_id)
    thecodeitself = oj.fetch_ac_code(request.user.username, request.session['password'], oj_id)
    code, created = Code.objects.get_or_create(problem=problem, user=request.user)
    code.text = thecodeitself
    code.save()
    messages.info(request, 'Successfully shared code of problem {}'.format(oj_id))
    return redirect(problem)
