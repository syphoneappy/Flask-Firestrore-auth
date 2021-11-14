from flask import *
import pyrebase , re ,os
from functools import wraps
import sys,secrets
import firebase_admin
from firebase_admin import firestore , credentials

# firebase

config = {

}
cred = credentials.Certificate("Enter Json Credentials here")

firebase = pyrebase.initialize_app(config)


db = firebase.database();
auth = firebase.auth();

firebase_admin.initialize_app(cred, {
  'projectId': "your project id",
})

db = firebase_admin.firestore.client()

# flask
def Global(photo):
    hash_photo = secrets.token_urlsafe(10)
    _, file_extension = os.path.splitext(photo.filename)
    photo_name =hash_photo + file_extension
    return photo_name

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route("/",methods=['GET','POST'])
def basic():
    return render_template("index.html" )

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method == 'POST':
        userDetails = request.form
        AnId = userDetails['email']
        Psw = userDetails['com_pass']
        password = userDetails['password']
        name = userDetails["Name"]
        if len(password) < 8:
            flash("Password Should have atlest 8 char")
            return redirect("/")
        elif re.search('[0-9]',password) is None:
            flash("Make sure you have Any One Numeric Value")
            return redirect("/")
        elif re.search('[A-Z]',password) is None:
            flash("Make Sure you have One Capital letter")
            return redirect("/")
        elif re.match('[@]',AnId):
            flash("Make sure you have One @ Character!")
            return redirect("/")
        elif re.match('[_@$]',password):
            flash("Make sure you have One Special Character!")
            return redirect("/")
        else:
            if Psw == password:
                user = db.collection('User').document(AnId)
                res = user.get()
                try:
                    usermain = auth.create_user_with_email_and_password(AnId, password)
                    if res.exists and usermain.exists:
                        print(f'Document data: {res.to_dict()} This User exists')
                        flash("User Already exists!")
                        return redirect("/")
                    else:
                        print(u'No such document!')
                        user.set({
                        'username': AnId ,
                        'Name': name
                        })
                        flash("User Has been created Continue to login!")
                        return redirect("/")
                except:
                    flash("User Already exists")
                    return redirect("/")
            else:
                flash("Password do not match!")
        return render_template("index.html")
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == 'POST':
        userDetails = request.form
        RegisterNumber = userDetails['UserName']
        password = userDetails['password']

        user = db.collection('User').document(RegisterNumber)
        res = user.get().to_dict()
        data = res["username"]
        name = res["Name"]
        if data == RegisterNumber:
            try:
                login = auth.sign_in_with_email_and_password(RegisterNumber,password)
                session['loggedin'] = True
                session['username'] = res['username']
                session['Name'] = res["Name"]
                try:
                    if res['image'] == True or res['Date'] == True or res['Address'] == True:
                        pass
                except:
                    flash("Fill The Form!")
                    return render_template("welcome.html",user = session['username'], UserName = session['Name'])
                return redirect('/views')
            except:
                flash("Password or username is incorrect!")
                return redirect("/")
        else:
            flash("User Not found!")
            return redirect("/")
    return render_template("index.html")
@app.route("/update",methods=["GET","POST"])
def update():
    try:
        return render_template("welcome.html",user = session['username'], UserName = session["Name"])
    except:
        flash("Your Session has expired please login again!")
        return redirect("/")
@app.route("/views",methods=["GET","POST"])
def views():
    try:
        user = db.collection('User').document(session['username'])
        data = user.get().to_dict()
        storage = firebase.storage()
        link = storage.child(data['image']).get_url(None)
        print(data)
        return render_template("views.html",user = session['username'], UserName = session['Name'], Date = data["Date"] ,Address = data["Address"] ,l = link)
    except:
        flash("Your Session has expired please login again!")
        return redirect("/")

@app.route("/details",methods=["GET","POST"])
def details():
    if request.method == 'POST':
        userDetails = request.form
        Address = userDetails['Address']
        Date = userDetails['Date']
        image = request.files['image']
        storage = firebase.storage()
        My_image = Global(image)
        storage.child(My_image).put(image)
        user = db.collection('User').document(session["username"])
        res = user.get()
        user.update({
            'Address': Address ,
            'Date': Date,
            'image':My_image
        })
        flash("Your Record Has been Saved Successfully!")
        return redirect("/views")
    return redirect("/")
@app.route('/forget',methods=["GET","POST"])
def forget():
    if request.method == 'POST':
        email = request.form['UserName']
        try:
            authDomain = auth.send_password_reset_email(email)
            flash("your reset password link has been send on your email:!"+ email)
            return redirect("/forget")
        except:
            flash("incorrect Email Entered!")
            return redirect("/forget")
    return render_template("forget.html")
@app.route('/LogOut')
def LogOut():
    session.pop('loggedin',None)
    session.pop('username',None)
    session.pop('Name',None)
    session.clear()
    flash("Logged Out Successfully")
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)
