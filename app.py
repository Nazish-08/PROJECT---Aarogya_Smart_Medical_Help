from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pickle
import pandas as pd
import os

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = "your_secret_key"
db = SQLAlchemy(app)

# Database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# Load ML model
model = None
features = []
model_path = os.path.join("ml_model", "disease_predictor.pkl")
if os.path.exists(model_path):
    with open(model_path, "rb") as f:
        data = pickle.load(f)
        if isinstance(data, dict) and "model" in data:
            model = data["model"]
            features = data["features"]

# Load medicine data
medicine_df = None
csv_path = os.path.join("data", "medicine_info.csv")
if os.path.exists(csv_path):
    medicine_df = pd.read_csv(csv_path)
    medicine_df['disease'] = medicine_df['disease'].str.strip().str.lower()

# Load doctor data
doctor_df = None
doctor_csv_path = os.path.join("data", "doctors_list.csv")
if os.path.exists(doctor_csv_path):
    doctor_df = pd.read_csv(doctor_csv_path)
    doctor_df['specialization'] = doctor_df['specialization'].str.strip().str.lower()

@app.route('/')
def home():
    username = session.get('user_name')
    return render_template('index.html', username=username)

@app.route('/about')
def about():
    username = session.get('user_name')
    return render_template('about.html', username=username)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    username = session.get('user_name')
    if request.method == 'POST':
        return redirect(url_for('home'))
    return render_template('contact.html', username=username)

@app.route('/predict', methods=['POST'])
def predict():
    username = session.get('user_name')
    selected_symptoms = [s.strip().lower() for s in request.form.getlist('symptoms')]
    symptom_display = ", ".join(selected_symptoms)

    predicted_disease = ""
    if model and features:
        input_data = [1 if f in selected_symptoms else 0 for f in features]
        if sum(input_data) == 0:
            predicted_disease = "Unknown"
        else:
            predicted_disease = model.predict([input_data])[0]

    predicted_disease_clean = predicted_disease.strip().lower()

    # Fetch medicines
    medicines = []
    if medicine_df is not None and predicted_disease_clean:
        med_rows = medicine_df[medicine_df['disease'].str.lower() == predicted_disease_clean]
        if not med_rows.empty:
            for _, row in med_rows.iterrows():
                medicines.append({
                    "name": row['medicine'],
                    "dosage": row['dosage'],
                    "side_effects": row['side_effects']
                })
        else:
            medicines = [{
                "name": "No medicines found for this disease",
                "dosage": "-",
                "side_effects": "-"
            }]
    else:
        medicines = [{
            "name": "No medicines found for this disease",
            "dosage": "-",
            "side_effects": "-"
        }]

    # Doctors
    doctors = []
    if doctor_df is not None:
        for _, row in doctor_df.iterrows():
            doctors.append({
                "name": row['doctor_name'],
                "specialization": row.get('specialization', 'N/A'),
                "location": row.get('location', row.get('address', 'N/A')),
                "contact": row.get('contact', row.get('phone', 'N/A'))
            })

    return render_template(
        'result.html',
        username=username,
        symptom=symptom_display if symptom_display else "No symptoms provided",
        disease=predicted_disease.capitalize() if predicted_disease else "Not Detected",
        medicines=medicines,
        doctors=doctors
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_name'] = email.split('@')[0].capitalize()
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
