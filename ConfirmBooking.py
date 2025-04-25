import boto3
import json
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1') # us-east-1 and us-west-2 specific

def lambda_handler(event, context):
    # Get appointment details from event
    patient_id = event.get('PatientID')
    doctor_id = event.get('DoctorID')
    appointment_date = event.get('AppointmentDate')
    start_time = event.get('StartTime')
    end_time = event.get('EndTime')
    
    # Generate a unique appointment ID if not provided
    appointment_id = event.get('AppointmentID', f'A{str(uuid.uuid4())[:8]}')
    
    # Access DynamoDB table
    appointments_table = dynamodb.Table('Appointments')
    
    try:
        # Create appointment in DynamoDB
        response = appointments_table.put_item(
            Item={
                'AppointmentID': appointment_id,
                'PatientID': patient_id,
                'DoctorID': doctor_id,
                'AppointmentDate': appointment_date,
                'StartTime': start_time,
                'EndTime': end_time,
                'AppointmentStatus': 'Confirmed',
                'CreatedAt': datetime.now().isoformat()
            }
        )
        
        return {
            'statusCode': 201,
            'body': json.dumps('Appointment confirmed successfully'),
            'appointmentDetails': {
                'AppointmentID': appointment_id,
                'PatientID': patient_id,
                'DoctorID': doctor_id,
                'AppointmentDate': appointment_date,
                'AppointmentStatus': 'Confirmed'
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error confirming appointment: {str(e)}')
        }
