# vpcbuild

Build VPC in Amazon.  The aim is to build a simple VPC that can be used to host Django websites.  Also maintain it and 
build derivates eg for testing purposes.  This should allow a whole infrastructure to be build and then destroyed
just for testing.

The focus is on lowest cost infrastructure to support a low volume production website.  The production element means
that I want to use RDS Postgres to store the data.

I am also using fabric so that I can remember all the commands I need.

# Sources

[Chris Allen] Blog PacketLlost - I have tried to follow this to see what happens   
[Troposphere] : A library to allow building of AWS templates in Python.  This makes it easy to generate dynamic sites 
depending on your Python code.   


[Troposphere]: https://github.com/cloudtools/troposphere   
[Chris Allen]: https://packetlost.com/blog/2017/09/04/dynamic-cloudformation-templates-troposphere-and-boto3/    

