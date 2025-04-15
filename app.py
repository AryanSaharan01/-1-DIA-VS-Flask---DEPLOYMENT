from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
from mysql.connector import Error
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session

# SMTP_SERVER = "smtp.gmail.com" 
# SMTP_PORT = 587
# SENDER_EMAIL = "hackathon01program01@gmail.com"
# SENDER_PASSWORD = "dkwj kcgq gspj dkyp"  
# COMPANY_NAME = "DIA Club"  
# SUPPORT_EMAIL = "support@yourcompany.com"  

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
COMPANY_NAME = os.getenv("COMPANY_NAME", "DIA Club")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@example.com")


def generate_otp():
    return str(random.randint(100000, 999999))

def send_email(receiver_email, otp):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Verification OTP"
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email

    html = f"""

    <html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333; max-width: 600px; margin: 0 auto;">
    <div style="padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
        <div style="text-align: center; margin-bottom: 25px;">
            <h2 style="color: #2c3e50; margin: 0;">{COMPANY_NAME}</h2>
            <p style="color: #7f8c8d; margin: 5px 0;">Secure Account Verification</p>
        </div>

        <p>Dear User,</p>

        <p>We received a request to verify your account associated with <strong>{receiver_email}</strong>. 
        Please use the following One-Time Password (OTP) to complete your verification:</p>

        <div style="background: #f8f9fa; padding: 15px; margin: 20px 0; 
                text-align: center; font-size: 24px; letter-spacing: 3px;
                border-radius: 5px; font-weight: bold; color: #1a73e8;">
            {otp}
        </div>

        <p>This OTP is valid for <strong>10 minutes</strong> and can only be used once.</p>

        <div style="background: #fff9e6; padding: 15px; border-left: 4px solid #ffd700; margin: 20px 0;">
            <strong>Security Tips:</strong>
            <ul style="margin: 10px 0 0 20px;">
                <li>Never share this OTP with anyone</li>
                <li>Our team will never ask for your OTP</li>
                <li>Delete this email after verification</li>
            </ul>
        </div>

        <p>If you didn't request this verification, please contact our support team immediately 
        at <a href="mailto:{SUPPORT_EMAIL}" style="color: #1a73e8; text-decoration: none;">
        {SUPPORT_EMAIL}</a>.</p>

        <p>Best regards,<br>
        The {COMPANY_NAME} Team</p>

        <div style="border-top: 1px solid #e0e0e0; margin-top: 30px; padding-top: 15px;
                text-align: center; color: #7f8c8d; font-size: 12px;">
            <p>This is an automated message - please do not reply directly to this email</p>
            <p>&copy; 2024 {COMPANY_NAME}. All rights reserved</p>
        </div>
    </div>
</body>
</html>
    """

    part = MIMEText(html, "html")
    message.attach(part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, message.as_string())


def get_db_connection():
    try:
        db = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DB", "dia_vs")
        )
        return db
    except Error as e:
        print("DB Connection Error:", str(e))
        return None

    
@app.route('/test_db')
def test_db():
    db = get_db_connection()
    if db:
        db.close()
        return "DB connection successful"
    return "DB connection failed"

@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    if not db:
        return render_template('index.html', error="Database connection failed")
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM all_users WHERE roll_no = %s", (session['user']['roll_no'],))
        user_details = cursor.fetchone()
        cursor.close()
        if user_details:
            return render_template('index.html', user=user_details)
        else:
            return render_template('index.html', error="User details not found")
    except Error as e:
        return render_template('index.html', error="Database error occurred")
    finally:
        db.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('txt', '').strip()
        email = request.form.get('email', '').strip()

        if not username or not email:
            return render_template('login.html', alert_message="Please fill in all fields.", show_otp=False)

        db = get_db_connection()
        if not db:
            return render_template('login.html', alert_message="Database connection failed. Please try again later.", show_otp=False)
            
        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM web_users WHERE username = %s AND email = %s", (username, email))
            user = cursor.fetchone()
            cursor.close()

            if user:
                otp = generate_otp()
                session['otp'] = otp
                session['login_email'] = email
                session['login_username'] = username
                
                try:
                    send_email(email, otp)
                    return render_template('login.html', 
                                         alert_message="OTP sent to your email. Please check and enter below.",
                                         show_otp=True,
                                         is_login=True)
                except Exception as e:
                    return render_template('login.html', 
                                         alert_message=f"Failed to send OTP: {str(e)}",
                                         show_otp=False)
            else:
                return render_template('login.html', 
                                    alert_message="User not found. Please register first.",
                                    show_otp=False)
        except Error as e:
            return render_template('login.html', 
                                alert_message="An error occurred during login. Please try again.",
                                show_otp=False)
        finally:
            if db:
                db.close()

    return render_template('login.html', show_otp=False)

