import smtplib, ssl, email.message, pymysql.cursors
from twilio.rest import Client
from pymysql import connect
from datetime import datetime
from time import sleep

#host
host_url = 'https://magang.cynthia.yasui.pw'

#db
conn = connect(
     host = 'localhost',
     user = 'root',
     password = '',
     db = 'gx_scheduler',
     cursorclass=pymysql.cursors.DictCursor
)

#smtp
smtp_server = "mail.smtp2go.com"
port = 587
sender_email = "reminder@task-scheduler.id"
password = "cynthia24"
#wa
account_sid = 'AC56255ba393f068e2617db3be7fdb6928' 
auth_token = 'ab133b68616eb55bd3d9cf5beb16065b'

def sendEmail(to, title, msg, image = None):

  if not image:
    email_content = f"""
    <html>
    
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        
      <title> Task Scheduler </title>
      
    </head>
    
    <body>
    <p> {msg} </p>
    </body>
    </html>"""
  
  else:
    email_content = f"""
    <html>
    
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        
      <title> Task Scheduler </title>
      
    </head>
    
    <body>
    <p> {msg} </p>
    <img src="{host_url}/{image}" style="max-width: 300px">
    </body>
    </html>"""

  msg = email.message.Message()
  msg['Subject'] = f'Task Scheduler - {title}'
  msg['From'] = 'ganezo@staff.uns.ac.id'
  msg['To'] = to
  msg.add_header('Content-Type', 'text/html')
  msg.set_payload(email_content)
  
  context = ssl.create_default_context()
  try:
    server = smtplib.SMTP(smtp_server,port)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(sender_email, password)
    return server.sendmail(msg['From'], [msg['To']], msg.as_string())
  except Exception as e:
      print(e)
  finally:
      server.quit() 

def sendWA(to, title, msg, image = None):

  if to.startswith("0"):
    to = f"+62{to[1:]}"
  client = Client(account_sid, auth_token) 

  data_send = f"""*Task Scheduler - {title}*
  {msg}
  """

  if image:
    message = client.messages.create( 
                                from_='whatsapp:+14155238886',  
                                body=data_send,
                                to=f'whatsapp:{to}',
                                media_url=f'{host_url}/{image}'
    ) 
  else:
    message = client.messages.create( 
                                from_='whatsapp:+14155238886',  
                                body=data_send,
                                to=f'whatsapp:{to}'
    )

  return message.sid

while True:
  conn.ping()
  with conn.cursor() as cursor:
    cursor.execute("select a.id_task, a.judul_task, a.desc_task, a.image, a.date_end, cast(a.time_to_send as time) as time_send, b.email, b.wa from tasks a join users b on a.id_user = b.id_user where cast(a.time_to_send as date) = curdate() AND a.status = 0")
    data = cursor.fetchall()
    for task in data:
      if datetime.now().time() > (datetime.min + task['time_send']).time():
        sendEmail(task['email'], task['judul_task'], task['desc_task'], task['image'])
        sendWA(task['wa'], task['judul_task'], task['desc_task'], task['image'])
        cursor.execute("UPDATE tasks SET status = 1 WHERE id_task = %s", (task['id_task'], ))
  sleep(1)
