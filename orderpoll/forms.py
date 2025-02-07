from django import forms
from .models import LabJob, ordered, inventory, Other, Users, categories, Message, getInvenList
from django.utils import timezone
from django.forms import modelformset_factory, ModelMultipleChoiceField, CheckboxInput
from django_select2.forms import Select2Widget
from bootstrap_datepicker_plus.widgets import DateTimePickerInput


class user_gen_form(forms.Form):
    username = forms.CharField(max_length=100)
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.CharField(max_length=100)
    is_staff = forms.BooleanField(required=False)



class loginForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ('username',)

class OrderReceiveForm(forms.ModelForm):
    class Meta:
        model = ordered
        fields = ('order_received','order_description','order_code', 'order_quantity')

class OrderFormsetForm(forms.ModelForm):
    class Meta:
        model = ordered
        exclude= ('order_suggest','order_code')
        widgets={'receive_date':DateTimePickerInput(), 'order_date':DateTimePickerInput()}#, 'order_code': Select2Widget()}
        labels= {'order_quantity':'Quantity', 'other_units':'Units','order_email':'Receive Email?', 'order_notes':'Notes', 'order_aliquots':'# of stickers?'}


OrderReceiveFormset = modelformset_factory(ordered, form=OrderFormsetForm, extra=0)

BulkNewItemFormset = modelformset_factory(Other, exclude=('',), widgets ={'post_date':DateTimePickerInput()}, extra=10)


class BoxForm(forms.Form):
    numberNeeded = forms.IntegerField(label="How many boxes do you need?", max_value=10)



class LabJobForm2(forms.ModelForm):
    job = forms.CharField(required=False, disabled=True)
    nudge = forms.IntegerField(required=False)
    score= forms.FloatField(disabled=True)

    class Meta:
        model = LabJob
        fields = ('job','status','nudge', 'score')
    """
    def __init__(self, *args, **kwargs):
               super(LabJobForm2, self).__init__(*args, **kwargs)
               print('kwargs:',kwargs)
               print('args:', args)
               self.fields['status'].label = kwargs['instance'].job
               self.fields['nudge'].label = 'nudge'
    """

LabJobFormset = modelformset_factory(LabJob, form=LabJobForm2,  extra=0)


class LabJobFormNudge(forms.ModelForm):
    job = forms.CharField(required=False, disabled=True)
    nudge = forms.IntegerField(required=False)
    last_completed = forms.DateField(disabled=True)
    score = forms.FloatField(disabled=True)

    class Meta:
        model = LabJob
        fields = ('nudge','job', 'last_completed', 'score')

LabJobFormsetNudge = modelformset_factory(LabJob, form=LabJobFormNudge, extra=0)


class InvenEditForm(forms.ModelForm):
    class Meta:
        model = inventory
        exclude=('',),
        widgets={'post_date':DateTimePickerInput()}

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('message',)

class OrderForm(forms.ModelForm):
    class Meta:
        model = ordered
        fields = ('order_code', 'order_quantity', 'order_units','order_notes','order_email','order_aliquots')
        widgets = {'order_code': Select2Widget}
        labels= {'order_code': 'Item', 'order_quantity':'Quantity', 'other_units':'Units','order_email':'Receive Email?', 'order_notes':'Notes', 'order_aliquots':'# of stickers?'}

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['order_code'].choices = getInvenList()
        self.fields['order_code'].widget.choices = getInvenList()

class newItemForm(forms.ModelForm):
    class Meta:
        model = Other
        fields = ('other_description', 'other_manufacturer', 'other_code','other_category','other_quantity', 'other_email','other_units','other_link','other_notes')
        labels = {'other_description':'New Item', 'other_manufacturer': 'Item Manufacturer', 'other_code':'Catalogue #',
                  'other_category':'Item Category','other_link':'Link to item','other_quantity':'Quantity', 'other_units':'Units', 'other_email':'Receive email?', 'other_notes':'Notes'}

        widgets = {'order_code': Select2Widget()}
