import re
from typing import List


class JourneysError(Exception):
    """Base for journeys errors."""

    pass


class ControllerError(JourneysError):
    pass


class AlreadyInitializedError(ControllerError):
    pass


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


class InputFileNotExistError(ControllerError, InputError):
    def __init__(self, input_name: str, file_ext=""):
        msg = f'File "{input_name}" not found!'
        if file_ext:
            msg = f"{file_ext} {msg}"
        super().__init__(msg)


class AS3InputDoesNotExistError(InputFileNotExistError):
    def __init__(self, input_name):
        super().__init__(input_name=input_name, file_ext="AS3")


class UcsInputDoesNotExistError(InputFileNotExistError):
    def __init__(self, input_name):
        super().__init__(input_name=input_name, file_ext="UCS")


class ValidationError(JourneysError):
    pass


class CoreDumpValidatorError(ValidationError):
    pass


class BigDbError(JourneysError):
    def __init__(self, message):
        error_info_data = re.findall(r"'([^']*)'", message)
        option = None
        try:
            file_path, option, section = error_info_data
        except ValueError:
            file_path, section = error_info_data

        option_str = f" option '{option}' in" if option else ""
        msg = f"Please remove duplicated element manually:{option_str} section '{section}' from '{file_path}'"
        super().__init__(msg)
