# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import pytest
from uuid import uuid4, UUID
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import Form, ModelChoiceField, CharField, IntegerField
from django.http import HttpRequest
from django.test import RequestFactory
from django.utils.encoding import force_text
from django.views.generic import View
from typesafetynet import safetynet, SafetyNet404


class ExampleFuncForm(Form):
    obj = ModelChoiceField(queryset=get_user_model().objects.all())
    uuid = CharField(max_length=36)

    def clean_uuid(self):
        try:
            return UUID(self.cleaned_data['uuid'])
        except ValueError:
            raise ValidationError("That's not a valid UUID")


@safetynet(klass=ExampleFuncForm)
def example_func(request, obj, uuid):
    assert isinstance(request, HttpRequest)
    assert isinstance(uuid, UUID)
    assert isinstance(obj, get_user_model())
    return 'woo'


class ExampleCBV(View):
    @safetynet(klass=ExampleFuncForm)
    def get(self, request, obj, uuid):
        assert isinstance(request, HttpRequest)
        assert isinstance(uuid, UUID)
        assert isinstance(obj, get_user_model())
        return 'woo cbv!'


def __makeuser(name):
    user = get_user_model()(username=name)
    user.set_password(raw_password=name)
    user.full_clean()
    user.save()
    return user


@pytest.mark.django_db
def test_example_func_ok_using_args():
    request = RequestFactory().get('/')
    user = __makeuser('test')
    assert example_func(request, user.pk, force_text(uuid4())) == 'woo'
    assert ExampleCBV.as_view()(request, user.pk, force_text(uuid4())) == 'woo cbv!'


@pytest.mark.django_db
def test_example_func_ok_using_kwargs():
    request = RequestFactory().get('/')
    user = __makeuser('test')
    assert example_func(request, obj=user.pk, uuid=force_text(uuid4())) == 'woo'
    assert ExampleCBV.as_view()(request, obj=user.pk, uuid=force_text(uuid4())) == 'woo cbv!'


@pytest.mark.django_db
def test_example_func_ok_using_args_and_kwargs():
    request = RequestFactory().get('/')
    user = __makeuser('test')
    assert example_func(user.pk, request=request, uuid=force_text(uuid4())) == 'woo'
    # for some reason I'm not bothered by right now, doing request=request yields
    # TypeError: view() got multiple values for keyword argument 'request'
    assert ExampleCBV.as_view()(request, user.pk, uuid=force_text(uuid4())) == 'woo cbv!'


@pytest.mark.django_db
def test_example_func_raises_404_using_invalid_args():
    request = RequestFactory().get('/')
    with pytest.raises(SafetyNet404):
        example_func(request, 'a', force_text(uuid4()))
    with pytest.raises(SafetyNet404):
        assert ExampleCBV.as_view()(request, 'a', force_text(uuid4())) == 'woo cbv!'


@pytest.mark.django_db
def test_example_func_raises_404_using_invalid_kwargs():
    request = RequestFactory().get('/')
    with pytest.raises(SafetyNet404):
        example_func(request, obj='blorp', uuid=force_text(uuid4()))
    with pytest.raises(SafetyNet404):
        assert ExampleCBV.as_view()(request, obj='blorp', uuid=force_text(uuid4())) == 'woo cbv!'

@pytest.mark.django_db
def test_example_func_raises_404_using_args_and_kwargs():
    request = RequestFactory().get('/')
    with pytest.raises(SafetyNet404) as exc:
        example_func('invalid user', request=request, uuid='a-a-a-a')
    # for some reason I'm not bothered by right now, doing request=request yields
    # TypeError: view() got multiple values for keyword argument 'request'
    with pytest.raises(SafetyNet404):
        assert ExampleCBV.as_view()(request, obj='invalid user', uuid='a-a-a-a') == 'woo cbv!'



class ExampleOptionalForm(Form):
    id = IntegerField()
    id2 = IntegerField()


@safetynet(ExampleOptionalForm)
def example_optional_func(request, id):
    return id


@safetynet(ExampleOptionalForm)
def example_optional_func_both(request, id, id2):
    return id + id2


@safetynet(ExampleOptionalForm)
def example_optional_func_with_extra(request, id, id2, unvalidated_option):
    # only id and id2 are validated
    return unvalidated_option.format(id + id2)


def test_optional_form():
    request = RequestFactory().get('/')
    assert example_optional_func(request, '12') == 12
    assert example_optional_func_both(request, '12', '10') == 22
    assert example_optional_func_with_extra(request, '12', '10', 'got {}') == 'got 22'
