import boto3
import json
from datetime import datetime, timedelta

def lambda_handler(event, context):
    # Initialize clients
    sns = boto3.client('sns')
    dynamodb = boto3.resource('dynamodb')
    
    # Calculate tomorrow's date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Query appointments for tomorrow
    appointments_table = dynamodb.Table('Appointments')
    response = appointments_table.scan(
        FilterExpression='AppointmentDate = :date',
        ExpressionAttributeValues={
            ':date': tomorrow
        }
    )
    
    appointments = response.get('Items', [])
    print(f"Found {len(appointments)} appointments for tomorrow")
    
    patients_table = dynamodb.Table('Patients')
    doctors_table = dynamodb.Table('Doctors')
    
    # Send reminder for each appointment
    for appointment in appointments:
        patient_id = appointment['PatientID']
        doctor_id = appointment['DoctorID']
        appointment_time = appointment.get('StartTime', '00:00')
        
        # Get patient and doctor details
        patient_data = patients_table.get_item(Key={'PatientID': patient_id})['Item']
        doctor_data = doctors_table.get_item(Key={'DoctorID': doctor_id})['Item']
        
        patient_email = patient_data['Email']
        doctor_email = doctor_data['Email']
        patient_name = f"{patient_data['FirstName']} {patient_data['LastName']}"
        doctor_name = f"Dr. {doctor_data['LastName']}"
        
        # Different messages for patient and doctor
        # Patient reminder - more detailed with preparation instructions
        patient_message = {
            "default": f"Reminder: Your appointment with {doctor_name} is tomorrow at {appointment_time}.",
            "email": f"""
            Appointment Reminder
            Dear {patient_name},
            This is a friendly reminder about your appointment with {doctor_name} tomorrow ({tomorrow}) at {appointment_time}.
            Please remember to:
                Bring your insurance card
                Arrive 15 minutes early
                Bring a list of current medications
            If you need to reschedule, please call us at least 4 hours in advance.
            """
        }
        
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:990308236413:AppointmentNotification',
            Message=json.dumps(patient_message),
            Subject=f"Reminder: Your appointment tomorrow at {appointment_time}",
            MessageStructure='json',
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': patient_email
                },
                'recipient_type': {
                    'DataType': 'String',
                    'StringValue': 'patient'  # or 'patient'
                },
                'notification_type': {
                    'DataType': 'String',
                    'StringValue': 'reminder'
                }
            }
        )
        
        # Doctor reminder - briefer with patient details
        doctor_message = {
            "default": f"Reminder: Appointment with {patient_name} tomorrow at {appointment_time}.",
            "email": f"""
            Appointment Reminder
            Dear {doctor_name},
            You have an appointment scheduled with {patient_name} tomorrow ({tomorrow}) at {appointment_time}.
            Patient records are available in your portal.
            """
        }
        
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:990308236413:AppointmentNotification',
            Message=json.dumps(doctor_message),
            Subject=f"Reminder: Appointment with {patient_name} tomorrow",
            MessageStructure='json',
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': doctor_email
                },
                'recipient_type': {
                    'DataType': 'String',
                    'StringValue': 'doctor'  # or 'patient'
                },
                'notification_type': {
                    'DataType': 'String',
                    'StringValue': 'reminder'
                }
            }
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Sent {len(appointments)*2} reminder notifications')
    }
