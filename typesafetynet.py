from copy import copy
from functools import partial
import logging
from django.http import HttpRequest, Http404
from django.utils.six import iteritems
from django.utils.functional import curry
import wrapt
import inspect


logger = logging.getLogger(__name__)

# noinspection PyPep8
class SafetyNet404(Http404): pass


def safetynet(klass):
    """
    Pass a Django form, and get typecast data in your functions.

    `klass` should be a `django.forms.Form` subclass, though in fact as long
    as it accepts a `data` kwarg and implements an `is_valid` method and
    a `cleaned_data` attribute, it could be something else if you want.

    Raises an Http404 subclass on invalid form.
    """
    @wrapt.decorator
    def wrapper(function, instance, args, kwargs):
        argspec = inspect.getargspec(func=function)
        callargs = inspect.getcallargs(function, *args, **kwargs)

        # pull out *args and **kwargs by given name
        varargs = ()
        keywords = {}
        if argspec.varargs is not None and argspec.varargs in callargs:
            varargs = callargs.pop(argspec.varargs)
        if argspec.keywords is not None and argspec.keywords in callargs:
            keywords = callargs.pop(argspec.keywords)
        if keywords:
            # merge **kwargs back into the dict
            callargs.update(**keywords)

        # if we find self in the callargs and it matches our instance,
        # remove it or we'll encounter multiple selfs trying to be passed to
        # the method itself.
        if instance is not None:
            try:
                key = next(k for k, v in iteritems(callargs) if v is instance)
            except StopIteration:
                pass
            else:
                callargs.pop(key)

        form = klass(data=callargs)
        # make the necessary fields required
        for fieldname in form.fields:
            if fieldname in callargs:
                # only mark it as required if it's not None ...
                form.fields[fieldname].required = callargs[fieldname] is not None
            else:
                form.fields[fieldname].required = False

        is_valid = form.is_valid()
        if not is_valid:
            msg = ("Unable to validate {kws!r} using {form!r}, errors "
                   "were: {errors!r}".format(kws=callargs, form=klass,
                                             errors=form.errors))
            logger.error(msg, extra={'status_code': 404})
            raise SafetyNet404(msg)
        # only supply back the keys we can expect the function to take
        # and only those which have a value
        cleaned_form_data = {k:v for k, v in iteritems(form.cleaned_data)
                             if k in callargs and v is not None}
        callargs.update(**cleaned_form_data)
        if varargs:
            partial_function = curry(function, **callargs)
            return partial_function(*varargs)
        return function(**callargs)
    return wrapper
