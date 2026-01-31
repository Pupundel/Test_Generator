from django.contrib import admin  
from django.urls import path
from first.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', main_page, name='main'),
    

    path('generate-question/', generate_question, name='gen_q'),
    path('generate-answers/', generate_answers, name='gen_a'),
    path('save-final/', save_to_final, name='save_f'),
    path('reset-test/', reset_test, name='reset_test'),

    path('download-test/', download_test_txt, name='download_test'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)