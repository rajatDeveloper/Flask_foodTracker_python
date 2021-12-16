from logging import log
import re
from typing import DefaultDict
from flask import Flask, render_template, request, session, redirect,url_for
from flask.json.tag import PassDict
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pymysql
import json
from werkzeug.utils import secure_filename

import smtplib
import os
import math
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

log_food = db.Table('log_food',
                    db.Column('log_id', db.Integer, db.ForeignKey(
                        'log.id'), primary_key=True),
                    db.Column('food_id', db.Integer, db.ForeignKey(
                        'food.id'), primary_key=True)
                    )


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    proteins = db.Column(db.Integer, nullable=False)
    carbs = db.Column(db.Integer, nullable=False)
    fats = db.Column(db.Integer, nullable=False)

    @property
    def calories(self):
        return self.proteins * 4 + self.carbs * 4 + self.fats * 9


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    foods = db.relationship('Food', secondary=log_food, lazy='dynamic')


 

@app.route('/')
def index():
    logs = Log.query.order_by(Log.date.desc()).all()

    log_dates = []

    for log in logs:
        proteins = 0
        carbs = 0
        fats = 0
        calories = 0

        for food in log.foods:
            proteins += food.proteins
            carbs += food.carbs 
            fats += food.fats
            calories += food.calories

        log_dates.append({
            'log_date' : log,
            'proteins' : proteins,
            'carbs' : carbs,
            'fats' : fats,
            'calories' : calories
        })

    return render_template('index.html', log_dates=log_dates)

@app.route('/create_log',methods=['POST'])
def create_log():
    date = request.form.get('date')
    log = Log(date=datetime.strptime(date,'%Y-%m-%d'))
    db.session.add(log)
    db.session.commit()
    return redirect(url_for('view',log_id=log.id))

@app.route('/add')
def add():
    foods = Food.query.all()
    return render_template('add.html',foods=foods,food=None)


@app.route('/add', methods=['POST'])
def add_post():
    food_name = request.form.get('food-name')
    proteins = request.form.get('protein')
    carbs = request.form.get('carbohydrates')
    fats = request.form.get('fat')

    food_id = request.form.get('food-id')

    if food_id:
        food = Food.query.get_or_404(food_id)
        food.name = food_name
        food.proteins = proteins
        food.carbs = carbs
        food.fats = fats

    else:
        new_food = Food(
            name=food_name,
            proteins=proteins,
            carbs=carbs,
            fats=fats
        )

        db.session.add(new_food)

    db.session.commit()

    return redirect(url_for('add'))

   
   
@app.route('/delete_food/<int:food_id>')
def delete_food(food_id):
    
    food = Food.query.get(food_id)
    db.session.delete(food)
    db.session.commit()

    return redirect('/add')

@app.route('/edit_food/<int:food_id>')
def edit_food(food_id):
    food = Food.query.get(food_id)
    
    return render_template('add.html',food=food)


@app.route('/view/<int:log_id>')
def view(log_id):
    log = Log.query.get_or_404(log_id)
    foods = Food.query.all()
    totals ={
        'protein':0,
        'carbs':0,
        'fat':0,
        'calories':0
    }
    for food in log.foods:
        totals['protein'] += food.proteins
        totals['carbs'] += food.carbs
        totals['fat']+= food.fats
        totals['calories']+=food.calories
    return render_template('view.html',foods=foods,log=log,totals=totals)

@app.route('/add_food_to_log/<int:log_id>',methods=['POST'])
def add_food_to_log(log_id):
    log = Log.query.get_or_404(log_id)
    selected_food = request.form.get('food-select')
    food = Food.query.get(int(selected_food))
    log.foods.append(food)
    db.session.commit()
    return redirect(url_for('view',log_id=log_id))        

@app.route('/remove_food_from_log/<int:log_id>/<int:food_id>')
def remove_food_from_log(log_id,food_id):
    log = Log.query.get(log_id)
    food= Food.query.get(food_id)
    log.foods.remove(food)
    db.session.commit()
    return redirect(url_for('view',log_id=log_id))


app.run(debug=True)

