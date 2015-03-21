django-typesafetynet
====================

A decorator for validating arguments and casting them to the correct
type, using `Django`_ `Forms`_.


.. _Django: https://docs.djangoproject.com/en/stable/
.. _Forms: https://docs.djangoproject.com/en/stable/topics/forms/


Usage & API
-----------

Here we go, let's define a function::

    from django.http import HttpResponse

    def myfunc(request, id, user):
        return HttpResponse('ahoy')

And now a form::

    from django.forms import Form
    from django.forms.fields import IntegerField
    from django.forms.models import ModelChoiceField

    class MyFuncForm(Form):
        id = IntegerField()
        user = ModelChoiceField(queryset=get_user_model().objects.filter(is_active=True))

We can wire the ``Form`` up as a validator for the supplied arguments, replacing
``myfunc`` with::

    from typesafetynset import safetynet

    @safetynet(MyFuncForm)
    def myfunc(request, id, user):
        # ...

If the arguments received when called (ie: by a ``urlconf`` match) are valid,
then ``id`` will be an int, and ``user`` will be an instance of whatever
``get_user_model()`` is defined as.

If the arguments are invalid, an `Http404` exception is raised.


How it works
------------

given a ``Form``, the ``cleaned_data`` dictionary is used to update the original
string arguments with their correct variants.


Running the tests
-----------------

Given a complete clone::

    python setup.py test

Or, for a full test::

    tox


Test status
^^^^^^^^^^^

.. image:: https://travis-ci.org/kezabelle/django-typesafetynet.svg
  :target: https://travis-ci.org/kezabelle/django-typesafetynet
