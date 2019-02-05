from __future__ import print_function
import os
import random
from flask import Flask, url_for, render_template, request, redirect, session
from flask import request, flash, abort ,g
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user , logout_user , current_user , login_required, LoginManager
from flask_login import UserMixin
from flask_session import Session
import tweepy 
from jinja2 import nodes
from jinja2.ext import Extension
import json
from os.path import join, dirname
from watson_developer_cloud import ToneAnalyzerV3
from watson_developer_cloud.tone_analyzer_v3 import ToneInput
import json

service = ToneAnalyzerV3(
     ## url is optional, and defaults to the URL below. Use the correct URL for your region.
    version='2017-09-21',
    iam_apikey=' ',
    url='https://gateway-lon.watsonplatform.net/tone-analyzer/api')
  
# Fill the X's with the credentials obtained by  
# following the above mentioned procedure. 
consumer_key = " " 
consumer_secret = " "
access_key = " "
access_secret = " "


project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "logindatabase.db"))

app = Flask(__name__)
SQLALCHEMY_TRACK_MODIFICATIONS = True
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config['TESTING'] = False
app.secret_key = '\xdf\xcd1\x17\x18w2:\xb77,j5\xc8*\xaeb\xe1/U.F\x17\xde'
db = SQLAlchemy(app)


login = LoginManager()
login.init_app(app)
login.login_view = 'login'

@login.user_loader
def load_user(user_id):
	return User.query.get(user_id)

dict = {"Joy":"https://cdn.shopify.com/s/files/1/1061/1924/products/Smiling_Face_Emoji_large.png?v=1480481056",
		"Anger":"https://cdn4.iconfinder.com/data/icons/reaction/32/angry-512.png",
		"Fear":"https://cdn.shopify.com/s/files/1/1061/1924/products/Fearful_Face_Emoji_large.png?v=1480481053",
		"Sadness":"https://cdn.shopify.com/s/files/1/1061/1924/products/Sad_Face_Emoji_grande.png?v=1480481055",
		"Analytical":"https://cdn170.picsart.com/upscale-239492790047212.png?r1024x1024",
		"Tentative":"https://i0.wp.com/www.emojifoundation.com/wp-content/uploads/2017/07/Thinking_Face_Emoji.png",
		"Neutral":"https://cdn.shopify.com/s/files/1/1061/1924/products/Neutral_Face_Emoji_large.png?v=1480481054",
		"Confident":"https://www.redwoodfalls.org/wp-content/uploads/2017/06/sunglass-emoji.png",
		"Disgust":"http://cdn.shopify.com/s/files/1/1061/1924/products/Confounded_Face_Emoji_Icon_ios10_grande.png?v=1542436041",
}
dictcolor={
"Joy": "#0091ff",
"Anger": "#dd2325",
"Fear": "#40892f",
"Sadness": "#ffb0b1",
"Analytical": "#2a97d8",
"Tentative" : "#ff415d",
"Confident": "#6d2f9b",
"Neutral": "#a96f9f",
"Disgust": "#b73767",

}
class User(db.Model):
	id= db.Column(db.Integer, unique=True)
	emailid= db.Column(db.String(80), unique=True)
	username = db.Column(db.String(80), unique=True, primary_key=True)
	password = db.Column(db.String(80), unique=True)

	def __init__(self, id, emailid ,username, password):
		self.username = username
		self.password = password
		self.emailid= emailid

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False
	def get_id(self):
		return unicode(self.id)

	def __repr__(self):
		return '<User %r>' %(self.username)





