import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

#------------------------------------------------------------------------------------------

#Sidebar Settings

#main navigation, page selection
st.sidebar.title('Menu')
st.sidebar.markdown(' ')
selected_page = st.sidebar.selectbox('Page Selection:', ['Coach Dashboard', 'Student Gradebook'])
st.sidebar.markdown('-----')


#load and prepare sample data, calculate rolling gpa
df_gradebook = pd.read_excel('sample_student_gradebook.xlsx')
df_gradebook = df_gradebook.sort_values(by=['Student','Date'], ascending=True)
df_gradebook['RunningGPA'] = df_gradebook.groupby(['Student'])[['Grade']].transform(lambda x: x.rolling(20, 1).mean().astype(int))


#conditional page selection
if selected_page == 'Student Gradebook':

    #page sidebar settings
    st.sidebar.subheader('Page Settings')

    #failed grade assumption
    assumption_failed_grade = st.sidebar.number_input('Failed Assignment Assumption', 50, 80, step=5, value=70)

    #page title and description
    st.title('Student Gradebook')
    st.text('This page aggregates all course grades for a selected student')
    st.markdown('-----')

    #student selection
    student_names = ['Tim Duncan', 'Tony Parker', 'David Robinson']
    selection_student = st.selectbox('Student Selection:', student_names)
    st.markdown(' ')

    #----------------------------------------------------------------------------

    #filter data for selected student, and pivot
    df_gradebook_selection = df_gradebook.loc[df_gradebook['Student'] == selection_student]
    df_gradebook_selection_pivot = df_gradebook_selection.pivot(index='Assignment', columns='CourseCode', values='Grade')

    #plot 1: overall gpa
    st.subheader(f"Overall GPA Trend") 
    fig = px.line(df_gradebook_selection, x='Date', y='RunningGPA')
    fig.update_layout(
        title_font_color = 'Black',
        font_family = 'Arial',
        margin=dict(l=80, r=50, b=70, t=50, pad=0),
        paper_bgcolor='rgb(250,250,250)',
        plot_bgcolor='rgb(250,250,250)')

    st.plotly_chart(fig, use_container_width=True)
    st.markdown(' ')


    #plot 2: course gpa
    st.subheader(f"Course GPA Trend") 
    fig = px.line(df_gradebook_selection, x='Date', y='Grade', color='CourseCode')
    fig.update_layout(
        title_font_color = 'Black',
        font_family = 'Arial',
        margin=dict(l=80, r=50, b=70, t=50, pad=0),
        paper_bgcolor='rgb(250,250,250)',
        plot_bgcolor='rgb(250,250,250)')

    st.plotly_chart(fig, use_container_width=True)


    #plot 3: assignment table
    def highlight(number):
        criteria = number < assumption_failed_grade
        return ['background-color: rgb(242,104,97)' if i else '' for i in criteria]
    
    #student combined gradebook
    st.table(df_gradebook_selection_pivot.style.apply(highlight, axis=0))




elif selected_page == 'Coach Dashboard':
    
    #page title and description
    st.title('Coach Dashboard')
    st.text('This page summarizes student performance for a given Coach')
    st.markdown('-----')


    #plot 1: overall gpa by stuent
    st.subheader(f"Student Overall GPA Trend") 
    fig = px.line(df_gradebook, x='Date', y='RunningGPA', facet_col='Student', facet_col_spacing=0.1)
    fig.update_layout(
        title_font_color = 'Black',
        font_family = 'Arial',
        margin=dict(l=80, r=50, b=70, t=50, pad=0),
        height=400,
        paper_bgcolor='rgb(250,250,250)',
        plot_bgcolor='rgb(250,250,250)')

    st.plotly_chart(fig, use_container_width=True)
    st.markdown(' ')




    #plot 1: overall gpa by stuent
    st.subheader(f"Student Overall GPA Trend") 
    fig = px.line(df_gradebook, x='Date', y='RunningGPA', color='Student')
    fig.update_layout(
        title_font_color = 'Black',
        font_family = 'Arial',
        margin=dict(l=80, r=50, b=70, t=50, pad=0),
        paper_bgcolor='rgb(250,250,250)',
        plot_bgcolor='rgb(250,250,250)')

    st.plotly_chart(fig, use_container_width=True)
    st.markdown(' ')


