from django.http import HttpResponsePermanentRedirect

class CanonicalHostMiddleware:
    """
    - Fuerza host canónico (sin www)
    - (Opcional) fuerza https si el request llega en http (en Render suele venir ya como https)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()  # puede incluir puerto
        hostname = host.split(":")[0].lower()

        # NO tocar staging onrender
        if hostname.endswith("onrender.com"):
            return self.get_response(request)

        # Forzar sin www
        if hostname == "www.destinosposibles.com":
            new_url = f"https://destinosposibles.com{request.get_full_path()}"
            return HttpResponsePermanentRedirect(new_url)

        return self.get_response(request)