@app.route('/verify-login', methods=['POST'])
def verify_login():
    if 'otp' not in session or 'login_email' not in session:
        return redirect(url_for('login'))

    user_otp = request.form.get('otp', '').strip()
    if user_otp == session['otp']:
        db = get_db_connection()
        if not db:
            return render_template('login.html', alert_message="DB connection failed.", show_otp=False)

        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM web_users WHERE username = %s AND email = %s",
                           (session['login_username'], session['login_email']))
            user = cursor.fetchone()
            cursor.close()

            if user:
                session['user'] = {
                    'username': user['username'],
                    'email': user['email'],
                    'roll_no': user['roll_no']
                }
                session.pop('otp', None)
                session.pop('login_email', None)
                session.pop('login_username', None)
                return redirect(url_for('index'))
            else:
                return render_template('login.html', alert_message="User data not found.", show_otp=False)
        except Error as e:
            return render_template('login.html', alert_message="Login verification error.", show_otp=False)
        finally:
            db.close()

    return render_template('login.html', alert_message="Invalid OTP. Try again.", show_otp=True, is_login=True)


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('txt', '').strip()
    roll_no = request.form.get('roll', '').strip()
    email = request.form.get('email', '').strip()
    mobile_no = request.form.get('phno', '').strip()

    if not all([username, roll_no, email, mobile_no]):
        return render_template('login.html', 
                             alert_message="Please fill in all fields.",
                             show_otp=False)

    db = get_db_connection()
    if not db:
        return render_template('login.html', 
                            alert_message="Database connection failed. Please try again later.",
                            show_otp=False)
        
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM all_users WHERE roll_no = %s AND username = %s", (roll_no, username))
        user = cursor.fetchone()

        if user:
            cursor.execute("SELECT * FROM web_users WHERE roll_no = %s", (roll_no,))
            existing_user = cursor.fetchone()

            if existing_user:
                return render_template('login.html', 
                                     alert_message="You are already registered. Please login.",
                                     show_otp=False)
            
            otp = generate_otp()
            session['otp'] = otp
            session['reg_data'] = {
                'username': username,
                'roll_no': roll_no,
                'email': email,
                'mobile_no': mobile_no
            }
            
            try:
                send_email(email, otp)
                return render_template('login.html', 
                                     alert_message="OTP sent to your email. Please check and enter below to complete registration.",
                                     show_otp=True,
                                     is_login=False)
            except Exception as e:
                return render_template('login.html', 
                                    alert_message=f"Failed to send OTP: {str(e)}",
                                    show_otp=False)
        else:
            return render_template('login.html', 
                                alert_message="YOU ARE NOT A MEMBER OF DIA CLUB",
                                show_otp=False)
    except Error as e:
        db.rollback()
        return render_template('login.html', 
                            alert_message="An error occurred during registration. Please try again.",
                            show_otp=False)
    finally:
        cursor.close()
        db.close()

@app.route('/verify-register', methods=['POST'])
def verify_register():
    if 'otp' not in session or 'reg_data' not in session:
        return redirect(url_for('login'))
    
    user_otp = request.form.get('otp', '').strip()
    if user_otp == session['otp']:
        reg_data = session['reg_data']
        session.pop('otp', None)
        session.pop('reg_data', None)
        
        db = get_db_connection()
        if not db:
            return render_template('login.html', 
                                alert_message="Database connection failed. Please try again.",
                                show_otp=False)
            
        try:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO web_users (roll_no, username, email, mobile_no) VALUES (%s, %s, %s, %s)",
                (reg_data['roll_no'], reg_data['username'], reg_data['email'], reg_data['mobile_no'])
            )
            db.commit()
            return render_template('login.html', 
                                 alert_message="Registration successful! Please login.",
                                 show_otp=False)
        except Error as e:
            db.rollback()
            return render_template('login.html', 
                                alert_message=f"Error completing registration: {str(e)}",
                                show_otp=False)
        finally:
            cursor.close()
            db.close()
    
    return render_template('login.html', 
                         alert_message="Invalid OTP. Please try again.",
                         show_otp=True,
                         is_login=False)

