import boto3
import json
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Archive appointments older than 6 months (using 1 day for demo)
    cutoff_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    appointments_table = dynamodb.Table('Appointments')
    
    # Scan for old appointments
    response = appointments_table.scan(
        FilterExpression='AppointmentDate < :cutoff',
        ExpressionAttributeValues={':cutoff': cutoff_date}
    )
    old_appointments = response.get('Items', [])
    
    if old_appointments:
        # Write to S3 (as a single file for demo)
        archive_key = f"archives/appointments-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json"
        s3.put_object(
            Bucket='s00224403-appointment-archive',
            Key=archive_key,
            Body=json.dumps(old_appointments)
        )
        
        # Delete from DynamoDB using composite key
        for item in old_appointments:
            appointments_table.delete_item(Key={
                'AppointmentID': item['AppointmentID'],
                'DoctorID': item['DoctorID']  # Include the sort key
            })
            
        return {"statusCode": 200, "body": f"Archived {len(old_appointments)} appointments to S3 Glacier and deleted from DynamoDB"}
    else:
        return {"statusCode": 200, "body": "No appointments to archive"}
