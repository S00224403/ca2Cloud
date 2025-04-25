import json
import boto3
import redis
import os

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb') # region specific

# More robust Redis initialization
try:
    redis_endpoint = os.environ['REDIS_ENDPOINT']
    redis_client = redis.Redis(
        host=redis_endpoint,
        port=6379,
        decode_responses=True,
        ssl=True,  # Enable SSL/TLS
        socket_timeout=5,  # Add timeouts to prevent hanging
        socket_connect_timeout=5
    )
    # Test connection immediately
    redis_client.ping()
    redis_available = True
    print("Successfully connected to Redis")
except Exception as e:
    print(f"Redis connection error: {e}")
    redis_available = False

def lambda_handler(event, context):
    patient_id = event.get('PatientID')
    cache_key = f"patient:{patient_id}"
    
    # Try cache first, if available
    if redis_available:
        try:
            cached_patient = redis_client.get(cache_key)
            if cached_patient:
                print("Cache HIT for patient data")
                return {
                    'statusCode': 200,
                    'body': json.dumps('Patient verified successfully'),
                    'patientDetails': json.loads(cached_patient)
                }
        except Exception as e:
            print(f"Cache retrieval error: {e}")
    
    # If cache miss or unavailable, query DynamoDB
    print("Cache MISS for patient data")
    patients_table = dynamodb.Table('Patients')
    print(f"About to query DynamoDB for patient {patient_id}")
    response = patients_table.get_item(Key={'PatientID': patient_id})
    print(f"DynamoDB response received: {response}")
    
    if 'Item' in response:
        # Try to store in cache for future requests if Redis is available
        if redis_available:
            try:
                redis_client.setex(cache_key, 86400, json.dumps(response['Item']))
            except Exception as e:
                print(f"Cache storage error: {e}")
                
        return {
            'statusCode': 200,
            'body': json.dumps('Patient verified successfully'),
            'patientDetails': response['Item']
        }
    else:
        return {
            'statusCode': 404,
            'body': json.dumps(f'Patient with ID {patient_id} not found')
        }
