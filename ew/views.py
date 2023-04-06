from django.shortcuts import render

# Create your views here.
def my_view(request):
    return render(request, 'WebsiteDesign/MainPage.html')
def results(request):
    return render(request, 'WebsiteDesign/Results.html')
