from django.shortcuts import render, get_object_or_404 as go404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from .models import Problem, Code, Upvote, Hint, HintUpvote
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import oj
# Create your views here.


class SearchForm(forms.Form):

    oj_id = forms.IntegerField(label='Problem ID', widget=forms.TextInput)


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


def about(request):
    return render(request, 'about.html')

def history(request):
    return render(request, 'history.html')


def problem(request, oj_id):
    problem, created = Problem.objects.get_or_create(oj_id=oj_id)
    if (
        request.user.is_authenticated() and
        Code.objects.filter(problem=problem, user=request.user).exists()
    ):
        shared = True
        hinted = Hint.objects.filter(problem=problem, user=request.user).exists()
    else:
        shared = False
        hinted = False
    code_list = Code.objects.filter(problem=problem).order_by('-upvotes', 'pk')
    hint_list = Hint.objects.filter(problem=problem).order_by('-upvotes', 'pk')

    # pagination
    paginator = Paginator(code_list, 10) # Show 25 contacts per page
    page = request.GET.get('page')
    try:
        code_list_pagination = paginator.page(page)
    except PageNotAnInteger:
        if(page=='last'):
            code_list_pagination = paginator.page(paginator.num_pages)
        else:
            code_list_pagination = paginator.page(1)
    except EmptyPage:
        code_list_pagination = paginator.page(paginator.num_pages)

    return render(
        request,
        'problem.html',
        {
            'problem': problem,
            'problem_id': oj_id,
            'shared': shared,
            'hinted': hinted,
            'code_list_count': code_list.count(),
            'code_list_pagination': code_list_pagination,
            'hint_list': hint_list,
            'hint_form': HintForm()
        }
    )


@login_required
def problem_share(request, oj_id):
    problem = go404(Problem, oj_id=oj_id)
    try:
        thecodeitself = oj.fetch_ac_code(request.user.username, request.session['password'], oj_id)
    except oj.YouNoAc:
        messages.warning(request, "You have not AC'd this problem.")
        return redirect(problem)
    code, created = Code.objects.get_or_create(problem=problem, user=request.user)
    code.text = thecodeitself
    code.save()
    messages.info(request, 'Successfully shared code of problem {}'.format(oj_id))
    return redirect(problem)


@login_required
def code_upvote(request, pk):
    code = go404(Code, pk=pk)
    upvote, created = Upvote.objects.get_or_create(user=request.user, code=code)
    if created:
        code.upvotes += 1
        code.save()
        messages.info(request, "upvoted #{}".format(pk))
    else:
        messages.warning(request, "You've upvoted this already!")
    return redirect(code.problem)


class HintForm(forms.Form):

    hint = forms.CharField(widget=forms.Textarea)


@login_required
@require_POST
def hint_share(request, oj_id):
    problem = go404(Problem, oj_id=oj_id)
    if not Code.objects.filter(problem=problem, user=request.user).exists():
        messages.warning(request, "You cannot share a hint until you share your AC code")
        return redirect(problem)
    form = HintForm(request.POST)
    if form.is_valid():
        hint, created = Hint.objects.get_or_create(user=request.user, problem=problem)
        hint.text = form.cleaned_data['hint']
        hint.save()
    else:
        messages.error(request, 'invalid input.')
    return redirect(problem)


@login_required
def hint_upvote(request, pk):
    hint = go404(Hint, pk=pk)
    upvote, created = HintUpvote.objects.get_or_create(user=request.user, hint=hint)
    if created:
        hint.upvotes += 1
        hint.save()
        messages.info(request, "upvoted #{}".format(pk))
    else:
        messages.warning(request, "You've upvoted this already!")
    return redirect(hint.problem)
