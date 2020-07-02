from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # path('', schema_view),
    path('admin/', admin.site.urls),
    path('banks/', include('bank_parser.urls')),
    path('api/user/', include('users.urls')),
]
