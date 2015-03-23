# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import logging
from django.core.exceptions import ValidationError
from django.forms import Field
from django.http import Http404
from django.utils.six import iteritems
import wrapt
try:
    from inspect import signature
except ImportError:
    from funcsigs import signature


__version_info__ = '0.1.2'
__version__ = '0.1.2'
version = '0.1.2'
def get_version(): return version  # noqa


logger = logging.getLogger(__name__)


__all__ = [
    'safetynet',
    'SafetyNet404',
    'FormField',
]

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
        callsig = signature(function)
        bound_signature = callsig.bind(*args, **kwargs)
        callargs = bound_signature.arguments

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
            msg = ("Unable to validate {function!r} using {form!r}, errors "
                   "were: {errors!r}".format(function=function, form=klass,
                                             errors=form.errors))
            logger.error(msg, extra={'status_code': 404})
            raise SafetyNet404(msg)
        # only supply back the keys we can expect the function to take
        # and only those which have a value
        cleaned_form_data = {k:v for k, v in iteritems(form.cleaned_data)
                             if k in callargs and v is not None}
        callargs.update(**cleaned_form_data)
        return function(*bound_signature.args, **bound_signature.kwargs)
    return wrapper



class FormField(Field):
    def __init__(self, form_class, *args, **kwargs):
        super(FormField, self).__init__(*args, **kwargs)
        self.form_class = form_class

    def clean(self, value):
        value = super(FormField, self).clean(value=value)
        form = self.form_class(data=value)
        if form.is_bound:
            if form.is_valid():
                return form.cleaned_data
            else:
                raise ValidationError(message=[e for e in form.errors])
        return value
