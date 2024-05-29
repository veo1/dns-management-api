# Flask DNS Management API

This Flask application provides a RESTful API for managing DNS records using AWS Route 53. It supports creating/updating (`UPSERT`) and deleting DNS records. The application includes rate limiting for easy API exploration and testing.

### Features
- Create/Update DNS records
- Delete DNS records
- Rate limiting to prevent abuse
- Health check endpoint

### Prerequisites
- Python 3.9+
- AWS account with Route 53 hosted zone
- Docker (optional, for containerized deployment)

### Setup

#### 1. Clone the Repository
```bash
git clone git@github.com:veo1/dns-management-api.git
cd dns-management-api
```

#### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Set Up Environment Variables
Create a .env file in the project root and populate it with your configuration:
```bash
DEBUG=True
AWS_ACCESS_KEY_ID=aws_access_key_id
AWS_SECRET_ACCESS_KEY=aws_secret_access_key
AWS_REGION=us-east-1
SECRET_TOKEN=secret_token
HOSTED_ZONE_ID=hosted_zone_id
TTL=300
RECORD_TYPE=A
```

### Running the Application

#### 1. Run the Flask Application
```bash
python app.py
```

#### 2. Access the Application
Send the requests to https://localhost:5000/


### Docker Deployment

#### 1. Build the Docker Image
```bash
docker build -t dns-management-api .
```

#### 2. Run the Docker Container
```bash
docker run -p 5000:5000 --env-file .env dns-management-api
```

### API Endpoints

#### 1. Update DNS Record
- URL: `/update-dns`
- Method: `POST`
- Payload:
```bash
{
  "token": "secret_token",
  "dns_name": "example.com", # Optional if ip_address is provided
  "ip_address": "192.168.1.1" # Optional if dns_name is provided
}
```
- Response:
- - `200 OK`: DNS record updated successfully
- - `400 Bad Request`: Invalid input
- - `403 Forbidden`: Invalid token
- - `500 Internal Server Error`: Server error

#### 2. Delete DNS Record
- URL: `/delete-dns`
- Method: `DELETE`
- Payload:
```bash
{
  "token": "secret_token",
  "dns_name": "example.com", # Optional if ip_address is provided
  "ip_address": "192.168.1.1" # Optional if dns_name is provided
}
```
- Response:
- - `200 OK`: DNS record deleted successfully
- - `400 Bad Request`: Invalid input
- - `403 Forbidden`: Invalid token
- - `500 Internal Server Error`: Server error

#### 3. Health Check

- URL: `/health`
- Method: `GET`
- Response:
- - `200 OK`: {"status": "ok"}


### Security
- Rate Limiting: The application uses `flask-limiter` to limit the number of requests to prevent abuse.
- Token-Based Authentication: Requests to update and delete DNS records require a valid secret token.


### Logging
The application uses Python's built-in logging module to log information, warnings, and errors.

### License
This project is licensed under the MIT License.
