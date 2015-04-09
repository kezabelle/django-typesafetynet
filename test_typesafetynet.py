# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
# noinspection PyUnresolvedReferences
from decimal import Decimal
import pytest
import tempfile
from uuid import uuid4, UUID
import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import (Form, ModelChoiceField, CharField, IntegerField, 
    DateField, TimeField, DateTimeField, RegexField, EmailField, FileField, 
    URLField, BooleanField, NullBooleanField, ChoiceField, 
    MultipleChoiceField, FloatField, DecimalField, SplitDateTimeField, 
    IPAddressField, GenericIPAddressField, FilePathField, SlugField, 
    TypedChoiceField, TypedMultipleChoiceField, ModelMultipleChoiceField)
from django.http import HttpRequest
from django.test import RequestFactory
from django.utils.encoding import force_text, force_bytes
from django.views.generic import View
import os
from typesafetynet import safetynet, SafetyNet404, FormField


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


@pytest.mark.django_db
def test_example_cbv_ok_using_args():
    request = RequestFactory().get('/')
    user = __makeuser('test')
    assert ExampleCBV.as_view()(request, user.pk, force_text(uuid4())) == 'woo cbv!'


@pytest.mark.django_db
def test_example_func_ok_using_kwargs():
    request = RequestFactory().get('/')
    user = __makeuser('test')
    assert example_func(request=request, obj=user.pk, uuid=force_text(uuid4())) == 'woo'


@pytest.mark.django_db
def test_example_cbv_ok_using_kwargs():
    request = RequestFactory().get('/')
    user = __makeuser('test')
    assert ExampleCBV.as_view()(request=request, obj=user.pk, uuid=force_text(uuid4())) == 'woo cbv!'


@pytest.mark.django_db
def test_example_func_ok_using_args_and_kwargs():
    request = RequestFactory().get('/')
    user = __makeuser('test')
    assert example_func(request, user.pk, uuid=force_text(uuid4())) == 'woo'


@pytest.mark.django_db
def test_example_cbv_ok_using_args_and_kwargs():
    request = RequestFactory().get('/')
    user = __makeuser('test')
    assert ExampleCBV.as_view()(request, user.pk, uuid=force_text(uuid4())) == 'woo cbv!'


def test_example_func_raises_404_using_invalid_args():
    request = RequestFactory().get('/')
    with pytest.raises(SafetyNet404):
        example_func(request, 'a', force_text(uuid4()))


def test_example_cbv_raises_404_using_invalid_args():
    request = RequestFactory().get('/')
    with pytest.raises(SafetyNet404):
        assert ExampleCBV.as_view()(request, 'a', force_text(uuid4())) == 'woo cbv!'


def test_example_func_raises_404_using_invalid_kwargs():
    request = RequestFactory().get('/')
    with pytest.raises(SafetyNet404):
        example_func(request=request, obj='blorp', uuid=force_text(uuid4()))


def test_example_cbv_raises_404_using_invalid_kwargs():
    request = RequestFactory().get('/')
    with pytest.raises(SafetyNet404):
        assert ExampleCBV.as_view()(request=request, obj='blorp', uuid=force_text(uuid4())) == 'woo cbv!'


def test_example_func_raises_404_using_args_and_kwargs():
    request = RequestFactory().get('/')
    with pytest.raises(SafetyNet404) as exc:
        example_func(request, 'invalid user', uuid='a-a-a-a')


def test_example_cbv_raises_404_using_args_and_kwargs():
    request = RequestFactory().get('/')
    with pytest.raises(SafetyNet404):
        assert ExampleCBV.as_view()(request, obj='invalid user', uuid='a-a-a-a') == 'woo cbv!'


class FuturamaForm(Form):
    clamps = CharField()

    def clean_clamps(self):
        return 'clamp! clamp!'


class CaptainKeywordsForm(Form):
    clop = CharField(max_length=4)
    futurama = FormField(FuturamaForm)

    def clean_clop(self):
        return 'did {}'.format(self.cleaned_data.get('clop', ''))



class ExampleOptionalForm(Form):
    id = IntegerField()
    id2 = IntegerField()
    # this is almost innocuous looking. It's for nested dictionaries. Now
    # we can validate **kwargs
    captain_kws = FormField(CaptainKeywordsForm)



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


@safetynet(ExampleOptionalForm)
def example_optional_func_with_defaultarg(request, id, id2=None):
    # should keep id2 as None
    return (id, id2)

@safetynet(ExampleOptionalForm)
def example_optional_func_with_starkwargs(request, id, id2=None, *aaarghs, **captain_kws):
    # turns out we'll not ever get aaarghs ... hmmm
    return [id, id2, aaarghs, captain_kws]


def test_optional_form_1_posarg():
    request = RequestFactory().get('/')
    assert example_optional_func(request, '12') == 12


def test_optional_form_2_posargs():
    request = RequestFactory().get('/')
    assert example_optional_func_both(request, '12', '10') == 22


def test_optional_form_3_posargs_with_unvalidated_option():
    request = RequestFactory().get('/')
    assert example_optional_func_with_extra(request, '12', '10', 'got {}') == 'got 22'


def test_optional_form_1_posarg_with_default_value():
    request = RequestFactory().get('/')
    assert example_optional_func_with_defaultarg(request, '12') == (12, None)


def test_optional_form_2_posargs_with_default_value_not_used():
    request = RequestFactory().get('/')
    assert example_optional_func_with_defaultarg(request, '12', '5') == (12, 5)


