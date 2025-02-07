from django.contrib import admin
from .models import LabJob,  Other, inventory, ordered, Users, POs, shelf, Box, Rack

# Register your models here.
admin.site.register(Other)
admin.site.register(inventory)
admin.site.register(ordered)
admin.site.register(Users)
admin.site.register(POs)
admin.site.register(LabJob)
admin.site.register(Box)
admin.site.register(shelf)
admin.site.register(Rack)



admin.site.site_url = '10.163.28.176:8000/orderpoll/'

class inventoryAdmin(admin.ModelAdmin):
    search_fields= ('item_description', 'item_category')
