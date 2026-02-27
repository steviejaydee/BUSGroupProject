from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SelectField, TextAreaField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Length

class TriageForm(FlaskForm):
  name = StringField("What is your full name?", 
                     validators=[DataRequired()])
  dob = DateField("What is your date of birth?", 
                  format="%Y-%m-%d", 
                  validators=[DataRequired()])
  problem = TextAreaField("Give a brief description of the problems you are experiencing",  
                          validators=[DataRequired(), Length(0, 500)])
  type = SelectField("Do you have a preference for the type of help you would like to receive?", 
                     choices=[("none", "No preference"), 
                              ("counselling", "Counselling"),
                              ("cbt", "Cognitive Behavioural Therapy (CBT)")], 
                     validators=[DataRequired()])
  addon = TextAreaField("Additional Comments", 
                        validators=[Length(0, 500)])
  submit = SubmitField("Submit")
