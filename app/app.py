from flask import Flask, render_template, request, redirect, session, abort
import pandas as pd
import os
from joblib import load

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# -------------------
# In-memory prediction history
# -------------------
history_records = []

# -------------------
# User Credentials
# -------------------
users = {
    'employee': {'password': 'employee', 'role': 'low'},
    'ceo': {'password': 'ceo', 'role': 'high'}
}

# -------------------
# Dropdown Data
# -------------------
merchant_list = [
    'fraud_Kilback LLC', 'fraud_Cormier LLC', 'fraud_Schumm PLC', 'fraud_Kuhn LLC', 'fraud_Boyer PLC',
    'fraud_Dickinson Ltd', 'fraud_Cummerata-Jones', 'fraud_Kutch LLC', 'fraud_Olson, Becker and Koch',
    'fraud_Stroman, Hudson and Erdman', 'fraud_Rodriguez Group', 'fraud_Erdman-Kertzmann',
    'fraud_Jenkins, Hauck and Friesen', 'fraud_Kling Inc', 'fraud_Connelly, Reichert and Fritsch',
    'fraud_Friesen-Stamm', 'fraud_Prohaska-Murray', 'fraud_Huels-Hahn', 'fraud_Berge LLC',
    'fraud_Bartoletti-Wunsch', 'fraud_Christiansen, Goyette and Schamberger', 'fraud_Corwin-Collins',
    'fraud_Eichmann, Bogan and Rodriguez', 'fraud_Greenholt, Jacobi and Gleason', 'fraud_Bins-Rice',
    'fraud_Brekke and Sons', 'fraud_Schmitt Inc', 'fraud_Mraz-Herzog',
    'fraud_Tillman, Dickinson and Labadie', 'fraud_Kuvalis Ltd'
]

category_label_map = {
    "Miscellaneous (Online)": "misc_net",
    "Grocery (POS)": "grocery_pos",
    "Entertainment": "entertainment",
    "Gas & Transport": "gas_transport",
    "Miscellaneous (POS)": "misc_pos",
    "Grocery (Online)": "grocery_net",
    "Shopping (Online)": "shopping_net",
    "Shopping (POS)": "shopping_pos",
    "Food & Dining": "food_dining",
    "Personal Care": "personal_care",
    "Health & Fitness": "health_fitness",
    "Travel": "travel",
    "Kids & Pets": "kids_pets",
    "Home": "home"
}

# -------------------
# Time Group Function
# -------------------
def get_time_group_from_time(timestr):
    hour = int(timestr.split(":")[0])
    if 0 <= hour < 5:
        return 'Midnight'
    elif 5 <= hour < 8:
        return 'Early Morning'
    elif 8 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 14:
        return 'Noon'
    elif 14 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 20:
        return 'Evening'
    else:
        return 'Night'

# -------------------
# Routes
# -------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            return redirect('/operator' if user['role'] == 'low' else '/manager')
        else:
            return "Invalid credentials"
    return render_template('login.html')


@app.route('/operator', methods=['GET', 'POST'])
def operator():
    if session.get('role') != 'low':
        return abort(403)

    result = None
    probability = None

    if request.method == 'POST':
        model = load('../model_saved/xgb_model.joblib')
        scaler = load('../model_saved/scaler.joblib')
        encoders = load('../model_saved/encoders.joblib')

        # Inputs
        amount = float(request.form['amount'])
        category_label = request.form['category']
        category = category_label_map.get(category_label, "")
        distance = float(request.form['distance'])
        age = int(request.form['age'])
        transaction_time = request.form['transaction_time']
        merchant = request.form['merchant']

        time_group = get_time_group_from_time(transaction_time)

        input_df = pd.DataFrame([{
            'merchant': merchant,
            'amt': amount,
            'distance_km': distance,
            'category': category,
            'age': age,
            'time_group': time_group
        }])

        for col in ['merchant', 'category', 'time_group']:
            input_df[col] = encoders[col].transform(input_df[col])

        X_scaled = scaler.transform(input_df)
        proba = model.predict_proba(X_scaled)[0][1]
        prediction = int(proba >= 0.625)

        result = "Fraud" if prediction == 1 else "Not Fraud"
        probability = round(proba * 100, 2)

        history_records.append({
            'Merchant': merchant,
            'Amount': amount,
            'Distance': distance,
            'Category': category_label,
            'Age': age,
            'Time Group': time_group,
            'Result': result,
            'Confidence': probability,
            'Operator': session.get('username'),
            'terminated': False
        })

    return render_template(
        'operator.html',
        result=result,
        confidence=probability,
        history=history_records,
        merchants=merchant_list,
        categories=category_label_map
    )


@app.route('/mark_terminated/<int:row_index>')
def mark_terminated(row_index):
    if 0 <= row_index < len(history_records):
        history_records[row_index]['terminated'] = True
        return '', 204
    return 'Invalid Index', 400


@app.route('/manager')
def manager():
    if session.get('role') != 'high':
        return abort(403)
    return render_template('manager.html', data="<p class='text-center text-muted'>Tableau Dashboard Embedded Here</p>")


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
