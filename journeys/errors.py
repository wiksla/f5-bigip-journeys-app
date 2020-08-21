class ControllerError(RuntimeError):
    pass


class ArchiveOpenError(ControllerError):
    pass


class ArchiveDecryptError(ControllerError):
    pass
