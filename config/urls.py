from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('banks/', include('apps.bank_parser.urls'))
]
