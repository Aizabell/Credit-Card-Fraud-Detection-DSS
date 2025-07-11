from flask import Flask, render_template, request, redirect, session, abort
import pandas as pd
import random
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Used to manage session data

# User login data with roles (username = password)
users = {
    'employee': {'password': 'employee', 'role': 'low'},
    'ceo': {'password': 'ceo', 'role': 'high'}
}

# -------------------
# Login Route
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

# -------------------
# Operator Panel - Prediction
# -------------------
@app.route('/operator', methods=['GET', 'POST'])
def operator():
    if session.get('role') != 'low':
        return abort(403)

    result = None
    if request.method == 'POST':
        # Read form data
        amount = float(request.form['amount'])
        category = request.form['category']
        gender = request.form['gender']

        # ⛔ Dummy model logic (replace later with actual model)
        prediction = random.choice([0, 1])

        # Log prediction
        input_df = pd.DataFrame([[amount, category, gender, prediction]],
                                columns=['amount', 'category', 'gender', 'prediction'])

        file_exists = os.path.exists('predictions.csv')
        input_df.to_csv('predictions.csv', mode='a', header=not file_exists, index=False)

        result = "Fraud" if prediction == 1 else "Not Fraud"

    return render_template('operator.html', result=result)

# -------------------
# Manager Panel - Dashboard
# -------------------
@app.route('/manager')
def manager():
    if session.get('role') != 'high':
        return abort(403)

    if not os.path.exists('predictions.csv') or os.stat('predictions.csv').st_size == 0:
        # Show dashboard with a placeholder message
        return render_template(
            'manager.html',
            # data="<p class='text-center text-muted'>No prediction data available yet.</p>"
        )

    df = pd.read_csv('predictions.csv')
    return render_template('manager.html', data=df.to_html(classes="table table-bordered", index=False))

# -------------------
# Logout
# -------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------
# App Runner
# -------------------
if __name__ == "__main__":
    app.run(debug=True)
