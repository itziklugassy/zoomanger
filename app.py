from flask import Flask, render_template, request, redirect, url_for, flash, g, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from contextlib import contextmanager
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zoo.db'
app.config['UPLOAD_FOLDER'] = '/Users/itziklugassy/Documents/zoo_manger/images'  # Set to your images directory
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Create a function to set up the application context before each request
@contextmanager
def app_context():
    with app.app_context():
        yield

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(100), nullable=True)  # Field for image filename

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        with app_context():
            animals = Animal.query.all()
        return render_template('index.html', animals=animals)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Please check your credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/add_animal', methods=['GET', 'POST'])
@login_required
def add_animal():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')

        # Check if the post request has the file part
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['photo']
        
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Create a new animal instance with image
            animal = Animal(name=name, age=age, image_filename=filename)
            
            with app_context():
                db.session.add(animal)
                db.session.commit()
            
            flash('Animal added successfully', 'success')
            return redirect(url_for('index'))
    
    return render_template('add_animal.html')

@app.route('/update_animal/<int:id>', methods=['GET', 'POST'])
@login_required
def update_animal(id):
    animal = Animal.query.get_or_404(id)
    if request.method == 'POST':
        try:
            animal.name = request.form['name']
            animal.age = request.form['age']
            db.session.commit()
            flash('Animal updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating animal: {}'.format(e), 'danger')
            print(e)  # For debugging, prints to console.
        return redirect(url_for('index'))
    return render_template('update_animal.html', animal=animal)

@app.route('/delete_animal/<int:id>')
@login_required
def delete_animal(id):
    with app_context():
        animal = Animal.query.get(id)
        if animal:
            db.session.delete(animal)
            db.session.commit()
            flash('Animal deleted successfully', 'success')
        else:
            flash('Animal not found', 'danger')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if the username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            # Create a new user and add it to the database
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Route for serving images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app_context():
        db.create_all()
    app.run(port=30924, debug=True)
