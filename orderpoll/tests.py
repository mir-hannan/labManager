from django.test import TestCase
import datetime
from django.utils import timezone

from orderpoll.models import Other

# Create your tests here.
class NewItemTest(TestCase):
    def setup(self):
        Other.objects.create(other_description='test',other_manufacturer='test',
                             other_code='test', other_quantity=1,
                             other_units='EA', other_category='Amino Acids',
                             other_link='null', post_date = timezone.now())

    def newItems(self):
        time = timezone.now(), datetime.timedelta(days=30)
        future_other = Other(post_date=time)
        self.assertIs(future_other.was_published_recently(), False)
