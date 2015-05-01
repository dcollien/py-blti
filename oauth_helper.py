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
        raise OAuthInvalidError("Missing OAuth Signature")

    is_valid = signature_method.check(oauth_request, oauth_consumer, None, signature)

    return is_valid
