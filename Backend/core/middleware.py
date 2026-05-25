from django.conf import settings


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        policy = getattr(settings, 'CONTENT_SECURITY_POLICY', '')
        if not policy:
            return response
        report_only = getattr(settings, 'CONTENT_SECURITY_POLICY_REPORT_ONLY', False)
        header_name = 'Content-Security-Policy-Report-Only' if report_only else 'Content-Security-Policy'
        if header_name not in response:
            response[header_name] = policy
        return response
