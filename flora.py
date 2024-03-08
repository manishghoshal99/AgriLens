from flask import Flask, render_template, request, redirect, url_for, session
from keras.models import load_model
import numpy as np
from exif import Image as im
from geopy.geocoders import Nominatim #geolocation services
import cv2
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re



app = Flask(__name__)


app.config['MYSQL_HOST'] = '35.200.223.139'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'LensFleur'
app.config['MYSQL_DB'] = 'lensfleur'
app.config['SECRET_KEY'] = 'lensfleur'
mysql = MySQLdb.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    passwd=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB']
)

classes=['Apple scab', 'Apple Black rot', 'Cedar apple rust', 
         'Apple healthy', 'Blueberry healthy', 
         'Cherry Powdery mildew', 'Cherry healthy', 
         'Corn Cercospora leaf spot', 'Corn Common rust', 
         'Corn Northern Leaf Blight', 'Corn healthy', 
         'Grape Black rot', 'Grape Black Measles', 
         'Grape Leaf blight', 'Grape healthy', 
         'Orange Haunglongbing', 'Peach Bacterial spot', 
         'Peach healthy', 'Bell Peppers Bacterial spot', 'Bell Peppers healthy', 
         'Potato Early blight', 'Potato Late blight', 'Potato healthy', 
         'Raspberry healthy', 'Soybean healthy', 'Squash Powdery mildew', 
         'Strawberry Leaf scorch', 'Strawberry healthy', 'Tomato Bacterial spot', 
         'Tomato Early blight', 'Tomato Late blight', 'Tomato Leaf Mold', 
         'Tomato Septoria leaf spot', 'Tomato Spider mites', 
         'Tomato Target Spot', 'Tomato Yellow Leaf Curl Virus', 
         'Tomato mosaic virus', 'Tomato healthy']



model = load_model("LensFleur-Flora.AI/model_finetuned.h5") 

@app.route('/', methods = ['GET'])
def index():
    return render_template('index1.html')
@app.route('/login', methods = ['GET', 'POST'])
def login():
    msg = 'Log In To Continue'
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            return render_template('index1.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        aadhaar = request.form['aadhaar']
        email = request.form['email']
        city = request.form['city_state']
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            msg = 'Invalid email address !'
        elif not re.match(r'^[a-zA-Z0-9]+$', username):
            msg = 'Username must contain only characters and numbers !'
        elif not re.match(r'^(?=.*[A-Z])(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):#for length of password
            msg = 'Password must contain atleast 8 characters, 1 uppercase, 1 lowercase, 1 number and 1 special character!'
        elif not username or not password or not email or not name or not aadhaar or not city:
            msg = 'Please fill out the form fully!'
        else:
            cursor.execute('INSERT INTO accounts VALUES (% s, % s, % s, %s, %s, %s)', (username, password, email, name, aadhaar,city, ))
            mysql.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)

@app.route('/home', methods = ['GET', 'POST'])
def home():
    return render_template('index1.html')

@app.route('/product', methods = ['GET', 'POST'])
def product():
    return render_template('Product.html')

@app.route('/profile', methods = ['GET', 'POST'])
def profile():
    return render_template('profiles.html')

@app.route('/chat', methods = ['GET', 'POST'])
def chat():
    return render_template('chat.html')


@app.route('/', methods = ['POST'])
def predict():
    # Get the data from the POST request.
    cur = mysql.cursor()
    image = request.files['image']
    # Make prediction using model loaded from disk as per the data.
    image_path = image.filename
    image.save(image_path)
    with open(image_path, 'rb') as src:
        copy = im(src)
    
    my_image = cv2.imread(image_path)
    my_image = cv2.resize(my_image, (224, 224) )
    my_image = my_image /255
    probabilities = model.predict(np.asarray([my_image]))[0]
    class_idx = np.argmax(probabilities)
    prediction = classes[class_idx]
    
    #Geolocation Services
    geocoder = Nominatim(user_agent = 'Flora')
    if copy.has_exif:    
        TheDegreeValue, TheMinuteValue, TheSecondValue = copy.gps_latitude
        TheLatitudeValue=TheDegreeValue+(TheMinuteValue/60)+(TheSecondValue/3600)
        TheDegreeValue, TheMinuteValue, TheSecondValue = copy.gps_longitude
        TheLongitudeValue=TheDegreeValue+(TheMinuteValue/60)+(TheSecondValue/3600)
        coord = (TheLatitudeValue, TheLongitudeValue)
        geolocation= geocoder.reverse(coord)
        
    else:
        geolocation = "No GPS Data"
    file = open("LensFleur-Flora.AI/static/" + prediction.title() + ".txt", "r") 
    if "Healthy" in prediction or "healthy" in prediction:
        basic = file.read()
       
        return render_template('Result.html', prediction=prediction, geolocation=geolocation, basic=basic)
       
    else:
        description = file.read()
        basics = description.split("Symptoms:")
        basic = basics[0]
        symp = basics[1].split("Cycle and Lethality:")
        symptoms = "Symptoms: "+symp[0]
        cyc = symp[1].split("Organic Solutions:")
        cycle = "Cycle and Lethality: "+cyc[0]
        organic = cyc[1].split("Inorganic Solutions:")
        organics = "Organic Solutions: "+ organic[0]
        inorganic = organic[1].split("Src:")
        inorganics = "Inorganic Solutions: "+inorganic[0]
        src = "Find out more at: "+inorganic[1]


        
        check = "select num_detection from detection_data where geo_location = %s and plant_disease = %s"
        num_detect = cur.execute(check, (geolocation, prediction))+1
        cur.execute("INSERT INTO detection_data  VALUES (NULL, %s, %s, %s, %s)", (session['username'], prediction, geolocation, num_detect,))
        mysql.commit()
        cur.close()

        assert1 = ""
        if num_detect > 2 and "Healthy" not in prediction.title():
            assert1 = "Data suggests there is a spike of "+prediction +" in "+str(geolocation)+". Please consult the appropriate authorities while we share our data to adequately combat the issue."
        
        return render_template('Result.html', prediction=prediction, geolocation=geolocation, basic=basic, symptoms=symptoms, cycle=cycle, organics=organics, inorganics=inorganics, src=src, 
                               assert1 = assert1)
    

if __name__ == '__main__':
    app.run(port = 3000, debug=True)
    