@app.route('/submit-manifesto', methods=['GET', 'POST'])
def submit_manifesto():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        brief = request.form.get('description', '').strip()
        manifesto = request.form.get('manifesto', '').strip()

        # Validate form data
        if not all([name, roll_no, brief, manifesto]):
            return render_template('approval_form.html', 
                                 error="Please fill all fields",
                                 form_data=request.form)

        db = get_db_connection()
        if not db:
            return render_template('approval_form.html', 
                                 error="Database connection failed",
                                 form_data=request.form)

        try:
            cursor = db.cursor(dictionary=True)
            
            # Debug: Print the data being inserted
            print(f"Inserting data: {name}, {roll_no}, {brief}, {manifesto}")
            
            # Insert new submission
            cursor.execute(
                "INSERT INTO candid_details (roll_no, name, brief, manifesto) VALUES (%s, %s, %s, %s)",
                (roll_no, name, brief, manifesto)
            )
            db.commit()
            
            # Verify insertion
            cursor.execute("SELECT * FROM candid_details WHERE roll_no = %s", (roll_no,))
            inserted = cursor.fetchone()
            print(f"Inserted record: {inserted}")
            
            return render_template('approval_form.html', 
                                 success="Manifesto submitted successfully!")
        except Error as e:
            db.rollback()
            print(f"Database error: {e}")
            return render_template('approval_form.html', 
                                 error=f"Error submitting manifesto: {e}",
                                 form_data=request.form)
        finally:
            cursor.close()
            db.close()

    return render_template('approval_form.html')

@app.route('/approval')
def approval():
    db = get_db_connection()
    if not db:
        return render_template('approval.html', error="Database connection failed")
    
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM candid_details WHERE status = 'pending' OR status = 'rejected'")
        candidates = cursor.fetchall()
        return render_template('approval.html', candidates=candidates)
    except Error as e:
        return render_template('approval.html', error="Error fetching candidates")
    finally:
        cursor.close()
        db.close()


@app.route('/update_status/<int:candidate_id>/<status>')
def update_status(candidate_id, status):
    if 'user' not in session:  # Add admin check if needed
        return redirect('/login')
    
    if status not in ['approved', 'rejected']:
        return "Invalid status", 400
        
    db = get_db_connection()
    if not db:
        return "Database error", 500
        
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE candid_details SET status = %s WHERE id = %s",
            (status, candidate_id)
        )
        db.commit()
        return redirect('/approval')
    except Error as e:
        db.rollback()
        return "Error updating status", 500
    finally:
        cursor.close()
        db.close()

@app.route('/candidates')
def candidates():
    db = get_db_connection()
    if not db:
        return render_template('candidates.html', error="Database connection failed")
    
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM candid_details WHERE status = 'approved'")
        candidates = cursor.fetchall()
        return render_template('candidates.html', candidates=candidates)
    except Error as e:
        return render_template('candidates.html', error="Error fetching candidates")
    finally:
        cursor.close()
        db.close()

@app.route('/vote/<int:candidate_id>')
def vote(candidate_id):
    if 'user' not in session:
        return redirect('/login')
    
    db = get_db_connection()
    if not db:
        flash("Database connection error", "danger")
        return redirect('/')

    try:
        cursor = db.cursor()
        db.start_transaction()  # Start transaction

        # Check if user already voted
        cursor.execute("SELECT 1 FROM votes WHERE roll_no = %s", (session['user']['roll_no'],))
        if cursor.fetchone():
            flash("You have already voted!", "warning")
            return redirect('/candidates')

        # Verify candidate exists and is approved
        cursor.execute("SELECT 1 FROM candid_details WHERE id = %s AND status = 'approved'", (candidate_id,))
        if not cursor.fetchone():
            flash("Invalid candidate selected", "danger")
            return redirect('/candidates')

        # Record vote
        cursor.execute(
            "INSERT INTO votes (candidate_id, roll_no) VALUES (%s, %s)",
            (candidate_id, session['user']['roll_no'])
        )

        # Update candidate vote count
        cursor.execute(
            "UPDATE candid_details SET vote_count = vote_count + 1 WHERE id = %s",
            (candidate_id,)
        )

        db.commit()  # Commit transaction
        flash("Vote submitted successfully!", "success")
        return redirect('/candidates')

    except Error as e:
        db.rollback()
        flash(f"Error submitting vote: {str(e)}", "danger")
        return redirect('/candidates')
    finally:
        cursor.close()
        db.close()
    if 'user' not in session:
        return redirect('/login')
    
    db = get_db_connection()
    if not db:
        flash("Database connection error", "danger")
        return redirect('/')

    try:
        cursor = db.cursor()

        # Check if this user already voted at all
        cursor.execute("SELECT * FROM votes WHERE roll_no = %s", (session['user']['roll_no'],))
        if cursor.fetchone():
            flash("You can only vote once and you did that already.", "warning")
            return redirect('/')

        # Record the vote
        cursor.execute("INSERT INTO votes (candidate_id, roll_no) VALUES (%s, %s)",
                       (candidate_id, session['user']['roll_no']))

        # Update vote count
        cursor.execute("UPDATE candid_details SET vote_count = vote_count + 1 WHERE id = %s", (candidate_id,))
        db.commit()

        flash("Vote submitted successfully!", "success")
        return redirect('/')
    except Error as e:
        db.rollback()
        flash("Error submitting vote. Try again.", "danger")
        return redirect('/')
    finally:
        cursor.close()
        db.close()


