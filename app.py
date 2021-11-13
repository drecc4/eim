import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date
import random
from twilio.rest import Client

#------------------------------------------------------------------------------------------

#the following line needs your Twilio Account SID and Auth Token
account_sid = 'ACb023703214a282446ab1efb0289ae5ae'
auth_token = '410736297f23f31e82980db30f6a121b'
client = Client(account_sid, auth_token)


#------------------------------------------------------------------------------------------

#Sidebar Settings

#main navigation, page selection
st.sidebar.title('Menu')
st.sidebar.markdown(' ')
selected_page = st.sidebar.selectbox('Page Selection:', ['Student Gradebook', 'Coach Dashboard'])
st.sidebar.markdown('-----')

#page sidebar settings
st.sidebar.subheader('Notification Example')
st.sidebar.markdown(' ')

#generate random grade button
st.sidebar.write('Use this section to simulate the behavior of a new (bad) grade entering the gradebook.')
st.sidebar.write('Enter your phone number in the box below to test the sms alert functionality.')
phone_input = st.sidebar.text_input('Phone Number:')
new_grade_button = st.sidebar.button('Generate Random Grade')


st.sidebar.markdown('-----')
st.sidebar.subheader('Page Settings')
st.sidebar.markdown(' ')


#student list
student_names = ['Tim Duncan', 'Tony Parker', 'David Robinson']


#------------------------------------------------------------------------------------------

#App Settings

#load and prepare sample data, calculate rolling gpa
df_gradebook = pd.read_excel('sample_student_gradebook.xlsx')
df_gradebook = df_gradebook.sort_values(by=['Student','Date'], ascending=True)
df_gradebook['RunningGPA'] = df_gradebook.groupby(['Student'])[['Grade']].transform(lambda x: x.rolling(20, 1).mean().astype(int))

#lists to simplify selection in next step
course_codes = list(df_gradebook.CourseCode.unique())
course_names = list(df_gradebook.Course.unique())

#this logic triggered on button click
if new_grade_button:

    #step 1: logic to add new grade
    def add_random_grade():
        rand_course_selector = random.randrange(0,3)
        student_random_grades = []

        for student in student_names:
            student = {
                'Date': date.today(),
                'Student': student, 
                'CourseCode': course_codes[rand_course_selector],
                'Course': course_names[rand_course_selector],
                'Assignment': 6,
                'Grade':int(random.randrange(60,95))
                }
            student_random_grades.append(student)
        return(student_random_grades)

    #step 2: logic to append grades to gradebook and re-calculate gpa
    def add_random_grades_to_gradebook(df, student_random_grades):
        df = df.append(student_random_grades, ignore_index=True)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by=['Student','Date'], ascending=True)
        df['RunningGPA'] = df.groupby(['Student'])[['Grade']].transform(lambda x: x.rolling(20, 1).mean().astype(int))
        return(df)


    #run functions
    student_random_grades = add_random_grade()
    df_gradebook = add_random_grades_to_gradebook(df_gradebook, student_random_grades)


#step 3: logic to send sms alert
def send_sms_alert(phone, student, grade, course_code, gpa):
    if len(phone_input) > 0:
        to_number = f'+1{phone}'
        from_number = "+13185089187"
        alert_message = f'''Hey Coach, Your student, {student} just received a {grade} on their {course_code} assignment. This score lowers their overall gpa to {gpa}.'''
        client.messages.create(to=to_number, from_=from_number, body=alert_message)
    else:
        ''

#------------------------------------------------------------------------------------------

#Page Settings

