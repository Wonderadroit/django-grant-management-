from django.http import JsonResponse

from .models import Grant


def grant_list(request):
    grants = Grant.objects.filter(is_open=True).values("id", "name", "description", "deadline")
    return JsonResponse({"grants": list(grants)})
