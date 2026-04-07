BUCKET_UPLOADS = "danloo-uploads"
BUCKET_RESULTS = "danloo-results"

uploads_object_key_pattern = "{user_id}/{upload_date}/{object_id}/{filename}"
results_object_key_pattern = (
    "{user_id}/{upload_date}/{object_id}/{filename}.results.txt"
)


def format_upload_object_key(
    user_id: str, upload_date: str, object_id: str, filename: str
):
    object_key = (
        uploads_object_key_pattern.replace("{user_id}", user_id)
        .replace("{upload_date}", upload_date)
        .replace("{object_id}", object_id)
        .replace("{filename}", filename)
    )
    return object_key
