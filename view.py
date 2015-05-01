from django.http import HttpResponse, HttpResponseForbidden
from django.core.context_processors import csrf

from oauth_helper import verify_oauth_with_params

SITE_URL = 'https://www.example.com'

CONSUMERS = {
   'consumer123': 'secret123'
}

def get_consumer_secret(consumer_key):
   return CONSUMERS.get(consumer_key, None)

@csrf_exempt
def provider(request):
   if request.method != 'POST':
      return HttpResponse('LTI provider for POST requests')

   post_params = dict(request.POST.iteritems())

   if 'oauth_consumer_key' not in post_params:
      return HttpResponseForbidden('No consumer key specified.')

   consumer_key = post_params.get('oauth_consumer_key', None)
   consumer_secret = get_consumer_secret(consumer_key)

   if consumer_secret is None:
      return HttpResponseForbidden('Unknown LTI consumer: ' + consumer_key)

   if SITE_URL:
      # Make our own URL
      url = SITE_URL + request.path
   else:
      # Requires up-to-date Django, with 
      # HTTP_X_FORWARDED_PROTOCOL set
      # by the reverse proxy
      url = request.build_absolute_uri()
   
   try:
      is_valid = verify_oauth_with_params(
         consumer_key,
         consumer_secret,
         url,
         post_params
      )
   except OAuthInvalidError as err:
      return HttpResponseForbidden(str(err))

   if is_valid:
      return HttpResponse('All good. You are verified as: ' + post_params.get('user_id', 'no user provided'))
   else:
      return HttpResponse("Nup. Didn't work for " + consumer_key + " on " + url)

