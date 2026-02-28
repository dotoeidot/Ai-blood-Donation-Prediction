from django.contrib import admin
from .models import DonationRecord

admin.site.register(DonationRecord)
from .models import DonorHistory

admin.site.register(DonorHistory)