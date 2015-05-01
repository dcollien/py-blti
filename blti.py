from django.http import HttpResponse, HttpResponseForbidden

from oauth_helper import verify_oauth_with_params

from functools import partial, wraps

import oauth2 as oauth

class OAuthInvalidError(Exception):
   pass

def sign_oauth_with_params(consumer_key, consumer_secret, url, parameters, method='POST'):
   consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
   oauth_request = oauth.Request(method=method, url=url, parameters=parameters)
   hmac = oauth.SignatureMethod_HMAC_SHA1()
   oauth_request.sign_request(hmac, consumer, None)

   return oauth_request

def verify_oauth_with_params(consumer_key, consumer_secret, url, parameters, method='POST'):
   oauth_request = oauth.Request(method=method, url=url, parameters=parameters)
   signature_method = oauth.SignatureMethod_HMAC_SHA1()
   oauth_consumer = oauth.Consumer(consumer_key, consumer_secret)

   try:
      signature = oauth_request.get_parameter('oauth_signature')
   except:
      raise OAuthInvalidError("missing OAuth signature")

   is_valid = signature_method.check(oauth_request, oauth_consumer, None, signature)

   return is_valid

LTI_PROPS = {}

def set_lti_properties(consumer_lookup=None, site_url=None, login_func=None, require_post=None, error_func=None):
   global LTI_PROPS
   
   if consumer_lookup is not None:
      LTI_PROPS['consumer_lookup'] = consumer_lookup
   if site_url is not None:
      LTI_PROPS['site_url'] = site_url
   if login_func is not None:
      LTI_PROPS['login_func'] = login_func
   if require_post is not None:
      LTI_PROPS['require_post'] = require_post
   if error_func is not None:
      LTI_PROPS['error_func'] = error_func

def lti_provider(func=None, consumer_lookup=None, site_url=None, login_func=None, require_post=None, error_func=None):
   if func is None:
      return partial(
         lti_provider, 
         consumer_lookup=consumer_lookup, 
         site_url=site_url, 
         login_func=login_func,
         require_post=require_post,
         error_func=error_func
      )

   # Set defaults
   if consumer_lookup is None:
      consumer_lookup = LTI_PROPS.get('consumer_lookup', {})
   if site_url is None:
      site_url = LTI_PROPS.get('site_url', None)
   if login_func is None:
      login_func = LTI_PROPS.get('login_func', None)
   if require_post is None:
      require_post = LTI_PROPS.get('require_post', True)
   if error_func is None:
      error_func = LTI_PROPS.get('error_func', error_func)

   @wraps(func)
   def provider(request, *args, **kwargs):
      if request.method != 'POST':
         if require_post:
            return error_func('LTI: a POST request is required')
         else:
            return func(request, *args, **kwargs)

      post_params = dict(request.POST.iteritems())

      consumer_key = post_params.get('oauth_consumer_key', None)

      if 'oauth_consumer_key' is None:
         return error_func('LTI: no consumer key provided')
      
      consumer_secret = consumer_lookup.get(consumer_key, None)

      if consumer_secret is None:
         return error_func('LTI: unknown consumer ' + consumer_key)

      if site_url:
         url = site_url + request.path
      else:
         url = request.build_absolute_uri()

      try:
         is_valid = verify_oauth_with_params(
            consumer_key,
            consumer_secret,
            url,
            post_params
         )
      except OAuthInvalidError as err:
         return error_func("LTI: " + str(err))

      if not is_valid:
         return error_func("LTI: unable to authenticate.")
      else:
         if login_func is not None:
            login_func(request, post_params)
         return func(request, *args, **kwargs)

   provider.csrf_exempt = True
   return provider
