# A simple in-memory store for job statuses.
# In a production environment, this would be replaced with Redis or a database table.
job_statuses = {}

def set_job_status(job_id: str, status: str):
    """Sets the status of a generation job."""
    job_statuses[job_id] = status

def get_job_status(job_id: str) -> str:
    """Gets the status of a generation job."""
    return job_statuses.get(job_id, "not_found")