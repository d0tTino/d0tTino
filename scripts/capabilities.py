from enum import Enum


class Capability(str, Enum):
    """Enumerate capability scopes supported by ``execute_steps``."""

    FILESYSTEM_READ = "filesystem.read"
    PROCESS_EXEC = "process.exec"
    NETWORK_FETCH = "network.fetch"


ALL_CAPABILITIES = {
    Capability.FILESYSTEM_READ,
    Capability.PROCESS_EXEC,
    Capability.NETWORK_FETCH,
}
