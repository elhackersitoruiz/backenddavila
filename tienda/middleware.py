from django.conf import settings
from django.http import HttpResponse, Http404
import mimetypes
import os

class MediaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(settings.MEDIA_URL):
            media_path = os.path.join(settings.MEDIA_ROOT, request.path.replace(settings.MEDIA_URL, "", 1))
            if os.path.exists(media_path):
                mime_type, _ = mimetypes.guess_type(media_path)
                with open(media_path, "rb") as f:
                    return HttpResponse(f.read(), content_type=mime_type)
            raise Http404
        return self.get_response(request)