def test_optional_form_which_is_really_complex():
    """
    Specifically, this has named positional args, unnamed positional arguments
    (aaarghs) and unnamed keyword arguments (captain_kws) ... also the
    unnamed keyword arguments themselves have dictionaries in them, to test
    our ``FormField`` lark.
    """
    request = RequestFactory().get('/')
    hopeful = [
        12, -1,
        # *args
        ('clippity', 'clip'),
        # **kwargs ... containing a validated & modified dict.
        {'clop': 'did clop', 'futurama': {'clamps': u'clamp! clamp!'}}
    ]
    assert example_optional_func_with_starkwargs(
        request, '12', -1, 'clippity', 'clip', clop='clop',
        futurama={'clamps': 'clamp'}) == hopeful


@safetynet(ExampleOptionalForm)
def example_optional_func2_son_of_example_optional_func(request, id):
    return example_optional_func(request=request, id=id)


def test_nesting():
    request = RequestFactory().get('/')
    assert example_optional_func2_son_of_example_optional_func(request, '100') == 100
    with pytest.raises(SafetyNet404):
        example_optional_func2_son_of_example_optional_func(request=request, id='test')


@safetynet(klass=ExampleFuncForm, exception_class=PermissionDenied)
def example_func_with_custom_exception(request, obj, uuid):
    assert isinstance(request, HttpRequest)
    assert isinstance(uuid, UUID)
    assert isinstance(obj, get_user_model())
    return 'woo'


def test_custom_exception_on_invalid_form():
    request = RequestFactory().get('/')
    with pytest.raises(PermissionDenied):
        example_func_with_custom_exception(request, 'a', force_text(uuid4()))


class AllFieldTypesForm(Form):
    char = CharField()
    int_ = IntegerField()
    date = DateField()
    time = TimeField()
    datetime_ = DateTimeField()
    regex = RegexField(regex='^[a-f]{3}$')
    email = EmailField()
    file = FileField()
    # image = ImageField()
    url = URLField()
    bool = BooleanField()
    nullbool = NullBooleanField()
    choice = ChoiceField(choices=(
        ('test choice', 'yay test choice'),
    ))
    multichoice = MultipleChoiceField(choices=(
        ('test choice', 'yay test choice'),
        ('test choice 2', 'yay another choice'),
        ('test choice 3', 'yay test choice'),
    ))
    float = FloatField()
    decimal = DecimalField()
    ip = IPAddressField()
    generic_ip = GenericIPAddressField()
    filepath = FilePathField(path=tempfile.gettempdir(),
                             allow_files=True, allow_folders=True)
    slug = SlugField()
    typed_choice = TypedChoiceField(choices=(
        (1, 'test'),
        (2, 'test 2'),
        (3, 'bah'),
    ), coerce=int)
    typed_multichoice = TypedMultipleChoiceField(choices=(
        (1, 'test'),
        (2, 'test 2'),
        (3, 'bah'),
    ), coerce=int)
    model_choice = ModelChoiceField(queryset=get_user_model().objects.all())
    model_multichoice = ModelMultipleChoiceField(queryset=get_user_model().objects.all())



@safetynet(klass=AllFieldTypesForm, exception_class=ValueError)
def all_the_fields(char, int_, date, time, datetime_, regex, email, file,
                   url, bool, nullbool, choice, multichoice, float, decimal,
                   ip, generic_ip, filepath,
                   slug, typed_choice, typed_multichoice, model_choice, 
                   model_multichoice):
    assert force_text(char) == 'test'
    assert int_ == 4
    assert date == datetime.date(2012, 12, 12)
    assert time == datetime.time(14, 30, 59)
    assert datetime_ == datetime.datetime(2012, 12, 12, 14, 30, 59)
    assert regex == 'abc'
    assert email == 'x@y.zzz'
    assert isinstance(file, SimpleUploadedFile)
    assert url == 'https://bbc.co.uk/'
    assert bool is True
    assert nullbool is None
    assert choice == 'test choice'
    assert multichoice == ['test choice', 'test choice 2']
    assert float == 1.222
    assert decimal == Decimal('4.001')
    assert ip == '127.0.0.1'
    assert generic_ip == '255.255.255.255'
    assert filepath.startswith(tempfile.gettempdir())
    assert slug == 'yorp'
    assert typed_choice == 1
    assert typed_multichoice == [3, 2]
    assert isinstance(model_choice, get_user_model())
    assert len(model_multichoice) == 1
    assert isinstance(model_multichoice[0], get_user_model())


@pytest.mark.django_db
def test_all_the_fields_string_values_ok():
    """
    Note: MultiValueFields aren't supported, because the way they work
    doesn't really mesh well.
    """
    users = [__makeuser('test{}'.format(x)) for x in range(1, 3)]
    user1_id = force_text(users[0].pk)
    user2_id = force_text(users[1].pk)
    tmp = tempfile.gettempdir()
    txtfile = SimpleUploadedFile(name='test', content=force_bytes('whee'),
                                 content_type='text/plain')
    files_in_tmp = os.listdir(tmp)
    filepath = os.path.join(tmp, files_in_tmp[0])
    all_the_fields(char='test', int_='4', date='12/12/2012', time='14:30:59',
                   datetime_='12/12/2012 14:30:59', regex='abc', email='x@y.zzz',
                   file=txtfile, url='https://bbc.co.uk',
                   bool='1', nullbool='', choice='test choice',
                   multichoice=['test choice', 'test choice 2'], float='1.222',
                   decimal='4.001', ip='127.0.0.1',
                   generic_ip='255.255.255.255', filepath=filepath,
                   slug='yorp', typed_choice='1', typed_multichoice=['3', '2'],
                   model_choice=user1_id, model_multichoice=[user2_id])
