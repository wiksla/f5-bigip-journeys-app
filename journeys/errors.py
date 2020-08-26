class ControllerError(RuntimeError):
    pass


class ArchiveOpenError(ControllerError):
    pass


class ArchiveDecryptError(ControllerError):
    pass


class NotMasterBranchError(ControllerError):
    pass


class DifferentUcsError(ControllerError):
    pass


class DifferentConflictError(ControllerError):
    def __init__(self, conflict_id):
        self.conflict_id = conflict_id


class UnknownConflictError(ControllerError):
    pass


class ConflictNotResolvedError(ControllerError):
    def __init__(self, conflict_id, conflict_info):
        self.conflict_id = conflict_id
        self.conflict_info = conflict_info


class NotAllConflictResolvedError(ControllerError):
    pass
