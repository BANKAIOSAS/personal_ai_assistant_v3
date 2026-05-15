from django.contrib import admin
from django.urls import path
from bot_app import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.chat_page, name='home'),
    path('api/ask/', views.api_get_answer, name='ask_api'),
]

