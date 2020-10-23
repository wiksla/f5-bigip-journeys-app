"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include
from django.urls import path
from rest_framework_nested import routers

from . import views

router = routers.SimpleRouter(trailing_slash=False)
router.register(r"sessions", views.SessionsViewSet)

sessions_router = routers.NestedSimpleRouter(router, r"sessions", lookup="session")
sessions_router.register(
    r"conflicts", views.SessionConflictsViewSet, basename="session-conflicts"
)
sessions_router.register(
    r"changes", views.SessionChangesViewSet, basename="session-changes"
)
sessions_router.register(
    r"deployments", views.SessionDeploymentsViewSet, basename="session-deployments"
)
sessions_router.register(
    r"files", views.SessionFilesViewSet, basename="session-files",
)
sessions_router.register(
    r"branches", views.SessionBranchesViewSet, basename="session-branches"
)
sessions_branches_router = routers.NestedSimpleRouter(
    sessions_router, r"branches", lookup="session_branch"
)
sessions_branches_router.register(
    r"files", views.SessionBranchesFilesViewSet, basename="session-branch-files"
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(sessions_router.urls)),
    path("", include(sessions_branches_router.urls)),
    path(r"supported_features", views.get_supported_features),
    path(r"supported_validators", views.get_supported_validators),
]
