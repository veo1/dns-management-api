from flask import Flask, request, jsonify
import boto3
import os
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from cerberus import Validator
from lookup import get_ip_address, get_host_name

load_dotenv()  

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

route53 = boto3.client(
    'route53',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

schema = {
    'token': {'type': 'string', 'required': True},
    'dns_name': {'type': 'string', 'required': False},
    'ip_address': {'type': 'string', 'required': False, 'regex': r'^(\d{1,3}\.){3}\d{1,3}$'}
}

# Secret token for validating requests
SECRET_TOKEN = os.getenv('SECRET_TOKEN')

HOSTED_ZONE_ID = os.getenv('HOSTED_ZONE_ID')
TTL = int(os.getenv('TTL', 300))
RECORD_TYPE = os.getenv('RECORD_TYPE', 'A')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

@app.route('/update-dns', methods=['POST'])
@limiter.limit("10 per minute")  
def update_dns():
    data = request.get_json()
    
    logger.info(f"Received request: {data}")

    # Validate input data
    v = Validator(schema)
    if not v.validate(data):
        logger.error(f"Input validation failed: {v.errors}")
        return jsonify({'error': 'Invalid input', 'details': v.errors}), 400

    # Validate the request token
    token = data.get('token')
    if token != SECRET_TOKEN:
        logger.warning(f"Unauthorized access attempt with token: {token}")
        return jsonify({'error': 'Invalid token'}), 403

    dns_name = data.get('dns_name')
    ip_address = data.get('ip_address')
    
   # If IP address is missing, look it up using the DNS name
    if dns_name and not ip_address:
        try:
            ip_address = get_ip_address(dns_name)
        except Exception as e:
            logger.error(f"Failed to get IP address for DNS name {dns_name}: {e}")
        return jsonify({'error': f'Failed to get IP address for DNS name {dns_name}'}), 400
    elif ip_address and not dns_name:
        try:
            dns_name = get_host_name(ip_address)
        except Exception as e:
            logger.error(f"Failed to get DNS name for IP address {ip_address}: {e}")
        return jsonify({'error': f'Failed to get DNS name for IP address {ip_address}'}), 400
    
    # Upsert DNS record
    try:
        response = route53.change_resource_record_sets(
            HostedZoneId=HOSTED_ZONE_ID,
            ChangeBatch={
                'Comment': 'Automated DNS update',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': dns_name,
                            'Type': 'A',
                            'TTL': 300,
                            'ResourceRecords': [{'Value': ip_address}]
                        }
                    }
                ]
            }
        )
        logger.info(f"DNS record updated successfully: {response}")
        return jsonify({'message': 'DNS record updated successfully', 'response': response}), 200
    except route53.exceptions.ClientError as e:
        logger.error(f"ClientError updating DNS record: {e.response['Error']['Message']}")
        return jsonify({'error': e.response['Error']['Message']}), 500
    except Exception as e:
        logger.error(f"Unexpected error updating DNS record: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

app.route('/delete-dns', methods=['DELETE'])
@limiter.limit("10 per minute")
def delete_dns():
    data = request.get_json()
    logger.info(f"Received request: {data}")

    # Validate input data
    v = Validator(schema)
    if not v.validate(data):
        logger.error(f"Input validation failed: {v.errors}")
        return jsonify({'error': 'Invalid input', 'details': v.errors}), 400

    # Validate the request token
    token = data.get('token')
    if token != SECRET_TOKEN:
        logger.warning(f"Unauthorized access attempt with token: {token}")
        return jsonify({'error': 'Invalid token'}), 403

    dns_name = data.get('dns_name')
    ip_address = data.get('ip_address')
    
    # If IP address is missing, look it up using the DNS name and vice versa
    if dns_name and not ip_address:
        try:
            ip_address = get_ip_address(dns_name)
        except Exception as e:
            logger.error(f"Failed to get IP address for DNS name {dns_name}: {e}")
            return jsonify({'error': f'Failed to get IP address for DNS name {dns_name}'}), 400
    elif ip_address and not dns_name:
        try:
            dns_name = get_host_name(ip_address)
        except Exception as e:
            logger.error(f"Failed to get DNS name for IP address {ip_address}: {e}")
            return jsonify({'error': f'Failed to get DNS name for IP address {ip_address}'}), 400
    
    # Delete DNS record
    try:
        response = route53.change_resource_record_sets(
            HostedZoneId=HOSTED_ZONE_ID,
            ChangeBatch={
                'Comment': 'Automated DNS delete',
                'Changes': [
                    {
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': dns_name,
                            'Type': RECORD_TYPE,
                            'TTL': TTL,
                            'ResourceRecords': [{'Value': ip_address}]
                        }
                    }
                ]
            }
        )
        logger.info(f"DNS record deleted successfully: {response}")
        return jsonify({'message': 'DNS record deleted successfully', 'response': response}), 200
    except route53.exceptions.ClientError as e:
        logger.error(f"ClientError deleting DNS record: {e.response['Error']['Message']}")
        return jsonify({'error': e.response['Error']['Message']}), 500
    except Exception as e:
        logger.error(f"Unexpected error deleting DNS record: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    if not (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and HOSTED_ZONE_ID and SECRET_TOKEN):
        logger.error("Missing required environment variables. Exiting.")
        exit(1)
    
    app.run(debug=DEBUG_MODE)
