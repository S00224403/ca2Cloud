import json
import boto3

# Initialize clients
sns = boto3.client('sns')

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    for record in event['Records']:
        try:
            # Extract message from SQS
            message_body = record['body']
            print(f"Processing message body: {message_body}")
            
            message_data = json.loads(message_body)
            
            # Extract details with names
            patient_name = message_data.get('PatientName', 'Patient')
            doctor_name = message_data.get('DoctorName', 'Doctor')
            appointment_date = message_data.get('AppointmentDate')
            start_time = message_data.get('StartTime', '00:00')
            message_type = message_data.get('MessageType')
            recipient_type = message_data.get('RecipientType')
            
            # SNS topic ARN
            topic_arn = "arn:aws:sns:us-east-1:990308236413:AppointmentNotification" # same for both regions
            
            if message_type == 'Notification':
                if recipient_type == 'patient':
                    # Patient notification
                    message = f"Dear {patient_name},\n\nYour appointment with {doctor_name} has been confirmed for {appointment_date} at {start_time}.\n\nPlease arrive 15 minutes early and bring your insurance card."
                    subject = f"Appointment Confirmation for {appointment_date}"
                elif recipient_type == 'doctor':
                    # Doctor notification
                    message = f"Dear {doctor_name},\n\nA new appointment has been scheduled with {patient_name} on {appointment_date} at {start_time}.\n\nPlease review patient details in your system."
                    subject = f"New Appointment: {patient_name} on {appointment_date}"
                else:
                    continue
                
                # Send notification via SNS with recipient filtering
                sns.publish(
                    TopicArn=topic_arn,
                    Message=message,
                    Subject=subject,
                    MessageAttributes={
                        'recipient_type': {
                            'DataType': 'String',
                            'StringValue': recipient_type
                        }
                    }
                )
                print(f"Sent {recipient_type} notification for appointment on {appointment_date}")
                
            elif message_type == 'Reminder':
                # Similar logic for reminders
                if recipient_type == 'patient':
                    message = f"Dear {patient_name},\n\nThis is a reminder about your appointment with {doctor_name} tomorrow ({appointment_date}) at {start_time}."
                    subject = f"Appointment Reminder for Tomorrow"
                elif recipient_type == 'doctor':
                    message = f"Dear {doctor_name},\n\nThis is a reminder about your appointment with {patient_name} tomorrow ({appointment_date}) at {start_time}."
                    subject = f"Appointment Reminder: {patient_name} Tomorrow"
                else:
                    continue
                
                sns.publish(
                    TopicArn=topic_arn,
                    Message=message,
                    Subject=subject,
                    MessageAttributes={
                        'recipient_type': {
                            'DataType': 'String',
                            'StringValue': recipient_type
                        }
                    }
                )
                print(f"Sent {recipient_type} reminder for appointment on {appointment_date}")
            else:
                print(f"Unknown message type: {message_type}")

        except Exception as e:
            print(f"Error processing record: {record.get('messageId')}")
            print(f"Error: {str(e)}")
            raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed messages.')
    }
