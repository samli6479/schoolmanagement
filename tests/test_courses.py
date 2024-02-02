import unittest
from .. import create_app
from ..config.config import config_dict
from ..utils import db
from ..models.courses import Course


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


    def test_courses(self):



        # Register a course
        course_registration_data = {
            "name": "BCH101",
        }

        response = self.client.post('/courses', json=course_registration_data)

        assert response.status_code == 201

        courses = Course.query.all()

        course_id = courses[0].id

        course_name = courses[0].name

        assert len(courses) == 1

        assert course_id == 1

        assert course_name == "BCH101"

        # Retrieve a course's details by ID
        response = self.client.get('courses/1')

        assert response.status_code == 200

        assert response.json == {
            "id": 1,
            "name": "BCH101",
        }

        # Get all courses
        response = self.client.get('/courses')

        assert response.status_code == 200

        assert response.json == [{
            "id": 1,
            "name": "BCH101",
        }]

         # Update a course's details
        course_to_update_data = {
            "name": "CHM101",
        }

        response = self.client.put('/courses/1', json=course_to_update_data)

        assert response.status_code == 200

        assert response.json == {
            "id": 1,
            "name": "CHM101",
        }

        # Enroll a student for a course
        course__update_data = {
            "course_id": "1",
            "student_id": "1"
        }
        response = self.client.post('/courses/students',json=course_to_update_data)
        
        assert response.status_code == 201

        assert response.json == {"message": "You have Successfully Been Enrolled"}


        # Get all students enrolled for a course
        response = self.client.get('/courses/1/students')

        assert response.status_code == 200

        assert response.json == [{
            "id": 1,
		"course_name": "BUS121",
		"full_name": "Bode,Peter",
        }]


        # Delete a course
        response = self.client.delete('/courses/1')
        assert response.status_code == 200