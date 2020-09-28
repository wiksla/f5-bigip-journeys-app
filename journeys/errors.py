from typing import List


class ControllerError(RuntimeError):
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


class AS3InputDoesNotExistError(ControllerError):
    def __init__(self):
        pass


class SSHConnection(Exception):
    pass


class DeviceAuthenticationError(SSHConnection):
    def __init__(self, host: str, ssh_username: str):
        self.host = host
        self.ssh_username = ssh_username


class NetworkConnectionError(SSHConnection):
    pass
