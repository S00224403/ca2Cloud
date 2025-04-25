import boto3
import json
import uuid

# Initialize DynamoDB and Step Functions clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1') # multi-region support
stepfunctions = boto3.client('stepfunctions', region_name='us-east-1')

def lambda_handler(event, context):
    try:
        # Parse the incoming event (from API Gateway)
        if 'body' in event and event['body']:
            payload = json.loads(event['body'])
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid request format"})
            }
        stage_vars = event.get('stageVariables', {})
        lambda_alias = stage_vars.get('lambdaAlias', 'dev')   # default to 'dev' if not set
        table_name = stage_vars.get('tableName', 'AppointmentsDev')

        print(f"Stage Lambda Alias: {lambda_alias}")
        print(f"Stage Table Name: {table_name}")    
        # Extract appointment details
        appointment_id = event.get('AppointmentID', f'A{str(uuid.uuid4())[:8]}')
        patient_id = payload['PatientID']
        doctor_id = payload['DoctorID']
        appointment_date = payload['AppointmentDate']
        start_time = payload['StartTime']
        end_time = payload['EndTime']
        
        # Create input for Step Function
        step_function_input = {
            "AppointmentID": appointment_id,
            "PatientID": patient_id,
            "DoctorID": doctor_id,
            "AppointmentDate": appointment_date,
            "StartTime": start_time,
            "EndTime": end_time
        }
        
        # Start Step Function execution
        step_function_arn = "arn:aws:states:us-east-1:990308236413:stateMachine:CloudAssignment2"
        
        response = stepfunctions.start_execution(
            stateMachineArn=step_function_arn,
            input=json.dumps(step_function_input)
        )
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({"message": "Appointment booked! Check email for confirmation"})
        }
    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing required field: {str(e)}"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
