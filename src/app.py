from flask import Flask, render_template, redirect, url_for, session, abort, request, flash
import requests
from bs4 import BeautifulSoup
import psycopg2
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
import glob
import pandas as pd
import random

app = Flask(__name__ , static_url_path='/static')

# set your own database name, username and password
db = "dbname='xxxx' user='xxxx' host='localhost' password='xxxx'" #potentially wrong password
conn = psycopg2.connect(db)
cursor = conn.cursor()


bcrypt = Bcrypt(app)

@app.route("/createaccount", methods=['POST', 'GET'])
def createaccount():
    cur = conn.cursor()
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        cur.execute(f'''select * from users where username = '{new_username}' ''')
        unique = cur.fetchall()
        flash('Account created!')
        if  len(unique) == 0:
            cur.execute(f'''INSERT INTO users(username, password) VALUES ('{new_username}', '{new_password}')''')
            flash('Account created!')
            conn.commit()

            return redirect(url_for("home"))
        else: 
            flash('Username already exists!')


    return render_template("createaccount.html")



@app.route("/", methods=["POST", "GET"])
def home():
    cur = conn.cursor()
    #Getting 10 random rows from Attributes
    tenrand = '''select * from pokemon order by random() limit 10;'''
    cur.execute(tenrand)
    poke = list(cur.fetchall())
    poke = [(str(p[0]),) + p[1:] for p in poke]
    length = len(poke)

    #Getting random id from table Attributes
    randint = '''select id from pokemon order by random() limit 1;'''
    cur.execute(randint)
    row = cur.fetchone()
    randomNumber = row[0] if row is not None else None
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        if request.method == "POST":
            input_name = request.form["radioname"].lower()
            input_type = request.form["radiotype"].lower()
            input_HP = request.form["radioHP"].lower()
            input_Att = request.form["radioAtt"].lower()
            input_Def = request.form["radioDef"].lower()
            input_height = request.form["radioheight"].lower()
            input_weight = request.form["radioweight"].lower()

            # input_count = request.form["accessCount"] or -1
            # input_access = request.form["access"].lower() or "NaN"

            input_id = request.form["Pokemonid"].lower() or ""

            if input_id != "":
                input_id = input_id.zfill(4)
                return redirect(url_for("pokemonpage", Pokemonid=input_id))
            return redirect(url_for("querypage", name = input_name, type=input_type, HP=input_HP, Att = input_Att, Def = input_Def, height=input_height, weight = input_weight))
            
        length = len(poke)
        return render_template("index.html", content=poke, length=length, randomNumber = randomNumber)

@app.route("/poke/<name>/<type>/<HP>/<Att>/<Def>/<height>/<weight>")
def querypage(name, type, HP, Att, Def, height, weight):
    cur = conn.cursor()
    rest = 0

    sqlcode = f'''select * from pokemon where '''
    if name != "all":
        sqlcode += f''' name = '{name}' and'''
        rest += 1
        
    if type != "all":
        sqlcode += f''' type = '{type}' and'''
        rest += 1

    if HP != "all":
        sqlcode += f''' abilities = '{HP}' and'''
        rest += 1
        
    if Att != "all":
        sqlcode += f''' abilities = '{Att}' and'''
        rest += 1
        
    if Def != "all":
        sqlcode += f''' abilities = '{Def}' and'''
        rest += 1
        
    if height != "all":
        sqlcode += f''' height = '{height}' and'''
        rest += 1
        
    if weight != "all":
        sqlcode += f''' height = '{weight}' and'''
        rest += 1
    
    # if access != "NaN":
    #    rest += 1
    #    sqlcode += f''' accessories ~* '{access}' and'''
    
    # if int(count) != -1:
    #    rest += 1
    #    sqlcode += f''' count = '{count}' and'''

    if rest == 0: 
        sqlcode = f''' select * from pokemon'''

    else: 
        sqlcode  = sqlcode[:-3]

    cur.execute(sqlcode)
    ct = list(cur.fetchall())


    length = len(ct)

    return render_template("cryptoquery.html", content=ct, length=length)


@app.route('/login', methods=['POST'])
def do_admin_login():
    cur = conn.cursor()
    username = request.form['username']
    password = request.form['password'] 

    insys = f''' SELECT * from users where username = '{username}' and password = '{password}' '''

    cur.execute(insys)

    ifcool = len(cur.fetchall()) != 0

    if ifcool:
        session['logged_in'] = True
        session['username'] = username
    else:
        flash('wrong password!')
    return redirect(url_for("home"))


@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

@app.route("/profile")
def profile():
    if not session.get('logged_in'):
        return render_template('login.html')

    cur = conn.cursor()
    username = session['username']

    try:
        sql1 = f'''select ID, Name, Type, HP, Att, Def, Height, Weight from favorites natural join pokemon where username = '{username}' '''
        cur.execute(sql1)
        favs = cur.fetchall()
        length = len(favs)
        return render_template("profile.html", content=favs, length=length, username=username)
    except Exception as e:
        conn.rollback()
        print("Error fetching data:", str(e))
        return render_template("error.html", message="An error occurred while fetching data. Please try again later.")



@app.route("/poke/<Pokemonid>", methods=["POST", "GET"])
def pokemonpage(Pokemonid):
    if not session.get('logged_in'):
        return render_template('login.html')

    cur = conn.cursor()
    
    if request.method == "POST":
        # Add to favorites
        username = session['username']
        try: 
            sql1 = f'''insert into favorites(ID, username) values ('{Pokemonid}', '{username}') '''
            cur.execute(sql1)
            conn.commit()
        except:
            conn.rollback()

    req = "https://cryptopunks.app/cryptopunks/details/" + Pokemonid
    response = requests.get(req)
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.select("table.ms-rteTable-default tr")
    pricelist = str(soup.find(class_="Pokemon-history-row-bid")).split('\n')
    if len(pricelist) < 5:
        price = "10Ξ ($18,000)"
    else:
        price = pricelist[4].replace('</td>', '').replace('<td>', '')

    sql1 = f'''select * from pokemon where id = '{Pokemonid}' '''
    cur.execute(sql1)
    ct = cur.fetchone()

    return render_template("cryptopunk.html", content=ct, price=price)

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)