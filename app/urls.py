# stock_monitor_project/app/urls.py
from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.index_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('get_chart_data/', views.get_chart_data, name='get_chart_data'),
    path('alertx/', views.alertx_view, name='alertx'),
    path('pricing/', views.pricing_view, name='pricing'),
    path('subscribe/', views.subscribe_index, name='subscribe_index'),

    # --- NEW URLS FOR STOCK WIDGET ---
    # URL for the stock data HTML page
    path('stock_data/', views.stocks_widget_view, name='stock_data'),
    # URL for the API endpoint to fetch stock data
    path('api/stock-data/', views.get_stock_data, name='get_stock_data'),
    # --- END NEW URLS ---
]