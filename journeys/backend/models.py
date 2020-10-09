import json
import os

from django.db import models

from ..workdir import WORKDIR


class SystemCredentials(models.Model):
    username = models.CharField(max_length=64)
    password = models.CharField(
        max_length=64
    )  # TODO: do not store password in the database
    host = models.CharField(max_length=64)


class Source(models.Model):
    has_ucs = models.BooleanField()
    has_as3 = models.BooleanField()
    credentials = models.ForeignKey(
        to=SystemCredentials,
        related_name="credentials",
        on_delete=models.PROTECT,
        null=True,
    )


class Session(models.Model):
    last_update_time = models.DateTimeField(auto_now=True)
    source = models.ForeignKey(to=Source, on_delete=models.PROTECT, null=True)
    current_conflict = models.CharField(max_length=128, null=True)
    instructions = models.TextField(null=True)

    @property
    def working_directory(self) -> str:
        return os.path.join(WORKDIR, str(self.id))  # pylint: disable=E1101


class Conflict(models.Model):
    name = models.CharField(max_length=32)
    summary = models.CharField(max_length=4096)
    session = models.ForeignKey(
        to=Session, related_name="conflicts", on_delete=models.PROTECT
    )

    class Meta:
        unique_together = (("name", "session"),)


class Mitigation(models.Model):
    name = models.CharField(max_length=512)
    conflict = models.ForeignKey(
        to=Conflict, related_name="mitigations", on_delete=models.PROTECT
    )
    session = models.ForeignKey(
        to=Session, related_name="mitigations", on_delete=models.PROTECT
    )


class File(models.Model):
    path = models.CharField(max_length=512)
    session = models.ForeignKey(
        to=Session, related_name="files", on_delete=models.PROTECT
    )
    conflict = models.ForeignKey(
        to=Conflict, related_name="files", on_delete=models.PROTECT, null=True
    )
    mitigation = models.ForeignKey(
        to=Mitigation, related_name="files", on_delete=models.PROTECT, null=True
    )


class Change(models.Model):
    session = models.ForeignKey(
        to=Session, related_name="changes", on_delete=models.PROTECT
    )
    message = models.CharField(max_length=512)
    commit = models.CharField(max_length=64)
    content = models.TextField()


class Deployment(models.Model):
    session = models.ForeignKey(
        to=Session, related_name="deployments", on_delete=models.PROTECT
    )
    source = models.ForeignKey(
        to=SystemCredentials, related_name="source", on_delete=models.PROTECT, null=True
    )
    destination = models.ForeignKey(to=SystemCredentials, on_delete=models.PROTECT)
    validators_json = models.TextField()
    status = models.CharField(
        max_length=11,
        choices=(("in_progress", "in_progress"), ("finished", "finished")),
    )

    @property
    def validators(self):
        return json.loads(self.validators_json)

    @validators.setter
    def validators(self, validators):
        self.validators_json = json.dumps(validators)


class DeploymentResult(models.Model):
    time = models.DateTimeField(auto_created=True)
    message = models.CharField(max_length=4096)
    deployment = models.ForeignKey(
        to=Deployment, related_name="results", on_delete=models.PROTECT
    )
