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
