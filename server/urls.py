from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path ,path
from . import views

urlpatterns = [
re_path('api/login' , views.login) ,
re_path('api/signup' , views.signup) , 
re_path('api/avatars', views.predefined_avatars), 
re_path('api/categories', views.categoryListAll), 
 path('api/category/<int:category_id>/', views.contentListByCat, name='content-list-by-category'),
 path('api/content/<int:content_id>/', views.contentListById, name='content-list-by-id'),
 re_path('api/todo-lists', views.todo_list_create), 
 path('api/todo-list/<int:todo_id>', views.todo_detail_update_delete, name='todo-list-by-id'),

 
 
re_path('api/admin/login', views.admin_login),  
re_path('api/admin/refresh', views.refresh_token),  
re_path('api/admin/generateQr', views.generate_qr_code),  
path('api/admin/category/<int:category_id>/', views.category_update_delete, name='update-delete-category'),
re_path('api/admin/categories', views.adminCreateCategory), 

path('api/admin/content/<int:content_id>/', views.content_update_delete, name='update-delete-category'),
re_path('api/admin/content', views.adminCreateContent), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)