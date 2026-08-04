from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='list'),
    path('create/', views.PaymentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='detail'),
    path('<int:pk>/receipt/', views.ReceiptView.as_view(), name='receipt'),
    path('<int:pk>/status/<str:status>/', views.PaymentStatusUpdateView.as_view(), name='update_status'),
    path('<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='delete'),
    # M-Pesa
    path('mpesa/', views.MpesaPaymentView.as_view(), name='mpesa'),
    path('mpesa/status/<int:pk>/', views.MpesaStatusView.as_view(), name='mpesa_status'),
    path('mpesa/check/<int:pk>/', views.MpesaCheckStatusView.as_view(), name='mpesa_check'),
    path('mpesa/callback/', views.MpesaCallbackView.as_view(), name='mpesa_callback'),
    path('mpesa/transactions/', views.MpesaTransactionListView.as_view(), name='mpesa_transactions'),
    path('mpesa/query/<int:pk>/', views.MpesaTransactionQueryView.as_view(), name='mpesa_query'),
]
