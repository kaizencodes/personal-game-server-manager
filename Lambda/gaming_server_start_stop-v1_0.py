# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0


import boto3
import json
import os


def lambda_handler(event, context): #standard function called on lambda invocation
    
    mcTagKey = event['mcTagName'] #This is the Tag for the resources we're looking to handle
    mcTagValue = event['mcTagValue'] #This is the Tag for the resources we're looking to handle
    global ec2
    mcInstanceIds = [] 
    mcInfo = []
    serverResizeCheck = "OK"
    statemachineresponse = {}
    
    ec2 = boto3.client('ec2') #Sets up ec2 as the object to call the boto3 (AWS Python SDK) client library for the EC2 service
    mcInfo = getInfo(mcTagKey, mcTagValue)
    
    if len(mcInfo['Instances']) < 1:
        statusmessage = "No gaming server instances found" #sets errormessage variable to error text as shown
        return(statusmessage)

    for i in mcInfo['Instances']:
        foundInstanceId = i['InstanceId']
        mcInstanceIds.append(foundInstanceId)
        

    if event['command'] == "start":
        try:
            ec2.start_instances(InstanceIds=mcInstanceIds)
            statusmessage = "Started Servers and updated DNS successfully"
        except:
            print("start failed")
            statusmessage = "Couldn't start servers, please try again later"
            return(statusmessage,mcInfo)
    elif event['command'] == "stop":
        try:
            ec2.stop_instances(InstanceIds=mcInstanceIds)
            statusmessage = "Stopped Servers"
        except:
            statusmessage = "Stopping servers failed - please wait a few minutes and try again"  
    elif event['command'] == "getInfo":
            statusmessage = "No action, just getting info"
    elif event['command'] == "reSize":
        for i in mcInfo['Instances']:
            if i['State'] != "stopped":
                statusmessage = "Your servers are not stopped. Please stop your servers and retry resizing them"
                return (statusmessage,mcInfo)
            try:
                for i in mcInstanceIds:
                    try:
                        ec2.modify_instance_attribute(
                            InstanceId=i,
                            InstanceType={'Value':  os.environ[event['reSizeType']]},
                        )
                    except:
                        serverResizeCheck = "NOK"
                if serverResizeCheck == "OK":
                    statusmessage = "Servers have been resized - please note they are currently stopped."
                else:
                    statusmessage = "There was an issue resizing one of your servers.  Make sure your target instance type is compatible (e.g. ARM bases servers such as T3g servers cannot be resized to x86 server types such as T3a servers"
            except:
                    statusmessage = "Something went wrong with resizing servers, please try again later"
    else:
        statusmessage = "Error - invalid invocation event received"
    return(statusmessage,mcInfo)

def getInfo(mcTagKey, mcTagValue):
    mcInfo = json.loads('{"Instances":[]}')
    filter =[{'Name': 'tag:'+mcTagKey, 'Values': [mcTagValue]}]
    response = ec2.describe_instances(Filters=filter)
    for reservation in response["Reservations"]: #starts for loop for all reservations returned
        for instance in reservation["Instances"]:
            if instance['State'].get('Name') != 'terminated':
                mcInfoDict = {}
                mcInfoDict['InstanceId'] = instance['InstanceId']
                mcInfoDict['InstanceType'] = instance['InstanceType']
                mcInfoDict['State'] = instance['State'].get('Name')
                mcInfoDict['PublicIpAddress'] = instance.get('PublicIpAddress','No public IP address')
                mcInfo["Instances"].append(mcInfoDict)
    return(mcInfo)
