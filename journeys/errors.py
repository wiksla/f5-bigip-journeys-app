from typing import List


class JourneysError(Exception):
    """Base for journeys errors."""

    pass


class ControllerError(JourneysError):
    pass


class AlreadyInitializedError(ControllerError):
    def __init__(self, input):
        self.input = input


class ArchiveOpenError(ControllerError):
    pass


class ArchiveDecryptError(ControllerError):
    pass


class NotInitializedError(ControllerError):
    pass


class NotMasterBranchError(ControllerError):
    pass


class DifferentConflictError(ControllerError):
    def __init__(self, conflict_id):
        self.conflict_id = conflict_id


class UnknownConflictError(ControllerError):
    def __init__(self, conflict_id):
        self.conflict_id = conflict_id


class ConflictNotResolvedError(ControllerError):
    def __init__(
        self,
        conflict_id,
        conflict_info,
        working_directory,
        config_path,
        mitigation_branches,
    ):
        self.conflict_id = conflict_id
        self.conflict_info = conflict_info
        self.working_directory = working_directory
        self.config_path = config_path
        self.mitigation_branches = mitigation_branches


class NotAllConflictResolvedError(ControllerError):
    pass


class OutputAlreadyExistsError(ControllerError):
    def __init__(self, output):
        self.output = output


class LocalChangesDetectedError(ControllerError):
    def __init__(self, uncommitted: List[str]):
        self.uncommitted = uncommitted


class NotResolvingConflictError(ControllerError):
    pass


class AS3InputDoesNotExistError(ControllerError):
    def __init__(self):
        pass


class UcsActionError(ControllerError):
    def __init__(self, action_name="Ucs operation"):
        self.action_name = action_name
        pass


class SSHConnectionError(JourneysError):
    pass


class DeviceAuthenticationError(SSHConnectionError):
    def __init__(self, host: str, ssh_username: str):
        self.host = host
        self.ssh_username = ssh_username


class InputError(JourneysError):
    """Signifies an issue with user-specified configuration."""

    def __init__(self, msg: str):
        msg = f"Invalid input: {msg}"
        super().__init__(msg)
