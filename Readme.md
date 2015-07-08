A simple basic LTI authentication mechanism for django.

Tested with:
http://www.imsglobal.org/developers/LTI/test/v1p1/lms.php

as both a provider and a consumer.


    pip install blti


As a provider:
see django_view.py

    from blti import lti_provider

    @lti_provider
    def provider_view(request):
        pass # your authenticated view here

N.B. to allow the embedding of your LTI provider in an iframe, you may need to disable django clickjacking protection (e.g. also using @xframe_options_exempt) when the "launch_presentation_document_target" parameter is set to "iframe".

set default options with:

    import blti

    blti.set_lti_properties(
        # this may be a callable or a dictionary-like object
		consumer_lookup = {
			'test_consumer': 'test_secret123'
		},
		site_url = 'https://www.example.com', # your site URL (if set to None, Django will try to infer it from the request)
		login_func = do_login, # the login function delegate (to log in or create new users)
		require_post = True, # this view only accepts POST requests
		error_func = some_error_callable # the callable to use to handle errors. Defaults to HttpResponseForbidden
        allow_origin = '*' # the value for the Access-Control-Allow-Origin header
	)

or pass them in:

    import blti

    @blti.lti_provider(allow_origin='https://www.example.com')
    def provider_view(request):
        pass


As a consumer:

    import blti

   	params = {
        'resource_link_id': 'unique value for the link',
        'resource_link_title': 'title of the link, e.g link text',
        'resource_link_description': 'description for the link',
        'user_id': 'some_user_id_123,
        'user_image': 'https://www.example.com/some_user_id_123.png',
        'roles' : 'Instructor',
        'lis_person_name_full': 'Some User',
        'lis_person_contact_email_primary': 'some_user_123@example.com',

        'context_id': 'course_id',
        'context_type': 'CourseSection',
        'context_title': 'Course on Stuff',

        # etc... for as many LTI params as required
    }
    
    url = 'https://www.some_provider.com/launch_url/'

    # this will be the same parameters, but with extra oauth and lti data, and the oauth_signature attached
    post_data = blti.sign_launch_data(url, params, 'my consumer key', 'my consumer secret')

