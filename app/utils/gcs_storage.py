from google.cloud import storage


class GCSStorage:
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def upload_file(self, file_path: str, gcs_path: str):
        """
        Uploads a file to Google Cloud Storage.
        """

        blob = self.bucket.blob(gcs_path)
        blob.upload_from_filename(file_path)

    def upload_text(self, text: str, gcs_path: str, content_type="text/plain"):
        """
        Uploads a text string to Google Cloud Storage.
        """

        blob = self.bucket.blob(gcs_path)
        blob.upload_from_string(text, content_type=content_type)

    def download_text(self, gcs_path: str):
        """
        Downloads a text string from Google Cloud Storage.
        """

        blob = self.bucket.blob(gcs_path)
        if not blob.exists():
            return None
        return blob.download_as_text()

    def exists(self, gcs_path: str) -> bool:
        """
        Checks if a file exists in Google Cloud Storage.
        """

        blob = self.bucket.blob(gcs_path)
        return blob.exists()

    def delete_object(self, gcs_path: str):
        """
        Deletes a file from Google Cloud Storage.
        """

        blob = self.bucket.blob(gcs_path)
        if blob.exists():
            blob.delete()

    def list_blobs(self, prefix: str):
        """
        Lists all blobs in the bucket with the given prefix.
        """

        return list(self.client.list_blobs(self.bucket, prefix=prefix))