# @app.route('/vote/<int:candidate_id>')
# def vote(candidate_id):
#     if 'user' not in session:
#         return redirect('/login')
    
#     db = get_db_connection()
#     if not db:
#         return "Database error", 500
        
#     try:
#         cursor = db.cursor()
        
#         # Check if user already voted
#         cursor.execute(
#             "SELECT * FROM votes WHERE candidate_id = %s AND roll_no = %s",
#             (candidate_id, session['user']['roll_no'])
#         )
#         if cursor.fetchone():
#             return "You have already voted", 400
            
#         # Record vote
#         cursor.execute(
#             "INSERT INTO votes (candidate_id, roll_no) VALUES (%s, %s)",
#             (candidate_id, session['user']['roll_no'])
#         )
        
#         # Update vote count
#         cursor.execute(
#             "UPDATE candid_details SET vote_count = vote_count + 1 WHERE id = %s",
#             (candidate_id,)
#         )
        
#         db.commit()
#         return redirect('/candidates')
#     except Error as e:
#         db.rollback()
#         return f"Error recording vote: {e}", 500
#     finally:
#         cursor.close()
#         db.close()

@app.route('/results')
def results():
    db = get_db_connection()
    if not db:
        return render_template('result.html', error="Database connection failed")
    
    try:
        cursor = db.cursor(dictionary=True)
        
        # Get total votes cast (direct count from votes table)
        cursor.execute("SELECT COUNT(*) as total_votes FROM votes")
        total_votes_result = cursor.fetchone()
        total_votes = total_votes_result['total_votes'] if total_votes_result else 0
        
        # Get all candidates with their vote counts (counted from votes table for accuracy)
        cursor.execute("""
            SELECT 
                cd.id, 
                cd.name, 
                cd.brief, 
                COUNT(v.id) as vote_count,
                CASE 
                    WHEN %s > 0 THEN ROUND((COUNT(v.id) * 100.0 / %s), 1)
                    ELSE 0
                END as percentage
            FROM candid_details cd
            LEFT JOIN votes v ON cd.id = v.candidate_id
            WHERE cd.status = 'approved'
            GROUP BY cd.id, cd.name, cd.brief
            ORDER BY vote_count DESC
        """, (total_votes, total_votes))
        
        candidates = cursor.fetchall()
        
        # Verify the sum of candidate votes matches total votes
        sum_candidate_votes = sum(candidate['vote_count'] for candidate in candidates)
        if sum_candidate_votes != total_votes:
            # If mismatch, log the issue (you might want to handle this differently)
            print(f"Warning: Vote count mismatch! Total votes: {total_votes}, Sum of candidate votes: {sum_candidate_votes}")
        
        return render_template('result.html', 
                            candidates=candidates,
                            total_votes=total_votes,
                            total_candidates=len(candidates))
    except Error as e:
        return render_template('result.html', error=f"Error fetching results: {str(e)}")
    finally:
        cursor.close()
        db.close()
    db = get_db_connection()
    if not db:
        return render_template('result.html', error="Database connection failed")
    
    try:
        cursor = db.cursor(dictionary=True)
        
        # Get total votes cast
        cursor.execute("SELECT COUNT(*) as total_votes FROM votes")
        total_votes = cursor.fetchone()['total_votes']
        
        # Get all candidates with vote counts
        cursor.execute("""
            SELECT cd.id, cd.name, cd.brief, cd.vote_count 
            FROM candid_details cd
            WHERE cd.status = 'approved'
            ORDER BY cd.vote_count DESC
        """)
        candidates = cursor.fetchall()
        
        return render_template('result.html', 
                            candidates=candidates,
                            total_votes=total_votes,
                            total_candidates=len(candidates))
    except Error as e:
        return render_template('result.html', error="Error fetching results")
    finally:
        cursor.close()
        db.close()
        
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port= 5002)