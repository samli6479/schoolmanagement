import datetime

from flask_restx import Namespace, Resource, fields
from ..utils import db
from flask import request
from ..models.students import Student
from ..models.studentcourse import StudentCourse
from ..models.courses import Course
from ..models.grade import Score
from http import HTTPStatus
from ..decorators.decorator import  teacher_required
from ..grade.grade_converter import get_grade, convert_grade_to_gpa
from dateutil.relativedelta import relativedelta
import re

students_namespace = Namespace('students', description='Namespace for Student ')

student_signup_model = students_namespace.model(
    'Signup', {
    'email': fields.String(required=True, description='User email address'),
    'full_name': fields.String(required=True, description="Full name"),
    'date_of_birth': fields.String(required=True, description="Date of Birth"),
}
)

students_fields_model = {
    'id': fields.String(),
    'email': fields.String(required=True, description='User email address'),
    'full_name': fields.String(required=True, description="Full name"),
    'date_of_birth': fields.String(required=True, description="Date of Birth"),
}

students_update_model =students_namespace.model( 'update student' ,{
    'email': fields.String(required=True, description='User email address'),
    'full_name': fields.String(required=True, description="Full Name"),
    'date_of_birth': fields.String(required=True, description="Date of birth"),
}
)

student_score_add_fields_model = {
    'student_id': fields.Integer(required=False, description='ID of student'),
    'course_id': fields.Integer(required=True, description='ID of course'),
    'score': fields.Integer(required=True, description="Score value"),
}



course_fields_model = {
    'course_id': fields.String(required=True),
}

course_retrieve_fields_model =  {
    'id': fields.Integer(),
    'name': fields.String(required=True, description="A course name"),
    'created_at': fields.DateTime( description="Course creation date"),
}

student_score_update_model = {
    'student_id': fields.Integer(required=False, description='ID of student'),
    'course_id': fields.Integer(required=True, description='ID of course'),
    'score': fields.Integer(required=True, description="Score value"),
}

course_model = students_namespace.model(
    'Course create', {
        'id': fields.Integer(description="Course's ID"),
        'name': fields.String(description="Course's Name", required=True),
    }
)
students_model = students_namespace.model('Students list ', students_fields_model)
courses_model = students_namespace.model('Students courses list ', course_retrieve_fields_model)
courses_add_model = students_namespace.model('Courses ', course_fields_model)
student_score_add_model = students_namespace.model('Courses add scores', student_score_add_fields_model)
student_update_model = students_namespace.model('Students update ', student_score_update_model)


@students_namespace.route('/register/student')
class StudentRegistrationView(Resource):

    @students_namespace.expect(student_signup_model)
    @students_namespace.doc(
        description="""
            This endpoint is used for creation of a student
            """
    )
    def post(self):
        """ Create a new Student"""
        data = request.get_json()

        # Check email address is valid or not
        email = data.get('email')
        pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if not re.match(pat,email):
            abort(HTTPStatus.CONFLICT, f"Invalid email '{email}' Please check.")
        # Check if email already exists
        if Student.get_by_email(email):
            abort(HTTPStatus.CONFLICT, f"Student with email '{email}' already exists.")
        # Create new Student
        identifier = str(random.randint(1000, 9999))
        date_of_birth_string = data.get("date_of_birth")
        date_of_birth = datetime.datetime(date_of_birth_string,'%Y%m%d')
        now = datetime.datetime.now()

        difference = relativedelta(now, date_of_birth).years
        if difference < 10:
            abort(HTTPStatus.CONFLICT, f"Student has  '{difference}' year of birthday require 10 years.")
        new_student = Student(
            email=data.get('email'),
            identifier=identifier,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            date_of_birth = date_of_birth_string
        )

        try:
            new_student.save()
        except:
            db.session.rollback()
            return {'message': 'An error occurred while saving student'}, HTTPStatus.INTERNAL_SERVER_ERROR
        return {
            'message': 'You have been registered successfully as a '}, HTTPStatus.CREATED


