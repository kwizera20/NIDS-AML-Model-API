from django.contrib import admin
from django.urls import include, path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Model API",
        default_version='v1',
        description="API to use ML model",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url= 'https://nidsmodel-dcgjbegraqc9cna0.southafricanorth-01.azurewebsites.net/swagger/'
    # url = 'http://127.0.0.1:8000/swagger/'
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('mlmodel.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
