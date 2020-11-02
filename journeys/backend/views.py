from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from journeys.errors import ConflictNotResolvedError
from journeys.errors import JourneysError
from journeys.modifier.conflict.plugins import load_plugins

from ..validators.checks_for_cli import default_checks
from . import forms
from . import logic
from . import models
from . import serializers


def get_supported_features(request):
    plugins = load_plugins()
    return JsonResponse({"items": [plugin.ID for plugin in plugins]})


def get_supported_validators(request):
    return JsonResponse(
        {
            "validators": {
                check.name: {
                    "require_source": check.require_source,
                    "require_root": check.require_root,
                    "description": check.description,
                }
                for check in default_checks.values()
            }
        }
    )


class SessionsViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.SessionDetailsSerializer

        return serializers.SessionSerializer

    queryset = models.Session.objects.all()  # pylint: disable=E1101

    def perform_create(self, serializer):
        session = serializer.save()
        logic.get_controller(session=session, allow_empty=True)

    @action(detail=True, methods=["post"])
    def source(self, request, pk):

        session = models.Session.objects.get(pk=pk)  # pylint: disable=E1101
        system_credentials = None

        form = forms.SourceForm(request.POST, request.FILES)
        form.is_valid()
        if form.errors:
            # TODO: Fill response content
            return HttpResponseBadRequest()
        fs = FileSystemStorage(location=session.working_directory)

        as3_file = (
            fs.save(form.cleaned_data["as3_file"].name, form.cleaned_data["as3_file"])
            if "as3_file" in form.cleaned_data and form.cleaned_data["as3_file"]
            else None
        )

        if "ucs_file" in form.cleaned_data and form.cleaned_data["ucs_file"]:
            ucs_file = fs.save(
                form.cleaned_data["ucs_file"].name, form.cleaned_data["ucs_file"]
            )
            ucs_passphrase = form.cleaned_data.get("ucs_passphrase", None)
        else:
            system_credentials = models.SystemCredentials(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                host=form.cleaned_data["host"],
            )
            try:
                ucs_file, ucs_passphrase = logic.download_ucs(
                    session=session, system_credentials=system_credentials
                )
                system_credentials.save()
            except JourneysError:
                # TODO: Fill response content
                return HttpResponseBadRequest()

        clear = True  # request.GET.get("clear", False)

        logic.initialize(
            session=session,
            ucs_file=ucs_file,
            ucs_passphrase=ucs_passphrase,
            as3_file=as3_file,
            clear=clear,
            credentials=system_credentials,
        )

        return Response()

    @action(detail=True, methods=["post"])
    def current_conflict(self, request, pk):
        session = models.Session.objects.get(pk=pk)  # pylint: disable=E1101
        conflict_id = request.data["conflict_id"]

        logic.set_current_conflict(session=session, conflict_id=conflict_id)
        return Response()

    @current_conflict.mapping.delete
    def delete_current_conflict(self, request, pk):
        session = models.Session.objects.get(pk=pk)  # pylint: disable=E1101

        logic.reset_current_conflict(session=session)
        return Response()


class SessionFilesViewSet(viewsets.GenericViewSet):
    lookup_value_regex = r".+"
    lookup_url_kwarg = "file_path"

    def retrieve(self, request, session_pk, file_path, *args, **kwargs):
        session = models.Session.objects.get(pk=session_pk)  # pylint: disable=E1101
        controller = logic.get_controller(session=session)
        fs = FileSystemStorage(location=controller.repo_path)
        try:
            f = fs.open(file_path)
        except FileNotFoundError:
            return HttpResponseNotFound()

        return FileResponse(f, content_type="application/octet-stream")

    def update(self, request, session_pk, file_path, *args, **kwargs):
        session = models.Session.objects.get(pk=session_pk)  # pylint: disable=E1101
        controller = logic.get_controller(session=session)

        form = forms.FileUploadFrom(data=request.POST, files=request.FILES)
        form.full_clean()
        if form.errors:
            # TODO: Fill response content
            return HttpResponseBadRequest()
        fs = FileSystemStorage(location=controller.repo_path)

        if fs.exists(file_path):
            fs.delete(file_path)

        fs.save(file_path, form.cleaned_data["file"])
        return Response(status=202)

    def delete(self, request, session_pk, file_path, *args, **kwargs):
        session = models.Session.objects.get(pk=session_pk)  # pylint: disable=E1101
        controller = logic.get_controller(session=session)
        fs = FileSystemStorage(location=controller.repo_path)
        try:
            fs.delete(file_path)
        except FileNotFoundError:
            return HttpResponseNotFound()

        return Response()


class SessionBranchesViewSet(viewsets.GenericViewSet):
    lookup_value_regex = r".+"


class SessionBranchesFilesViewSet(viewsets.GenericViewSet):
    lookup_value_regex = r".+"
    lookup_url_kwarg = "file_path"

    def retrieve(
        self, request, session_pk, session_branch_pk, file_path, *args, **kwargs
    ):
        session = models.Session.objects.get(pk=session_pk)  # pylint: disable=E1101
        controller = logic.get_controller(session=session)
        git = controller.repo.git
        content = git.show(f"{session_branch_pk}:{file_path}")

        return FileResponse(content, content_type="application/octet-stream")


class SessionConflictsViewSet(
    mixins.ListModelMixin, viewsets.GenericViewSet,
):
    def get_queryset(self):
        return models.Conflict.objects.filter(  # pylint: disable=E1101
            session=self.kwargs["session_pk"]
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.ConflictDetailsSerializer

        return serializers.ConflictSerializer


class SessionChangesViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        return models.Change.objects.filter(  # pylint: disable=E1101
            session=self.kwargs["session_pk"]
        ).order_by("id")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.ChangeDetailsSerializer

        return serializers.ChangeSerializer

    def create(self, request, session_pk, *args, **kwargs):
        session = models.Session.objects.get(pk=session_pk)  # pylint: disable=E1101

        message = request.data.get("message", None)
        try:
            logic.process(session=session, commit_name=message)
        except ConflictNotResolvedError:
            # TODO: Fill response content
            return HttpResponseBadRequest()

        return Response()


class SessionDeploymentsViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        return models.Deployment.objects.filter(  # pylint: disable=E1101
            session=self.kwargs["session_pk"]
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.DeploymentDetailsSerializer

        return serializers.DeploymentSerializer

    @action(detail=True, methods=["get"])
    def log(self, request, session_pk=None, pk=None):
        # TODO: implement
        return Response({})

    @action(detail=True, methods=["get"])
    def report(self, request, session_pk=None, pk=None):
        # TODO: implement
        return Response({})
