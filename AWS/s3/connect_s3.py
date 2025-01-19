import os
import configparser
import boto3
from botocore.exceptions import ClientError
import json
from dotenv import load_dotenv
import logging
import streamlit as st

# Configure logging
logger = logging.getLogger("AWS.s3.connect_s3")
logger.setLevel(logging.WARNING)  # Change level to WARNING to reduce non-essential messages

class S3Manager:
    """Manages interactions with AWS S3 bucket."""
    
    def __init__(self):
        """
        Initialize S3 client using configuration file or environment variables.
        """
        # Try to get credentials from various sources
        self.aws_access_key_id = None
        self.aws_secret_access_key = None
        self.region = None
        self.bucket_name = None
        
        # 1. Try environment variables
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = os.getenv('AWS_REGION')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        
        # 2. Try .env file if environment variables are not set
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.region, self.bucket_name]):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            env_path = os.path.join(current_dir, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
                self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
                self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                self.region = os.getenv('AWS_REGION')
                self.bucket_name = os.getenv('S3_BUCKET_NAME')
        
        # Verify we have all required credentials
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.region, self.bucket_name]):
            logger.error("Missing AWS credentials!")
            missing_vars = []
            if not self.aws_access_key_id: missing_vars.append('AWS_ACCESS_KEY_ID')
            if not self.aws_secret_access_key: missing_vars.append('AWS_SECRET_ACCESS_KEY')
            if not self.region: missing_vars.append('AWS_REGION')
            if not self.bucket_name: missing_vars.append('S3_BUCKET_NAME')
            raise ValueError(f"Missing AWS credentials: {', '.join(missing_vars)}")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region
        )

    def upload_file(self, file_path, s3_key=None):
        """
        Upload a file to S3 bucket.
        
        Args:
            file_path (str): Local path to the file
            s3_key (str, optional): The key to use in S3. If None, uses filename
        
        Returns:
            bool: True if file was uploaded, else False
        """
        if s3_key is None:
            s3_key = os.path.basename(file_path)
            
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            return True
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return False

    def download_file(self, s3_key, local_path):
        """
        Download a file from S3 bucket.
        
        Args:
            s3_key (str): The key of the file in S3
            local_path (str): Local path where to save the file
        
        Returns:
            bool: True if file was downloaded, else False
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {str(e)}")
            return False

    def list_files(self, prefix=""):
        """
        List files in the S3 bucket.
        
        Args:
            prefix (str): Only list objects beginning with prefix
        
        Returns:
            list: List of object keys in the bucket
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError as e:
            logger.error(f"Error listing files in S3: {str(e)}")
            return []

    def delete_file(self, s3_key):
        """
        Delete a file from S3 bucket.
        
        Args:
            s3_key (str): The key of the file to delete
        
        Returns:
            bool: True if file was deleted, else False
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False

    def file_exists(self, s3_key):
        """
        Check if a file exists in the S3 bucket.
        
        Args:
            s3_key (str): The key of the file to check
        
        Returns:
            bool: True if file exists, else False
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

    def get_file_size(self, s3_key):
        """
        Get the size of a file in S3 bucket.
        
        Args:
            s3_key (str): The key of the file
        
        Returns:
            int: Size of the file in bytes, or None if file doesn't exist
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return response['ContentLength']
        except ClientError:
            return None

    def upload_json(self, data, s3_key):
        """
        Upload JSON data directly to S3.
        
        Args:
            data: The data to serialize to JSON
            s3_key (str): The key to use in S3
            
        Returns:
            bool: True if data was uploaded, else False
        """
        try:
            json_data = json.dumps(data)
            self.s3_client.put_object(
                Body=json_data,
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except (ClientError, TypeError) as e:
            logger.error(f"Error uploading JSON to S3: {str(e)}")
            return False

    def save_ai_results(self, model_type, results, filename=None, timestamp=None):
        """
        Save AI model results to specific S3 folders.
        
        Args:
            model_type (str): Type of AI model (e.g., 'clustering', 'recommender')
            results: Results to save (can be dict, DataFrame, or other serializable object)
            filename (str, optional): Custom filename. If None, will be auto-generated
            timestamp (str, optional): Timestamp to use in filename. If None, current time used
            
        Returns:
            str: S3 key where results were saved
        """
        import datetime
        import pandas as pd
        
        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
        # Generate filename if not provided
        if filename is None:
            filename = f"{model_type}_results_{timestamp}.json"
            
        # Construct S3 key
        s3_key = f"AI/{model_type}/{filename}"
        
        # Convert results to appropriate format
        if isinstance(results, pd.DataFrame):
            # For DataFrames, save as CSV
            local_path = f"/tmp/{filename}.csv"
            results.to_csv(local_path, index=False)
        else:
            # For other objects, save as JSON
            local_path = f"/tmp/{filename}"
            with open(local_path, 'w') as f:
                json.dump(results, f)
                
        # Upload to S3
        success = self.upload_file(local_path, s3_key)
        
        # Clean up temporary file
        if os.path.exists(local_path):
            os.remove(local_path)
            
        if success:
            return s3_key
        return None

    def upload_with_overwrite(self, file_path, s3_key):
        """
        Upload a file to S3 bucket, overwriting if it already exists.
        
        Args:
            file_path (str): Local path to the file
            s3_key (str): The key to use in S3
            
        Returns:
            bool: True if file was uploaded, else False
        """
        try:
            # Vérifier si le fichier existe
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    pass
                else:
                    raise e
                    
            # Upload le fichier (écrase si existe)
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return False