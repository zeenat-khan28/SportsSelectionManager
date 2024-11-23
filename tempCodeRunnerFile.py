import pandas as pd
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydrive.auth import GoogleAuth 
from pydrive.drive import GoogleDrive 
from sqlalchemy import create_engine, text

#---------------------------------GOOGLE AUTHENTICATION---------------------------------

print("Your browser will open now so please select your google account and click on continue to complete the authentication.\n")

# Initializing a GoogleAuth Object 
gauth = GoogleAuth() 

# client_secrets.json file is verified and it automatically handles authentication 
gauth.LocalWebserverAuth() 

# GoogleDrive Instance is created using authenticated GoogleAuth instance 
drive = GoogleDrive(gauth) 

# Initialize GoogleDriveFile instance with file id 
file_obj = drive.CreateFile({'id': '1-je2pJlmZlX7nXrNGezR2YyRk-4PL52FATKiRAh0_QI'})   #File ID of the Response xls File ( The thing after /d/ in your xls response sheet )
file_obj.GetContentFile('REGISTRATION(F) (Responses).xls',                                  #Name of xls file
		mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') 

df = pd.read_excel('REGISTRATION(F) (Responses).xls') 

#---------------------------------------------------------------------------------------



#------------------------------MYSQL AUTHENTICATION & FETCH-----------------------------

# MySQL database configuration
db_username = 'root'						#input("Enter your username (Usually 'root'): ")
db_password = 'mysqlyug' 					#input("Enter your MySQL Password: ")
db_host = 'localhost'
db_name = 'sports'

# Create a SQLAlchemy engine
engine = create_engine(f'mysql+mysqlconnector://{db_username}:{db_password}@{db_host}/{db_name}')

table_name = 'SRTable'
df.to_sql(table_name, con=engine, if_exists='replace', index=True, index_label = "S. No.")

# Define the MySQL SELECT statement as a string

connection = engine.connect()
sport_stmt = text("SELECT `Game previously participated` from SRTable")
sports = connection.execute(sport_stmt)
sports_group = list(set([i[0] for i in sports.fetchall()]))

#---------------------------------------------------------------------------------------


#---------------------------------------SMTP--------------------------------------------

# Email server settings
email_address = "yugtatiya@gmail.com"
email_password = "ntdu edbg ikre yces"              #An app password is generated for security purposes
smtp_server = "smtp.gmail.com"
smtp_port = 587 

# Email content
subject = ""
message = ""

#Creates a function that sends email
def send_email(to_email, bcc_emails, subject, message):
    # Create message
    msg = MIMEMultipart()
    msg['From'] = email_address
    msg['To'] = ", ".join(to_email)
    msg['Bcc'] = ", ".join(bcc_emails)
    msg['Subject'] = subject

    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    # Connect to the SMTP server with TLS
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(email_address, email_password)

        # Send the email
        server.sendmail(email_address, to_email + bcc_emails, msg.as_string())

#Sends the emails only to the selected sports group
def send_emails(sports,sub,mesg):
    selected_sports_group = sports
    # Fetch emails from MySQL based on the selected sports group
    mysql_stmt = text(f"SELECT `email address` FROM SRTable WHERE `Game previously participated` = '{selected_sports_group}'")
    result = connection.execute(mysql_stmt)
    bcc_emails = [row[0] for row in result]

    # Send emails to each recipient
    send_email(["cayugjain@gmail.com"], bcc_emails, sub, mesg)

#---------------------------------------------------------------------------------------

