#!/usr/bin/python3

# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, session, render_template, flash
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY=os.environ.get('SECRET_KEY', 'development key')
))

strings = {
    
    "BusinessTravel": ['Travel_Rarely', 'Travel_Frequently', 'Non-Travel'],
    "Department": ['Sales', 'Research & Development', 'Human Resources'],
    "EducationField": ['Life Sciences', 'Other', 'Medical', 'Marketing',
       'Technical Degree', 'Human Resources'],
    "Gender": ['Female', 'Male'],
    "JobRole": ['Sales Executive', 'Research Scientist', 'Laboratory Technician',
       'Manufacturing Director', 'Healthcare Representative', 'Manager',
       'Sales Representative', 'Research Director', 'Human Resources'],
    "MaritalStatus": ['Single', 'Married', 'Divorced'],
    "Over18": ['N','Y'],
    "OverTime": ['No', 'Yes'],
  
}

# min, max, default value
floats = {    
    "Age": [0, 100, 30],
    "DailyRate": [0,2000, 800],
    "DistanceFromHome": [0,100,10],
    "Education": [1,5,3],
    #"EmployeeCount": [1,1,1],
    #"EmployeeNumber": [1,3000,1],
    "JobInvolvement": [1,4,3],
    "JobLevel": [1,5,2],
    "JobSatisfaction": [1,4,3],
    "MonthlyIncome": [0,20000,6500],
    "MonthlyRate": [0,30000,15000],
    "HourlyRate": [0,100,65],
    "PercentSalaryHike": [0,30,15],
    "PerformanceRating": [1,4,3],
    "RelationshipSatisfaction": [1,4,3],
    "EnvironmentSatisfaction": [1,4,2],
    "StandardHours": [80,80,80],
    "StockOptionLevel": [0,3,1],
    "TotalWorkingYears": [0,50,11],
    "TrainingTimesLastYear": [0,6,3],
    "WorkLifeBalance": [1,4,3],
    "NumCompaniesWorked": [0,10,3],
    "YearsAtCompany": [0,50,7],
    "YearsInCurrentRole": [0,20,4],
    "YearsSinceLastPromotion": [0,20,2],
    "YearsWithCurrManager": [0,20,4],
     "JobSatisfaction": [1,4,3]
  
}

# # min, max, default value
# ints = {
#     "Age": [0, 100, 30],
#     "JobSatisfaction": [1,4,3]
# }

labels = ["No Risk", "Risk"]


def generate_input_lines():
    result = f'<table>'

    counter = 0
    for k in floats.keys():
        minn, maxx, vall = floats[k]
        if (counter % 2 == 0):
            result += f'<tr>'
        result += f'<td>{k}'
        result += f'<input type="number" class="form-control" min="{minn}" max="{maxx}" step="1" name="{k}" id="{k}" value="{vall}" required (this.value)">'
        result += f'</td>'
        if (counter % 2 == 1):
            result += f'</tr>'
        counter = counter + 1

    counter = 0
    for k in ints.keys():
        minn, maxx, vall = ints[k]
        if (counter % 2 == 0):
            result += f'<tr>'
        result += f'<td>{k}'
        result += f'<input type="number" class="form-control" min="{minn}" max="{maxx}" step="1" name="{k}" id="{k}" value="{vall}" required (this.value)">'
        result += f'</td>'
        if (counter % 2 == 1):
            result += f'</tr>'
        counter = counter + 1

    counter = 0
    for k in strings.keys():
        if (counter % 2 == 0):
            result += f'<tr>'
        result += f'<td>{k}'
        result += f'<select class="form-control" name="{k}">'
        for value in strings[k]:
            result += f'<option value="{value}" selected>{value}</option>'
        result += f'</select>'
        result += f'</td>'
        if (counter % 2 == 1):
            result += f'</tr>'
        counter = counter + 1

    result += f'</table>'

    return result


app.jinja_env.globals.update(generate_input_lines=generate_input_lines)


def get_token():
    auth_token = os.environ.get('AUTH_TOKEN')
    api_token = os.environ.get("API_TOKEN")
    token_request_url = os.environ.get("TOKEN_REQUEST_URL")

    if (auth_token):
        # All three are set. bad bad!
        if (api_token and auth_token):
            raise EnvironmentError('[ENV VARIABLES] please set either "AUTH_TOKEN" or "API_TOKEN". Not both.')
        # Only TOKEN is set. good.
        else:
            return auth_token
    else:
        # Nothing is set. bad!
        if not (api_token and token_request_url):
            raise EnvironmentError('[ENV VARIABLES] Please set "API_TOKEN" as "AUTH_TOKEN" is not set.')
        # Only USERNAME, PASSWORD are set. good.
        else:
            token_response = requests.post(token_request_url, data={"apikey": api_token, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
            if token_response.status_code == 200:
                return token_response.json()["access_token"]
            else:
                raise Exception(f"Authentication returned {token_response.status_code}: {token_response.text}")


class riskForm():

    @app.route('/', methods=['GET', 'POST'])
    def index():

        if request.method == 'POST':
            ID = 999

            session['ID'] = ID
            data = {}

            for k, v in request.form.items():
                data[k] = v
                session[k] = v

            scoring_href = os.environ.get('MODEL_URL')

            if not (scoring_href):
                raise EnvironmentError('[ENV VARIABLES] Please set "URL".')

            for field in ints.keys():
                data[field] = int(data[field])
            for field in floats.keys():
                data[field] = float(data[field])

            input_data = list(data.keys())
            input_values = list(data.values())

            # Inject fields into payload to match model input schema
            extra_fields = os.environ.get('EXTRA_FIELDS').split(',')
            #print(extra_fields)
            i = 0
            for f in extra_fields:
                if f:
                    input_data.insert(i, f)
                    input_values.insert(i, None)
                    i += 1

            payload_scoring = {"input_data": [
                {"fields": input_data, "values": [input_values]}
            ]}
            print("Payload is: ")
            print(payload_scoring)
            header_online = {
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + get_token()
            }
            response_scoring = requests.post(
                scoring_href,
                verify=True,
                json=payload_scoring,
                headers=header_online)
            result = response_scoring.text
            print("Result is ", result)
            result_json = json.loads(result)

            result_keys = result_json['predictions'][0]['fields']
            result_vals = result_json['predictions'][0]['values']

            result_dict = dict(zip(result_keys, result_vals[0]))

            loan_risk = ''
            if "predictedLabel" in result_dict:
                loan_risk = result_dict["predictedLabel"].lower()
            if "prediction" in result_dict:
                loan_risk = result_dict["prediction"].lower()

            no_percent = result_dict["probability"][0] * 100
            yes_percent = result_dict["probability"][1] * 100
            flash('Percentage of this employee representing risk of attrition is: %.0f%%'
                  % yes_percent)
            return render_template(
                'score.html',
                result=result_dict,
                loan_risk=loan_risk,
                yes_percent=yes_percent,
                no_percent=no_percent,
                response_scoring=response_scoring,
                labels=labels)

        else:
            return render_template('input.html')


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
port = os.environ.get('PORT', '5000')
host = os.environ.get('HOST', '0.0.0.0')
if __name__ == "__main__":
    app.run(host=host, port=int(port))
