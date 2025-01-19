import logging

# Configure root logger for AWS package
logging.getLogger('AWS').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
