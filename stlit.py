# import subprocess
# import os

# subprocess.check_call(["pip", "install", "-r", os.path.join(os.path.abspath("."), "requirements.txt")])

import streamlit as st
import pandas as pd
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydrive.auth import GoogleAuth 
from pydrive.drive import GoogleDrive 
from sqlalchemy import create_engine, text
import webbrowser
import json
from flask import Flask, redirect, url_for, session
from google.oauth2 import id_token
from google.auth.transport.requests import Request
import google.auth.exceptions




def get_session_store():
    if not session.get('store'):
        session['store'] = {}
    return session['store']


if 'email' not in st.session_state:
    st.write('Please log in to access the app.')
    if st.button('Log In'):
        webbrowser.open('http://localhost:5000/login')  # Replace with your Flask app URL
else:
    # Authenticate using the user's access token stored in the Flask app's session
    gauth = GoogleAuth()
    session_store = get_session_store()
    session_store.save()
    gauth.LoadCredentialsFile(session_store.path)
    drive = GoogleDrive(gauth)

    # Use the `drive` object to upload or download files, create or delete folders, etc.
    st.write(f'Welcome, {st.session_state["email"]}!')


with open('client_secrets.json') as f:
    client_secrets = json.load(f)

# Define the client secret as a string
CLIENT_SECRET = client_secrets['installed']['client_secret']

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/login')
def login():
    # Get the URL for the Google login page
    google_auth_url = id_token.generate_login_url(
        'https://rvcesports.streamlit.app//google_callback',  # Replace with your Streamlit app URL
        access_type='offline',
        prompt='consent',
        scope=['openid', 'email', 'profile', 'https://www.googleapis.com/auth/drive']
    )
    return redirect(google_auth_url)

@app.route('/google_callback')
def google_callback():
    # Verify the user's credentials
    try:
        idinfo = id_token.verify_oauth2_token(
            Flask.request.args['idtoken'],
            Request(),
            CLIENT_SECRET
        )
    except google.auth.exceptions.InvalidTokenError:
        return 'Invalid token', 401

    # Save the user's email address and access token in the session
    session['email'] = idinfo['email']
    session['access_token'] = idinfo['at_hash']

    # Redirect the user back to your Streamlit app
    return redirect('https://rvcesports.streamlit.app/')  # Replace with your Streamlit app URL

if __name__ == '__main__':
    app.run(port=5000)

#---------------------------------GOOGLE AUTHENTICATION---------------------------------

# print("Your browser will open now so please select your google account and click on continue to complete the authentication.\n")

# # Initializing a GoogleAuth Object 
# gauth = GoogleAuth() 

# # client_secrets.json file is verified and it automatically handles authentication 
# gauth.LocalWebserverAuth() 

# # GoogleDrive Instance is created using authenticated GoogleAuth instance 
# drive = GoogleDrive(gauth) 

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


#__________________________________________________________



try:
    # Creating a session state
    st.image("RVLogo.jpeg", width=150)
    st.title("SPORTS SELECTION MANAGER")
    if 'selected_sport' not in st.session_state:
        st.session_state.selected_sport = None

    # Dropdown Menu for sports selection
    st.session_state.selected_sport = st.selectbox("Enter sports", sports_group, index=0)

    #A frame for the mail
    frame = st.container(border=True)
    frame.write("Mail Box")

    subject_input = frame.text_input("Enter a subject:", max_chars=100, key="subject_input", placeholder="Subject...")
    message_input = frame.text_area("Enter a message:", height=200, key="message_input", placeholder="Type your message here...")
    uploaded_file = frame.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()            #Converting pdf into byte form

    sport = st.session_state['selected_sport']      #Getting sport value

    # Send emails when the button is clicked
    if st.button("Send Emails"):
        send_emails(sport,subject_input, message_input, pdf = file_bytes)
        st.write(f"Emails to {sport} sent successfully!")
    

    #Searching with USN
    usn_input = st.text_input('Enter Branch')

    if usn_input:
        filtered_df = df[df['Branch'] == usn_input]
        
        # If a row with that name exists, display it
        if not filtered_df.empty:
            st.write('Row with USN', usn_input, ':', filtered_df)
        else:
            st.write('No row found with USN', usn_input)
    
    column_names = st.multiselect('Select columns:', df.columns, default=['USN','Name of the Student','Email address', 'Game previously participated'])
    st.dataframe(df[column_names])


except Exception as e:
    st.error(f"An error occurred: {e}")
