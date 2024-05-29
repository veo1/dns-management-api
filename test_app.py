import os
import pytest
from flask.testing import FlaskClient
from app import app  

# Set environment variables for testing
os.environ['AWS_ACCESS_KEY_ID'] = 'fake_access_key_id'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fake_secret_access_key'
os.environ['HOSTED_ZONE_ID'] = 'fake_hosted_zone_id'
os.environ['SECRET_TOKEN'] = 'fake_secret_token'
os.environ['TTL'] = '300'
os.environ['RECORD_TYPE'] = 'A'
os.environ['DEBUG_MODE'] = 'false'

@pytest.fixture
def client() -> FlaskClient:
    with app.test_client() as client:
        yield client

def test_health(client: FlaskClient):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_update_dns(client: FlaskClient, mocker):
    # Mock the boto3 client
    mock_route53 = mocker.patch('app.route53')
    mock_route53.change_resource_record_sets.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

    # Test data
    data = {
        'token': 'fake_secret_token',
        'dns_name': 'test.example.com',
        'ip_address': '192.168.1.1'
    }

    response = client.post('/update-dns', json=data)
    assert response.status_code == 200
    assert response.json['message'] == 'DNS record updated successfully'

# test_delete_dns is not implemented due to mocker limitations, TBA
   
def test_invalid_token(client: FlaskClient):
    data = {
        'token': 'invalid_token',
        'dns_name': 'test.example.com',
        'ip_address': '192.168.1.1'
    }

    response = client.post('/update-dns', json=data)
    assert response.status_code == 403
    assert response.json['error'] == 'Invalid token'

def test_missing_token(client: FlaskClient):
    data = {
        'dns_name': 'test.example.com',
        'ip_address': '192.168.1.1'
    }

    response = client.post('/update-dns', json=data)
    assert response.status_code == 400
    assert 'token' in response.json['details']

def test_invalid_input(client: FlaskClient):
    data = {
        'token': 'fake_secret_token',
        'dns_name': 'test.example.com',
        'ip_address': 'invalid_ip'
    }

    response = client.post('/update-dns', json=data)
    assert response.status_code == 400
    assert 'ip_address' in response.json['details']

if __name__ == '__main__':
    pytest.main()
