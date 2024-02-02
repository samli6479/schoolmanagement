import unittest
from .. import create_app
from ..config.config import config_dict
from ..utils import db
from ..models.teacher import Teacher
from ..models.courses import Course
from ..models.students import Student
from flask_jwt_extended import create_access_token


class CourseTestCase(unittest.TestCase):
    def setUp(self):

        self.app = create_app(config=config_dict['test'])

        self.appctx = self.app.app_context()

        self.appctx.push()

        self.client = self.app.test_client()

        db.create_all()


    def tearDown(self):

        db.drop_all()

        self.appctx.pop()

        self.app = None

        self.client = None

    def test_student_registration(self):
        # Register a Student
        student_reg_data = {
            "email": "teststudent@gmail.com",
            "full_name": "Olubunmi Berry",
        }


        response = self.client.post('register/student', json=student_reg_data)


        user = Student.query.filter_by(email='teststudent@gmail.com').first()

        assert response.status_code == 201

    def test_student(self):


        # Retrieve all students
        response = self.client.get('/students')

        assert response.status_code == 200

        assert response.json == [{
            "id": "2",
            "email": "teststudent@gmail.com",
            "full_name": "Olubunmi Berry",
        }]