from copy import copy
import logging
from django.http import HttpRequest, Http404
from django.utils.six import iteritems
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
        needed_args = argspec.args
        unnamed_args = list(args)

        # special case instancemethods
        if instance is not None and 'self' in needed_args:
            needed_args.remove('self')

        # special case the request argument
        request = None
        if 'request' in needed_args:
            needed_args.remove('request')
            for index, arg in enumerate(unnamed_args):
                if isinstance(arg, HttpRequest):
                    request = arg
                    unnamed_args.remove(arg)

        args_to_check = {k: v for k, v in zip(needed_args, unnamed_args)}
        args_to_check.update(**kwargs)

        # request was passed in as a kwarg ... still remove it.
        if 'request' in args_to_check:
            request = args_to_check.pop('request')

        form = klass(data=args_to_check)

        # make the necessary fields required
        for fieldname in form.fields:
            if fieldname in args_to_check:
                form.fields[fieldname].required = True
            else:
                form.fields[fieldname].required = False

        is_valid = form.is_valid()
        if not is_valid:
            msg = ("Unable to validate {kws!r} using {form!r}, errors "
                   "were: {errors!r}".format(kws=args_to_check, form=klass,
                                             errors=form.errors))
            logger.error(msg, extra={'request': request, 'status_code': 404})
            raise SafetyNet404(msg)
        checked_args = copy(args_to_check)
        # only supply back the keys we can expect the function to take
        # and only those which have a value
        cleaned_form_data = {k:v for k, v in iteritems(form.cleaned_data)
                             if k in checked_args and v is not None}
        checked_args.update(**cleaned_form_data)
        if request is not None:
            checked_args.update(request=request)
        return function(**checked_args)
    return wrapper
