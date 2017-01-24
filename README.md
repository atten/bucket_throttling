# bucket_throttling
Throttling module that uses Token Bucket algorithm

**Integrations included:**
- Django (>=1.10)
- django-rest-framework (>=3.3)

**Test:**

`python tests.py`


**Dependencies:**
- redis

### Install

```
pip install -e git://github.com/atten/bucket_throttling.git#egg=bucket_throttling
```


### Usage in Django

1. Add middleware to project settings (after AuthenticationMiddleware):

```
MIDDLEWARE = [
    ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'bucket_throttling.integrations.django.BucketThrottlingMiddleware', 
    ...
]
```

2. Apply `throttle_request` decorator to target views:

```
from bucket_throttling.integrations.django import throttle_request
from bucket_throttling import ThrottlingRule

@throttle_request(ThrottlingRule(2, interval=60))  # it means 2 requests per 60 seconds
def my_view(request):
    return HttpResponse('Success!')

```

You're able to apply more complex rules:

```
from datetime import timedelta

@throttle_request([
    ThrottlingRule(5, interval=timedelta(minutes=1),
    ThrottlingRule(10, interval=timedelta(hours=1),
    ThrottlingRule(100, interval=timedelta(hours=24)
])
def my_view(request):
    ...
```
 
That's it!

If user has exceeded his limit, he will receive HTTP 429 with JSON like this:
 
`{"detail": "Expected available in 47 seconds."}`


### Usage in Django-REST-framework

If you want to throttle requests in ViewSet:

1. Add `ThrottledViewSetMixIn` to you class:

```
from rest_framework.viewsets import ModelViewSet
from bucket_throttling.integrations.rest_framework import ThrottledViewSetMixIn

class SomeModelViewSet(ThrottledViewSetMixIn, ModelViewSet):
    ...
```

2. In your class, assign `throttling_rules` or implement `get_throttling_rules` function:
 
```
class SomeModelViewSet(ThrottledViewSetMixIn, ModelViewSet):
    throttling_rules = [
        ThrottlingRule(5, interval=timedelta(minutes=1),
        ThrottlingRule(10, interval=timedelta(hours=1),
        ThrottlingRule(100, interval=timedelta(hours=24)
    ]
    
    # or
    
    def get_throttling_rules(self, request):
        # generate throttling rules for request here
        return [
            ThrottlingRule(5, interval=timedelta(minutes=1),
            ThrottlingRule(10, interval=timedelta(hours=1),
            ThrottlingRule(100, interval=timedelta(hours=24)
        ]
```
 
With `ThrottledViewSetMixIn`, it's not necessary to add middleware to project settings.

### Customize

1. Change default redis location

Add this code to settings.py to use custom redis port:
```
from bucket_throttling import defaultThrottlingOptions
defaultThrottlingOptions.redis_options = {'port': 6565}
```

2. Change throttling bucket arguments

todo