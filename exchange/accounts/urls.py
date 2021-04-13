from django.urls import path
from .views import (
    homepage_view,
    login_view,
    logout_view,
    register_view,
    user_profile_view,
    json_profile_view,
    permission_denied_view,
    change_password_view,
    password_changed_view,
    ip_check_view,
)

urlpatterns = [
    path('', homepage_view, name='homepage-view'),
    path('login/', login_view, name='login-view'),
    path('logout/', logout_view, name='logout-view'),
    path('register/', register_view, name='register-view'),
    path('user/<int:id>/', user_profile_view, name='user-profile-view'),
    path('user/<int:id>/json', json_profile_view, name='json-profile-view'),
    path('permission_denied/', permission_denied_view, name='permission-denied-view'),
    path('change_password/', change_password_view, name='change-password-view'),
    path('password_changed/', password_changed_view, name='password-changed-view'),
    path('ip_check/', ip_check_view, name='ip-check-view'),
]