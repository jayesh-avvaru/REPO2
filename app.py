import json
import sys

from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

settings.configure(
    DEBUG=True,
    SECRET_KEY="dev-only-secret",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    MIDDLEWARE=[],
)

# ---------- In-memory "database" ----------
db = {}
next_id = 1

FIELDS = ("name", "description", "price")


def read_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None


# ---------- CREATE + READ (all) ----------
@csrf_exempt
def items(request):
    global next_id

    if request.method == "GET":
        return JsonResponse(list(db.values()), safe=False)

    if request.method == "POST":
        data = read_json(request)
        if not data or "name" not in data or "price" not in data:
            return JsonResponse({"detail": "name and price are required"}, status=400)
        item = {
            "id": next_id,
            "name": data["name"],
            "description": data.get("description"),
            "price": data["price"],
        }
        db[next_id] = item
        next_id += 1
        return JsonResponse(item, status=201)

    return HttpResponse(status=405)


# ---------- READ (one) + UPDATE + DELETE ----------
@csrf_exempt
def item_detail(request, item_id):
    item = db.get(item_id)
    if item is None:
        return JsonResponse({"detail": "Item not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(item)

    if request.method == "PUT":
        data = read_json(request)
        if data is None:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)
        item.update({k: data[k] for k in FIELDS if k in data})
        return JsonResponse(item)

    if request.method == "DELETE":
        del db[item_id]
        return HttpResponse(status=204)

    return HttpResponse(status=405)


urlpatterns = [
    path("items", items),
    path("items/<int:item_id>", item_detail),
]

if __name__ == "__main__":
    execute_from_command_line(sys.argv)

# Run:  pip install django
#       python app.py runserver 8000 --noreload