@students_namespace.route('')
class StudentsListView(Resource):

    @students_namespace.marshal_with(students_model)
    @students_namespace.doc(
        description=""" 
            Get All students list
            """
    )
    def get(self):
        """
        Get all Students
        """
        students = Student.query.all()
        return students , HTTPStatus.OK
    

@students_namespace.route('/<int:student_id>')
class StudentRetrieveDeleteUpdateView(Resource):

    @students_namespace.marshal_with(students_model)
    @students_namespace.doc(
        description="""
            Get Student by ID
            """
    )
    def get(self, student_id):
        """
        Retrieve a Student by its ID
        """
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return {'message':'Student does not exist'}, HTTPStatus.NOT_FOUND
        return student , HTTPStatus.OK
    
    @students_namespace.expect(students_update_model)
    @students_namespace.marshal_with(students_model)
    @students_namespace.doc(
        description="""
            Update student details
            """
    )

    def put(self, student_id):
        """ Update Student Details """
        data = request.get_json()
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return {'message': 'Student not found'}, HTTPStatus.NOT_FOUND
        student.email = data.get('email', student.email)
        student.full_name = data.get('first_name', student.full_name)
        student.date_of_birth = data.get('date_of_birth', student.date_of_birth)
        student.save()
        return student, HTTPStatus.OK
    
    
    @students_namespace.doc(
        description='Delete a Student by its ID',
        params = {
            'student_id': "The Student's ID"
        }
    )
    @teacher_required()
    def delete(self, student_id):
        """
            Delete a Student by its ID!
        """
        student = Student.get_by_id(student_id)

        student.delete()

        return {"message": "Student Successfully Deleted"}, HTTPStatus.OK
    


@students_namespace.route('/<int:student_id>/courses/grade')
class StudentCoursesGradeListView(Resource):

    def get(self, student_id):
        """
        Retrieve a Student Grade for all courses
        """     
        courses = StudentCourse.get_student_courses(student_id)
        response = []
        
        for course in courses:
            grade_response = {}
            score_in_course = Score.query.filter_by(student_id=student_id , course_id=course.id).first()
            grade_response['name'] = course.name
            if score_in_course:
                grade_response['grade'] = score_in_course.grade
            else:
                grade_response['grade'] = None
            response.append(grade_response)
        return response , HTTPStatus.OK
    

@students_namespace.route('/<int:student_id>/courses')
class StudentCoursesListView(Resource):

    def get(self, student_id):
        """
        Get a Student's Courses!
        """
            
        courses = StudentCourse.get_student_courses(student_id)
        resp = []

        for course in courses:
                course_resp = {}
                course_resp['id'] = course.id
                course_resp['name'] = course.name

                resp.append(course_resp)

        return resp, HTTPStatus.OK
    

@students_namespace.route('/course/add_score')
class StudentCourseScoreAddView(Resource):

    @students_namespace.expect(student_score_add_model)
    @students_namespace.doc(
        description=  """
        Add student score to a course.
        """
    )
    def put(self):
        """
        Grade Student Course!
        """     
        student_id = request.json['student_id']
        course_id = request.json['course_id']
        score_value = request.json['grade']
        # check if student and course exist
        student = Student.query.filter_by(id = student_id).first()
        course = Course.query.filter_by(id=course_id).first()
        if not student or not course:
            return {'message': 'Student or course not found'}, HTTPStatus.NOT_FOUND
        # check if student is registered for the course
        student_in_course = StudentCourse.query.filter_by(course_id=course.id, student_id=student.id).first() 
        if student_in_course:
            # check if the student already have a score in the course
            score = Score.query.filter_by(student_id=student_id, course_id=course_id).first()
            if score:
                score.grade = score_value
            else:
                # create a new score object and save to database
                score = Score(student_id=student_id, course_id=course_id , grade=score)
            try:
                score.save()
                return {'message': 'Score added successfully'}, HTTPStatus.CREATED
            except:
                db.session.rollback()
                return {'message': 'An error occurred while saving student course score'}, HTTPStatus.INTERNAL_SERVER_ERROR
        return {'message': 'The student is not registered for this course'}, HTTPStatus.BAD_REQUEST
