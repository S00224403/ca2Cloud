import boto3
import json

# Initialize SQS client
sqs = boto3.client('sqs')

def lambda_handler(event, context):
    # Queue URL from your SQS queue
    queue_url = "https://sqs.us-east-1.amazonaws.com/990308236413/NotificationQueue" # queue remains same across both regions
    
    try:
        # Extract names from the event
        patient_first_name = event['verifyResult']['patientDetails']['FirstName']
        patient_last_name = event['verifyResult']['patientDetails']['LastName']
        patient_full_name = f"{patient_first_name} {patient_last_name}"
        
        doctor_first_name = event['availabilityResult']['doctorDetails']['FirstName']
        doctor_last_name = event['availabilityResult']['doctorDetails']['LastName']
        doctor_full_name = f"{doctor_first_name} {doctor_last_name}"
        
        # Create separate messages for patient and doctor notifications
        patient_message = {
            "PatientID": event['PatientID'],
            "PatientName": patient_full_name,
            "DoctorID": event['DoctorID'],
            "DoctorName": doctor_full_name,
            "AppointmentDate": event['AppointmentDate'],
            "StartTime": event['StartTime'],
            "RecipientType": "patient",
            "MessageType": "Notification"
        }
        
        doctor_message = {
            "PatientID": event['PatientID'],
            "PatientName": patient_full_name,
            "DoctorID": event['DoctorID'],
            "DoctorName": doctor_full_name,
            "AppointmentDate": event['AppointmentDate'],
            "StartTime": event['StartTime'],
            "RecipientType": "doctor",
            "MessageType": "Notification"
        }

        # Send both messages to SQS
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(patient_message)
        )
        
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(doctor_message)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Notifications queued successfully')
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error queueing notifications: {str(e)}')
        }
