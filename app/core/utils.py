def get_status(status: str) -> PipelineStatus:
    if status.lower() == "queued":
        return PipelineStatus.QUEUED
    if status.lower() == "running":
        return PipelineStatus.RUNNING
    if status.lower() == "success":
        return PipelineStatus.SUCCESS
    if status.lower() == "failed":
        return PipelineStatus.FAILURE