#conditional page selection
if selected_page == 'Student Gradebook':

    #assumption for failed grade, at risk student
    assumption_failed_grade = 70
    assumption_at_risk = st.sidebar.number_input('At Risk Student Threshold:', 60, 80, step=5, value=75)

    #page title and description
    st.title('Student Gradebook')
    st.text('This page aggregates all course grades for a selected student')
    st.markdown(' ')
    selection_student = st.selectbox('Selected Student:', student_names)
    st.markdown('-----')

    #----------------------------------------------------------------------------

    #filter data for selected student, and pivot
    df_gradebook_selection = df_gradebook.loc[df_gradebook['Student'] == selection_student].sort_values(by=['CourseCode', 'Date'], ascending=True)
    df_gradebook_selection = df_gradebook_selection.sort_values(by='Date', ascending=True)
    df_gradebook_selection_pivot = df_gradebook_selection.pivot_table(index='Assignment', columns='CourseCode', values='Grade', fill_value=0)
    
    
    #dynamic warning box based on student last assignment score
    df_gradebook_selection_last_grade = df_gradebook_selection.tail(1)
    last_grade_abbvname = df_gradebook_selection_last_grade.Student.str.split(expand=True)[0].max()
    last_grade_score = df_gradebook_selection_last_grade.Grade.max()
    last_grade_course = df_gradebook_selection_last_grade.Course.max()
    last_grade_gpa = df_gradebook_selection_last_grade.RunningGPA.max()
    last_grade_date = df_gradebook_selection_last_grade.Date.max()

    df_gradebook_selection_courses = df_gradebook_selection.groupby(['CourseCode']).tail(1)
    df_gradebook_selection_courses['AtRiskCourses'] = np.where(df_gradebook_selection_courses['RunningGPA'] <= assumption_at_risk, 1, 0)
    at_risk_courses = df_gradebook_selection_courses['AtRiskCourses'].sum()

    if last_grade_score < assumption_at_risk:
        st.error(f'Notification: {last_grade_abbvname} scored a {last_grade_score} on his last {last_grade_course} assignment.')

    elif last_grade_score >= assumption_at_risk:
        st.success(f'Notification: {last_grade_abbvname} scored a {last_grade_score} on his last {last_grade_course} assignment.')
    
    st.markdown(' ')

    #metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Current GPA", value=int(last_grade_gpa))
    with col2:
        st.metric(label="Last Grade", value=int(last_grade_score))
    with col3:
        if at_risk_courses > 0:
            st.metric(label="Courses At Risk", value=at_risk_courses.astype(float))
        else:
            st.metric(label="Courses At Risk", value='None')
    

    #function to conditionally color charts
    def color_area_on_gpa(gpa):
        if gpa > assumption_at_risk:
            color = '#00CC96'
        else:
            color = '#EF553B'
        return (color)


    #plot 1: overall gpa and assignment grades
    st.subheader(f"GPA Trend with Grade History")
    
    fig_gpa = px.area(df_gradebook_selection, x='Date', y='RunningGPA')
    fig_gpa.update_traces(line_color=color_area_on_gpa(last_grade_gpa), line_width=5)
    
    fig_grades = px.scatter(df_gradebook_selection, x='Date', y='Grade', hover_name="CourseCode", hover_data=["Course", "Date", "Grade"])
    fig_grades.update_traces(marker=dict(size=13, color='LightGrey', line=dict(width=2.2, color='#171717')))

    fig_combined = go.Figure(data = fig_gpa.data + fig_grades.data)

    fig_combined.update_yaxes(range=[50, 105])
    fig_combined.add_hline(y=assumption_at_risk, line_dash="dot", xref='paper')

    fig_combined.add_annotation(
        x=0.94, y=last_grade_score*1.05, xref="paper", yref="y", text=f'{last_grade_score}', font_size=24, font_color='#171717', 
        showarrow=True, ax=0, ay=-60, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='#171717'
        )
    
    fig_combined.update_layout(
        title_font_color = 'Black',
        font_family = 'Arial',
        margin=dict(l=60, r=10, b=70, t=40, pad=10),
        paper_bgcolor='rgb(250,250,250)',
        plot_bgcolor='rgb(250,250,250)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.94))

    st.plotly_chart(fig_combined, use_container_width=True)


    #student combined gradebook
    st.table(df_gradebook_selection_pivot)

    send_sms_alert(phone_input, selection_student, last_grade_score, last_grade_course, last_grade_gpa)


elif selected_page == 'Coach Dashboard':

    #page title and description
    st.title('Coach Dashboard')
    st.text('This page summarizes student performance for a given Coach')
    st.markdown('-----')


    st.write('Coming Soon')

