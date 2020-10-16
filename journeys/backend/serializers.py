from rest_framework import serializers

from . import models


class SessionSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField("get_url")
    last_update_time = serializers.SerializerMethodField("get_last_update_time")

    def get_url(self, session):
        request = self.context["request"]
        base_url = f"/sessions/{session.id}"
        return request.build_absolute_uri(base_url)

    def get_last_update_time(self, session):
        return int(session.last_update_time.timestamp() * 1000000)

    class Meta:
        model = models.Session
        fields = ["id", "url", "last_update_time"]


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Source
        fields = ["has_ucs", "has_as3", "credentials"]


class ConflictSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField("get_name")
    affected_objects = serializers.SerializerMethodField("get_affected_objects")

    def get_name(self, conflict):
        return conflict.name

    def get_affected_objects(self, conflict):
        return conflict.affected_objects

    class Meta:
        model = models.Conflict
        fields = ["id", "summary", "affected_objects"]


class FileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField("get_url")

    def get_url(self, file):
        request = self.context["request"]
        base_url = f"/sessions/{file.session.id}/"
        if file.mitigation:
            base_url += f"branches/{file.mitigation.name}/"
        base_url += f"files/{file.path}"
        return request.build_absolute_uri(base_url)

    class Meta:
        model = models.File
        fields = ["path", "url"]


class MitigationSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = models.Mitigation
        fields = ["name", "files"]


class ConflictDetailsSerializer(ConflictSerializer):
    files = serializers.SerializerMethodField("get_files")
    mitigations = MitigationSerializer(many=True, read_only=True)

    def get_files(self, conflict):
        return FileSerializer(
            context=self.context,
            instance=models.File.objects.filter(  # pylint: disable=E1101
                conflict=conflict, mitigation=None
            ),
            many=True,
        ).data

    class Meta:
        model = models.Conflict
        fields = ["id", "summary", "affected_objects", "files", "mitigations"]


class ChangeSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField("get_url")

    def get_url(self, change):
        request = self.context["request"]
        base_url = f"/sessions/{change.session.id}/changes/{change.id}"
        return request.build_absolute_uri(base_url)

    class Meta:
        model = models.Change
        fields = ["id", "message", "commit", "url"]


class ChangeDetailsSerializer(ChangeSerializer):
    class Meta:
        model = models.Change
        fields = ["id", "message", "url", "content"]


class SystemCredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SystemCredentials
        fields = ["username", "password", "host"]
        extra_kwargs = {"password": {"write_only": True}}


class DeploymentSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField("get_url")
    validators = serializers.SerializerMethodField("get_validators")
    source = SystemCredentialsSerializer()
    destination = SystemCredentialsSerializer()

    def get_url(self, deployment):
        request = self.context["request"]
        base_url = f"/sessions/{deployment.session.id}/deployments/{deployment.id}"
        return request.build_absolute_uri(base_url)

    def get_validators(self, deployment):
        return deployment.validators

    class Meta:
        model = models.Deployment
        fields = ["id", "url", "source", "destination", "validators", "status"]


class DeploymentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeploymentResult
        fields = ["time", "message"]


class DeploymentDetailsSerializer(DeploymentSerializer):

    results = DeploymentResultSerializer(many=True, read_only=True)

    class Meta:
        model = models.Deployment
        fields = [
            "id",
            "url",
            "source",
            "destination",
            "validators",
            "status",
            "results",
        ]


class SessionDetailsSerializer(SessionSerializer):
    source = SourceSerializer(read_only=True)
    conflicts = ConflictSerializer(many=True, read_only=True)
    changes = ChangeSerializer(many=True, read_only=True)
    current_conflict = serializers.SerializerMethodField("get_current_conflict")
    instructions = serializers.SerializerMethodField("get_instructions")
    deployments = DeploymentSerializer(many=True, read_only=True)

    def get_current_conflict(self, session):
        if not session.current_conflict:
            return None

        conflict = models.Conflict.objects.get(  # pylint: disable=E1101
            name=session.current_conflict, session=session
        )

        return ConflictDetailsSerializer(context=self.context, instance=conflict).data

    def get_instructions(self, instance):
        if instance.instructions:
            return {"message": instance.instructions}
        return None

    def to_representation(self, instance):
        result = super(SessionDetailsSerializer, self).to_representation(instance)
        return serializers.OrderedDict(
            [
                (
                    key,
                    result[key]
                    if result[key] is not None
                    else serializers.OrderedDict([]),
                )
                for key in result
            ]
        )

    class Meta:
        model = models.Session
        fields = [
            "id",
            "url",
            "last_update_time",
            "source",
            "current_conflict",
            "conflicts",
            "changes",
            "instructions",
            "deployments",
        ]
