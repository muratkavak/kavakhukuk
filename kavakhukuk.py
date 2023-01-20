from flask import Flask,render_template,flash,redirect,url_for,session,logging,request,g
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

bcrypt = Bcrypt()


db = SQLAlchemy()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////Users/MURAT/OneDrive/Masaüstü/kavakhukuk/kavakhukuk.db"

db = SQLAlchemy(app)

app.secret_key="kavakhukuk"



class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String)
    email = db.Column(db.String)
class articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    content = db.Column(db.String)

class LoginForm(Form):
    username=StringField("Kullanıcı Adı:")
    password=PasswordField("Parola:")

class verifyForm(Form):
    code=StringField("Gönderilen Kod:")

class registerform(Form):
    username= StringField("Kullanıcı Adı:",validators=[validators.Length(min=5,max=14)])
    email= StringField("Mail Adresi:",validators=[validators.Email(message="Gecerli bir mail adresi giriniz:")])
    password= PasswordField("Parola",validators=[
        validators.DataRequired("Lutfen bir parola giriniz:")])

class passchange(Form):
    newpass=PasswordField("Yeni Parola:")
    newpassconfirm=PasswordField("Parola Tekrar:")

class ArticleFrom(Form):
    title=StringField("Makale Baslıgı:",validators=[validators.length(min=5,max=100)])
    content=TextAreaField("İcerik:",validators=[validators.length(min=20)])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giris yapınız.","danger")
            return redirect(url_for("login"))
    return decorated_function


@app.route("/register",methods=["GET","POST"])
def register():
    form=registerform(request.form)
    if request.method=="POST" and form.validate():
        newusername=form.username.data
        newemail=form.email.data
        newpassword=bcrypt.generate_password_hash(form.password.data)
        user=users(username=newusername,password=newpassword,email=newemail)
        db.session.add(user)
        db.session.commit()
        flash("Basariyla kayit oldunuz.","success")
        return redirect(url_for("index"))
    else:
        return render_template("register.html",form =form)


@app.route("/login",methods=["GET","POST"])
def login():
    loginform=LoginForm(request.form)
    if request.method=="POST":
        username=loginform.username.data
        password=loginform.password.data
        data=users.query.filter_by(username=username).first()
        if data:
            realPassword=data.password
            if bcrypt.check_password_hash(realPassword,password):
                session["twostep"]=True
                session["username"]=username
                """flash("Basariyla giris yaptiniz.","success")
                session["logged_in"]=True
                session["username"]=username"""
                return redirect(url_for("twostep"))
            else:
                flash("Sifre hatali.","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunamadı.","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html",loginform=loginform)

@app.route("/twostep", methods=["GET", "POST"])
def twostep():
    current_time = datetime.datetime.now().minute
    #cd=datetime.datetime.now()
    #day=cd.day
    random.seed(current_time)
    form = verifyForm(request.form)
    kod = random.randint(1000,9999)
    if "twostep" in session:
        if request.method == "POST":
            code=int(form.code.data)
            if kod == code:
                session["logged_in"] = True
                flash("Basariyla giris yaptiniz.","success")
                return redirect(url_for("index"))
            else:
                session.clear()
                flash("Hatalı kod !","danger")
                return redirect(url_for("login"))
        else:
            mesaj = MIMEMultipart()
            mesaj["From"] = "mrtkvk2135@gmail.com"
            mesaj["To"] = "kavakmuratt@gmail.com"
            mesaj["Subject"] = "Onay Kodu"
            yazi = str(kod)
            mesajgovde = MIMEText(yazi, "plain")
            mesaj.attach(mesajgovde)
            mail = smtplib.SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login("mrtkvk2135@gmail.com","yypducysrkupuhip")
            mail.sendmail(mesaj["From"], mesaj["To"], mesaj.as_string())
            mail.close()
            return render_template("twostep.html", form=form)
    else:
        flash("Giris yapınız.","danger")
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Basariyla cikis yapildi.","success")
    return redirect(url_for("index"))
@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/dashboard")
@login_required
def dashboard():
    data=articles.query.all()
    if data:
        return render_template("dashboard.html",articles=data)
    else:
        flash("")
        return render_template("dashboard.html")

@app.route("/article/<string:id>")
def article(id):

    article=articles.query.filter_by(id=id).first()

    if article:
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")

@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form=ArticleFrom(request.form)

    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data
        newarticle=articles(title=title,content=content)
        db.session.add(newarticle)
        db.session.commit()
        flash("Makale Kaydı Basariyla Gerceklesti !","success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html",form=form)

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    article = articles.query.filter_by(id = id).first()


    if article:
        db.session.delete(article)
        db.session.commit()
        flash("Makale silme basarili.","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok.","danger")
        return redirect(url_for("index"))

@app.route("/edit/<string:id>",methods=["POST","GET"])
@login_required
def update(id):

    if request.method=="GET":
        article = articles.query.filter_by(id = id).first()
        if article:
            form=ArticleFrom()
            form.title.data=article.title
            form.content.data=article.content
            return render_template("update.html",form=form)

        else:
            flash("Böyle bir makale yok.","danger")
            return redirect(url_for("index"))
    else:
        article = articles.query.filter_by(id = id).first()
        form=ArticleFrom(request.form)
        newtitle=form.title.data
        newcontent=form.content.data
        article.title=newtitle
        article.content=newcontent
        db.session.commit()

        flash("Makale basariyla güncellendi.","success")
        return redirect(url_for("dashboard"))

@app.route("/articles")
def articless():
    data=articles.query.all()
    if data:
        return render_template("articles.html",articles=data)
    else:
        return render_template("articles.html")

@app.route("/changepassword",methods=["POST","GET"])
@login_required
def changePass():
    form=passchange(request.form)
    if request.method=="POST":
        newpass=form.newpass.data
        newpassconfirm=form.newpassconfirm.data
        user=users.query.filter_by(username=session["username"]).first()
        if newpass==newpassconfirm:
            user.password=bcrypt.generate_password_hash(newpass)
            db.session.commit()
            flash("Sifre Degistirme Basarili.","success")
            return redirect(url_for("index"))
        else:
            flash("Girilen sifreler uyusmuyor.","warning")
            return redirect(url_for("changePass"))
    else:
        return render_template("changepassword.html",form=form)

@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        results = articles.query.filter(articles.title.like(f"%{keyword}%")).all()
        if results:
            return render_template("articles.html",articles=results)
        else:
            flash("Aranan kelimeye uygun makale bulanamadı.","warning")
            return redirect(url_for("articless"))

@app.route("/")
def index():
    data = articles.query.order_by(articles.id.desc()).limit(3).all()
    return render_template("index.html",articles=data)

@app.route("/about")
def about():
    return render_template("about.html")

if __name__=="__main__":
    app.run(debug=True)