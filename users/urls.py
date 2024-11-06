from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register("users", views.CustomUserViewSet)
router.register("university-user", views.UniversityUsersViewSet)
