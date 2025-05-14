# from django.contrib import admin
# from django.urls import include, path
#
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('jobs/', include('jobapply.urls')),
# ]
#


from django.contrib import admin
from django.urls import include, path
from jobapply.views import home  # Import home view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('jobs/', include('jobapply.urls')),  # Ensure this app has its own URLs
    path('', home),  # Add home page route
]
