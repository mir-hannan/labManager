from django.db import models
import datetime
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.


class Users(models.Model):
    username = models.CharField(max_length=10)
    password = models.CharField(max_length=100)
    fname = models.CharField(max_length=50, null=True)
    User = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    admin = models.BooleanField(default=False)
    def __str__(self):
        return self.username

class Box(models.Model):
    owner = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, blank=True)
    rack = models.ForeignKey('Rack', on_delete=models.SET_NULL, null=True, blank=True)
    shelf = models.IntegerField(max_length=20, null=True, blank=True)
    #position= models.IntegerField(max_length=20, null=True, blank=True)
    def __str__(self):
        return str(self.rack) +' -> '+str(self.shelf)+ ' | '+str(self.owner)

class Rack(models.Model):
    row = models.CharField(max_length=20, null=True, blank=True)
    column = models.IntegerField(max_length=20, null=True, blank=True)
    S1 = models.IntegerField(max_length=20, null=True, blank=True)
    S2 = models.IntegerField(max_length=20, null=True, blank=True)
    S3 = models.IntegerField(max_length=20, null=True, blank=True)
    S4 = models.IntegerField(max_length=20, null=True, blank=True)
    s1_f = models.BooleanField(default=False)
    s2_f = models.BooleanField(default=False)
    s3_f = models.BooleanField(default=False)
    s4_f = models.BooleanField(default=False)
    full = models.BooleanField(default=False)
    def __str__(self):
        return str(self.row) +''+str(self.column)

class shelf(models.Model):
    name = models.CharField(max_length=5, null=True, blank=True)
    full = models.BooleanField(default=False)
    occupants = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name +' '+str(self.full)

class LabJob(models.Model):
    user = models.ForeignKey('Users', on_delete=models.CASCADE)
    job = models.CharField(max_length=500, null=True, blank=True)
    status = models.BooleanField(default=False)
    nudge = models.IntegerField(default=0)
    last_completed = models.DateField(null=True, blank=True)
    #Approximately how frequuently job needs completion (in days)
    lifetime = models.IntegerField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True, default=100.0)
    last_email = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.job+' -- '+self.user.username


class Message(models.Model):
    message = models.TextField(max_length=1000, null=True)
    owner = models.CharField(max_length=10, null=True)
    date = models.DateTimeField('date posted', null=True)
    def __str__(self):
        return self.message

class POs(models.Model):
    title = models.CharField(max_length=100, null=True, blank=True)
    PONumber = models.CharField(max_length=20, null=True, blank=True)
    date_added = models.DateTimeField('date posted', null=True)
    def __str__(self):
        return self.title


categories = ['Antibody','Drugs','Cell Isolation','GCMS','Isotopes','Vacuum','Biohazard','Bottle Top Filters', 'Glassware', 'Spatulas, Forceps, Scissors & Grinders',
              'Graduated Cylinders & Funnels', 'Carboys', 'Weigh Boats','Spray and Wash Bottles', 'Plates/Dishes',
              'Ice Buckets', 'Chemicals', 'Freezer Boxes', 'Metabolic Enzymes', 'TBD', 'Bacterial', 'Amino Acids', 'Qiagen Kits',
              'PPE', 'Water Baths', 'General Lab', 'Sealer Bags', 'Tubes & Cryovials', 'PCR', 'Pipette Tips',
              'Multichannel Pipette Tips & Supplies', 'Repeat Pipetter Tips', 'Media/Cell Culture', 'Westerns',
              'Serological Pipettes', 'Pasteur Pipettes', 'Syringes & Needles', 'From Boston', 'Cell Counter',
              'Wraps', 'Office Supplies', 'Cleaning Supplies', 'Dialysis', 'FACS', 'Mice', 'Stir Bars', 'Microscope',
              'Autoclave', 'Security', 'Antibody Kits', 'Radiation', 'Chromatography', 'Seahorse',
              'Nitrogen Tanks', 'Electroporation', 'Stericycle Filters', 'Desiccator', 'Restriction Enzymes']

units = ['EA','case','uL','mL','L','ug','mg','g','kg','T (antibody)','S (antibody)']
units2 = list(zip(units,units))
categories2 = list(zip(sorted(categories),sorted(categories)))

class Other(models.Model):
    other_description = models.CharField(max_length=200)
    other_manufacturer = models.CharField(max_length=200)
    other_code = models.CharField(max_length=50)
    other_quantity = models.IntegerField(default=1)
    other_units = models.CharField(max_length=50, choices = units2, default='EA')
    other_category = models.CharField(max_length=300, null=True, choices =categories2)
    other_link = models.CharField(max_length=500, null=True)
    other_notes = models.TextField(max_length=1000, null=True, blank=True)
    other_email = models.BooleanField(default=False)
    post_date = models.DateTimeField('Date Posted')
    def __str__(self):
        return self.other_description
    def was_published_recently(self):
        return self.post_date >=timezone.now() - datetime.timedelta(days=1)

class inventory(models.Model):
    item_description = models.CharField(max_length=200)
    item_manufacturer = models.CharField(max_length=200, null=True, blank=True)
    item_code = models.CharField(max_length=50, null=True)
    item_category = models.CharField(max_length=300, null=True, choices =categories2)
    item_stats = models.CharField(max_length=300, null=True)
    item_link = models.CharField(max_length=500, null=True)
    item_quick = models.BooleanField(default=False)
    post_date = models.DateTimeField('item added')
    #orderhistory= models.TextField(max_length=10000, blank=True)

    def __str__(self):
        return self.item_description
    class Meta:
        ordering = ['item_category']

def getInvenList():
        test = inventory.objects.order_by('item_category').values()
        invenlist = []
        invenlist2 = []
        for x in range(0, len(test)):
            invenlist.append(str(test[x]['item_description'])+' -- '+str(test[x]['item_manufacturer'])+' -- '+str(test[x]['item_category']))
            invenlist2.append(test[x]['item_code'])
        invenlist3 = list(zip(invenlist2,invenlist))
        print('invenlist3 created')
        return invenlist3

updatedList = getInvenList()

class ordered(models.Model):

    order_description = models.CharField(max_length=200)
    order_code = models.CharField(max_length=50, null=True, choices=updatedList)
    order_category = models.CharField(max_length=300, null=True, choices =categories2)
    order_quantity = models.IntegerField(default=1)
    order_units = models.CharField(max_length=50, choices = units2, default='EA')
    order_aliquots = models.IntegerField(default=0)
    order_owner = models.CharField(default='Lab', max_length=10)
    order_ordered = models.BooleanField(default=False)
    order_received = models.BooleanField(default=False)
    order_email = models.BooleanField(default=False)
    order_notes = models.TextField(max_length=1000, null=True, blank=True)
    order_backorder = models.CharField(max_length=200, null=True, blank=True)
    request_date = models.DateTimeField('Requested', null=True)
    order_date = models.DateTimeField('ordered', null=True, blank=True)
    receive_date = models.DateTimeField('received', null=True, blank=True)
    order_suggest = models.BooleanField(default=False)
    inven_item = models.ForeignKey(inventory, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.order_description

