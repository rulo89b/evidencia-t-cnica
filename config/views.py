
from django.conf import settings
from django.http import FileResponse
from django.views.decorators.http import require_GET


@require_GET
def service_worker(request):
    file_path = (
        settings.BASE_DIR
        / "static"
        / "service-worker.js"
    )

    response = FileResponse(
        open(file_path, "rb"),
        content_type="application/javascript",
    )

    response["Cache-Control"] = "no-cache"

    return response
