## Pure Storage Open Connect for Amazon Web Services (AWS) ##

Version 1.0 of the Open Connect for AWS is implemented through a series of functions to help simplify the deployment of AWS Direct Connect with the Pure Storage FlashArray

Functions:
1. xml() - Used for reading the .xml configuration file and getting the values.
2. vpc() - Used for creating the vpc in aws
3. securitygroup() - Used for creation security groups for vpc
4. launch_instance() - This is used for creating all the other dependencies for the direct connect connection and launching the ec2 instance. Some user inputs are needed for using this function.
5. initiator_iscsi() - Used for configuring the iscsi connection in the ec2 instance and formatting the disk
6. Diskspd() - used for running the tests

There is a Windows PowerShell script which will be used for connecting to the Pure Storage FlashArray, creating host, volumes and assigning the volumes to the host(s).
