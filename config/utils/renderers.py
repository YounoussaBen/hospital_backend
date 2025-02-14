from rest_framework.renderers import JSONRenderer

class CustomJSONRenderer(JSONRenderer):
    """
    Custom renderer to wrap the response in a consistent format.
    """
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_data = {
            'status': renderer_context['response'].status_code if renderer_context else 200,
            'data': data
        }
        return super().render(response_data, accepted_media_type, renderer_context)