@app.route('/login', methods=['GET', 'POST'])
def login():
	user_id = session.get('id')
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	if request.method == 'GET':
		return render_template("login.html")
	#nme=User(id=1,emailid=request.form.get("emailid"), password=request.form.get("password"))
	em=request.form.get("emailid")
	pas=request.form.get('password')

	user = User.query.filter_by(emailid=request.form.get("emailid"),password=request.form.get('password')).first()
	if len(em)==0 or  len(pas)==0:
		if len(em)==0:
			flash("Email-Id is required")
		
		if len(pas)==0:
			flash("Password is required")
		session['logged_in']=False
		return redirect(url_for('login'))
		
	elif user is None:
		flash('Invalid Email-Id or Password')
		session['logged_in']=False
		print("#")
		return redirect(url_for('login'))
	else:
		login_user(user)
		session['logged_in'] = True
		flash("Logged in Successfully")
		print("*")
		session['this'] = user.username
		print(user.username)
		return redirect(url_for('home'))
	return render_template('login.html', title='Sign In')

@app.route('/', methods=['GET', 'POST'])
def home():
	user_id = session.get('id')

	if 'logged_in' not in session:
		session['logged_in']=False
		return render_template('index1a.html',uname="")
	elif session['logged_in'] is False:
		
		return render_template('index1a.html',uname="")
	else:
		
		nme = session['this']
		print(nme)
		
		
		auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
  
        # Access to user's access key and access secret 
		auth.set_access_token(access_key, access_secret) 
  
        # Calling api 
		api = tweepy.API(auth) 
  
        # 200 tweets to be extracted 
		number_of_tweets=3
		tweets = api.user_timeline(screen_name=nme) 
		results = api.get_user(nme)
		url = "https://avatars.io/twitter/"+nme
  
        # Empty Array 
		tmp=[]  
  
        # create array of tweet information: username,  
        # tweet id, date/time, text 
		tweets_for_csv = [tweet.text for tweet in tweets] # CSV file created  
		for j in tweets_for_csv: 
  
            # Appending tweets to the empty array tmp 
			tmp.append(j)  

		tlen=len(tmp)
		results = api.get_user(nme)
		fname=results.name
		prlink = "https://twitter.com/intent/user?user_id=" + str(results.id)

		moodans=[]
		for item in tmp:
			tone_input = ToneInput(item)
			tone = service.tone(tone_input=tone_input, content_type="application/json", sentences=False).get_result()
			#print(json.dumps(tone, indent=2))
			parsed = json.loads(json.dumps(tone, indent=2))
		
			i=0;
			ak="Neutral"
			for tones in parsed['document_tone']['tones']:
				ak=tones['tone_name']
				i=i+1
				if(i==1):
					break


			moodans.append(ak)
		return render_template('index1a.html',uname=nme,tmp=tmp,dictcolor=dictcolor,moodans=moodans,dict=dict,url=url,tlen=tlen,prlink=prlink,fname=fname)


@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.form:
		try:
			
			existu = User.query.filter_by(username=request.form.get("username")).scalar()
			existe = User.query.filter_by(username=request.form.get("emailid")).scalar()
			existp = User.query.filter_by(username=request.form.get("password")).scalar()


			new_user = User(id=1,emailid=request.form.get("emailid"),username=request.form.get("username"), password=request.form.get("password"))
			if existu is not None:
				flash("User name already taken! Can't register")
			elif existe is not None:
				flash("Email-Id already taken! Can't register")
			elif existp is not None:
				flash("Password already taken! Can't register")
			elif len(new_user.emailid)==0 or  len(new_user.password)==0 or  len(new_user.username)==0:
				if len(new_user.emailid)==0:
					flash("Email-Id is required")
				if len(new_user.username)==0:
					flash("UserName is required")
				if len(new_user.password)==0:
					flash("Password is required")
				
			else:
				db.session.add(new_user)
				db.session.commit()
				flash("Registered Successfully")
				print('*')
				return render_template('login.html')
		except Exception as e:
			print("Failed to add")
			print(e)
			flash('Invalid Credentials')
			db.session.rollback();
	return render_template('register.html')


@app.route("/logout")
def logout():
	session['logged_in'] = False
	return redirect(url_for('home'))


if __name__ == "__main__":
	#session['logged_in']=None
	#Session.init_app(app)
	jinja_env = Environment(extensions=['jinja2.ext.do'])
	app.run(host='0.0.0.0', debug=True)
	

   