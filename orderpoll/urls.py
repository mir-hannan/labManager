from django.urls import path
from . import views

app_name = 'orderpoll'
urlpatterns = [
        path('login/', views.logIn, name='logIn'),
        path('usergen/', views.userGenerator, name='userGenerator'),
        path('logout/', views.logOut, name='logOut'),
        path('', views.index, name='home'),
        path('getOrder/', views.getOrder, name='getOrder'),
        path('newItem/', views.newItem, name='newItem'),
        path('<int:pk>/edit/', views.editOrder, name='editOrder'),
        path('<int:pk>/delete/', views.delOrder, name='delOrder'),
        path('<int:id>/qordered/', views.quickOrdered, name='quickOrdered'),
        path('<int:id>/qreceived/', views.quickReceived, name='quickReceived'),
        path('<int:id>/unqordered/', views.unQuickOrdered, name='unQuickOrdered'),
        path('<int:id>/unqreceived/', views.unQuickReceived, name='unQuickReceived'),
        path('history/', views.orderHistory, name='orderHistory'),
        path('manageOrders/', views.labmanPanel, name='labmanPanel'),
        path('inventoryPage/', views.inventoryPage, name='inventoryPage'),
        path('<int:pk>/editInven/', views.editInven, name='editInven'),
        path('POs/', views.pagePO, name='POs'),
        path('<int:pk>/order_note/', views.order_note, name='order_note'),
        path('nudge/', views.NudgePage, name='NudgePage'),
        path('<int:pk1>/nudged/', views.nudged, name='nudged'),
        path('suggestions/', views.OrderHelper, name='orderhelper'),
        path('snooze/<int:pk1>/<str:order_code>/<str:days>/', views.snooze, name='snooze'),
        path('<int:pk>/accept/', views.accept_suggest, name='accept'),
        path('Box/', views.newBox, name='Box'),
        path('<str:usr>/<str:shel>/delB/', views.del_box, name="delete_box"),
        path('<int:numneeded>/getBox/', views.get_boxes, name="get_boxes"),


    ]
