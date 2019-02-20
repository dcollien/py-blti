try:
   from django.http import HttpResponseForbidden
except:
   def HttpResponseForbidden(error_message):
      raise Exception(error_message)

from functools import partial, wraps
import oauth2 as oauth
import time
import os
import string

class OAuthInvalidError(Exception):
   pass

def sign_oauth_with_params(consumer_key, consumer_secret, url, parameters, method='POST', is_form_encoded=True):
   consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
   oauth_request = oauth.Request(method=method, url=url, parameters=parameters, is_form_encoded=is_form_encoded)
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

def set_lti_properties(consumer_lookup=None, site_url=None, require_post=None, error_func=None, allow_origin=None):
   """
   Set the default properties for the lti_provider decorator.
   """

   global LTI_PROPS
   
   if consumer_lookup is not None:
      LTI_PROPS['consumer_lookup'] = consumer_lookup
   if site_url is not None:
      LTI_PROPS['site_url'] = site_url
   if require_post is not None:
      LTI_PROPS['require_post'] = require_post
   if error_func is not None:
      LTI_PROPS['error_func'] = error_func
   if allow_origin is not None:
      LTI_PROPS['allow_origin'] = allow_origin

def sign_launch_data(url, launch_data, consumer_key, secret, is_form_encoded=True):
   """
   Generate the basic LTI launch data that needs to be POSTed to the given URL.

   launch_data -- a dictionary of LTI launch parameters, must contain "resource_link_id".
                   it is recommended that this also contain "user_id", "resource_link_title", "roles", etc.
   """

   chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
   nonce_chars = [chars[ord(x) % len(chars)] for x in os.urandom(32)]

   assert('resource_link_id' in launch_data)

   lti_params = {
      'lti_message_type': 'basic-lti-launch-request',
      'lti_version': 'LTI-1p0',

      'oauth_consumer_key': consumer_key,
      'oauth_signature_method': 'HMAC-SHA1',
      'oauth_timestamp': int(time.time()),
      'oauth_nonce': ''.join(nonce_chars),
      'oauth_version': '1.0'
   }

   lti_params.update(launch_data)

   return sign_oauth_with_params(consumer_key, secret, url, lti_params)

def lti_provider(func=None, consumer_lookup=None, site_url=None, require_post=None, error_func=None, allow_origin=None):
   """
   Django view decorator to create a basic LTI authenticated provider endpoint to receive bLTI POST requests.
   """

   if func is None:
      return partial(
         lti_provider, 
         consumer_lookup=consumer_lookup, 
         site_url=site_url,
         require_post=require_post,
         error_func=error_func,
         allow_origin=allow_origin
      )

   # Set defaults
   if consumer_lookup is None:
      consumer_lookup = LTI_PROPS.get('consumer_lookup', {})
   if site_url is None:
      site_url = LTI_PROPS.get('site_url', None)
   if require_post is None:
      require_post = LTI_PROPS.get('require_post', True)
   if error_func is None:
      error_func = LTI_PROPS.get('error_func', HttpResponseForbidden)
   if allow_origin is None:
      allow_origin = LTI_PROPS.get('allow_origin', '*')

   @wraps(func)
   def provider(request, *args, **kwargs):
      if request.method != 'POST':
         if require_post:
            return error_func('LTI: a POST request is required')
         else:
            return func(request, *args, **kwargs)

      post_params = dict(request.POST.iteritems())

      consumer_key = post_params.get('oauth_consumer_key', None)

      if consumer_key is None:
         return error_func('LTI: no consumer key provided')
      
      if callable(consumer_lookup):
         consumer_secret = consumer_lookup(consumer_key)
      else:
         consumer_secret = consumer_lookup.get(consumer_key, None)

      if consumer_secret is None:
         return error_func('LTI: unknown consumer ' + str(consumer_key))

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
         response = func(request, post_params, consumer_key, *args, **kwargs)

         if allow_origin:
            response['Access-Control-Allow-Origin'] = allow_origin
            response['Access-Control-Expose-Headers'] = 'Access-Control-Allow-Origin'

         return response

   provider.csrf_exempt = True
   return provider
