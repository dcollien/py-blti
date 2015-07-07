from django.http import HttpResponse
from blti import lti_provider, set_lti_properties

def do_login(request, params):
	pass # TODO: log request.user in using verified params

set_lti_properties(
	consumer_lookup = {
		'test_consumer': 'test_secret123'
	},
	site_url = 'https://www.example.com',
	login_func = do_login,
	require_post = True,
	#error_func = some_error_callable
)

@lti_provider
def provider_view(request):
	if request.method == 'POST':
		return HttpResponse("User verified")
	else:
		# should never happen, as require_post is set to True
		return HttpResponse("This is a LTI provider, make a POST request.")