import boto3
import json
import redis
import os

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1') # multi-region support

# Redis initialization
try:
    redis_endpoint = os.environ['REDIS_ENDPOINT']
    redis_client = redis.Redis(
        host=redis_endpoint,
        port=6379,
        decode_responses=True,
        ssl=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    redis_available = True
    print("Successfully connected to Redis")
except Exception as e:
    print(f"Redis connection error: {e}")
    redis_available = False

def check_conflicts(start_time, end_time, appointments):
    """Helper function to check for conflicts with more detailed logging"""
    for appt in appointments:
        # Log appointment we're checking against
        print(f"Checking against appointment: {appt['AppointmentID']}, Time: {appt['StartTime']}-{appt['EndTime']}")
        
        # Case 1: New appointment start time falls within existing appointment
        if start_time >= appt['StartTime'] and start_time <= appt['EndTime']:
            print(f"CONFLICT: New start time {start_time} falls within existing appointment {appt['StartTime']}-{appt['EndTime']}")
            return True
            
        # Case 2: New appointment end time falls within existing appointment
        if end_time >= appt['StartTime'] and end_time <= appt['EndTime']:
            print(f"CONFLICT: New end time {end_time} falls within existing appointment {appt['StartTime']}-{appt['EndTime']}")
            return True
            
        # Case 3: New appointment completely encompasses existing appointment
        if start_time <= appt['StartTime'] and end_time >= appt['EndTime']:
            print(f"CONFLICT: New appointment {start_time}-{end_time} encompasses existing appointment {appt['StartTime']}-{appt['EndTime']}")
            return True
    
    print("No conflicts found")
    return False

def lambda_handler(event, context):
    # Get doctor ID and appointment details from event
    doctor_id = event.get('DoctorID')
    appointment_date = event.get('AppointmentDate')
    start_time = event.get('StartTime')
    end_time = event.get('EndTime')
    
    print(f"Checking availability for Dr. {doctor_id} on {appointment_date} from {start_time} to {end_time}")
    
    # Create cache keys
    doctor_cache_key = f"doctor:{doctor_id}"
    appointments_cache_key = f"appointments:{doctor_id}:{appointment_date}"
    availability_result_key = f"availability:{doctor_id}:{appointment_date}:{start_time}:{end_time}"
    
    # ALWAYS check DynamoDB first for fresh appointment data, cache results for later
    # This ensures we don't miss newly created appointments
    appointments_table = dynamodb.Table('Appointments')
    
    try:
        # Get fresh appointment data from DynamoDB
        print(f"Checking latest appointments directly from DynamoDB")
        appointment_response = appointments_table.scan(
            FilterExpression='DoctorID = :doctor_id AND AppointmentDate = :date',
            ExpressionAttributeValues={
                ':doctor_id': doctor_id,
                ':date': appointment_date
            }
        )
        
        # Get the latest appointments data
        appointments = appointment_response.get('Items', [])
        print(f"Found {len(appointments)} appointments in DynamoDB")
        
        # Update cache with fresh appointment data
        if redis_available:
            try:
                redis_client.setex(appointments_cache_key, 600, json.dumps(appointments))
                print(f"Updated appointments cache with fresh data")
            except Exception as e:
                print(f"Cache storage error: {e}")
        
        # Now check for conflicts with the fresh data
        has_conflicts = check_conflicts(start_time, end_time, appointments)
        
        # If we found conflicts, doctor is not available
        if has_conflicts:
            result = {
                'statusCode': 409,
                'body': json.dumps('Doctor is not available at the requested time')
            }
            
            # Cache negative result
            if redis_available:
                try:
                    redis_client.setex(availability_result_key, 600, json.dumps(result))
                except Exception as e:
                    print(f"Cache storage error: {e}")
            
            print(f"Returning 409 - Doctor not available")
            return result
        
        # No conflicts, now get doctor details
        doctors_table = dynamodb.Table('Doctors')
        doctor_response = doctors_table.get_item(
            Key={
                'DoctorID': doctor_id
            }
        )
        
        if 'Item' not in doctor_response:
            result = {
                'statusCode': 404,
                'body': json.dumps(f'Doctor with ID {doctor_id} not found')
            }
            
            if redis_available:
                try:
                    redis_client.setex(availability_result_key, 300, json.dumps(result))
                except Exception as e:
                    print(f"Cache storage error: {e}")
            return result
        
        # Cache doctor details
        doctor_data = doctor_response['Item']
        if redis_available:
            try:
                redis_client.setex(doctor_cache_key, 1800, json.dumps(doctor_data))
            except Exception as e:
                print(f"Cache storage error: {e}")
        
        # Doctor is available
        result = {
            'statusCode': 200,
            'body': json.dumps('Doctor is available'),
            'doctorDetails': doctor_data
        }
        
        # Cache positive result (short TTL)
        if redis_available:
            try:
                # Short TTL (1 minute) for positive results to reduce chance of race conditions
                redis_client.setex(availability_result_key, 60, json.dumps(result))
            except Exception as e:
                print(f"Cache storage error: {e}")
        
        print(f"Returning 200 - Doctor is available")
        return result
    except Exception as e:
        error_result = {
            'statusCode': 500,
            'body': json.dumps(f'Error checking doctor availability: {str(e)}')
        }
        print(f"Error: {str(e)}")
        return error_result
