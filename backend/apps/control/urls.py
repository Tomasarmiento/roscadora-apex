from django.urls import path, re_path
from django.urls.conf import include
from . import views

urlpatterns = [
    path('manual/motor/', views.manual_lineal, name='manual-motor'),
    path('manual/motor/enable/', views.enable_axis, name='enable-axis'),
    path('manual/motor/sync/', views.sync_axis, name='sync-axys'),
    path('manual/neummatica/', views.ManualPneumatic.as_view(), name='manual-pneumatic'),
    path('semiautomatico/', views.semiauto, name='semiauto'),
    path('manual/stop-axis/', views.stop_axis, name='stop-axis'),
    path('stop-all/', views.stop_all, name='stop-all'),
    path('end-master-routine/', views.end_master_routine, name='end-master-routine'),
    path('reset-cuplas-count/', views.reset_cuplas_count, name='reset_cuplas_count'),
    path('safe-mode/', views.safe_mode, name='safe-mode'),
    # path('referenciar-lineal/', views.referenciar_lineal, name='referenciar-lineal'),
    path('auto/', views.StartRoutine.as_view(), name='auto'),
    path('safe/', views.enter_exit_safe, name='toggle-safe'),
    # path('logout/', views.logout, name="logout"),
    path('exit-tapping/', views.exit_tapping, name='end-master-routine'),
]