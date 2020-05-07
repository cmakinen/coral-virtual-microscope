from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app import db

class Slides(db.Model):
    __tablename__ = 'slides'
    id = db.Column(Integer, primary_key=True)
    filename = db.Column(String)
    number = db.Column(String)
    genus = db.Column(String)
    species = db.Column(String)
    stain = db.Column(String)
    accession_number = db.Column(String)
    source = db.Column(String)
    contributor = db.Column(String)
    processing = db.Column(String)
    comments = db.Column(String)
    date_collected = db.Column(String)
    date_received = db.Column(String)
    date_sent_to_aperio = db.Column(String)
    sample = db.Column(String)
    infect = db.Column(String)
    study = db.Column(String)
    collection_site = db.Column(String)
    histopathologic_description = db.Column(String)
    attachment = db.Column(String)

    def prop_map(self):
        slide = {}
        slide["id"] = self.id
        slide["filename"] = self.filename
        slide["number"] = self.number
        slide["genus"] = self.genus
        slide["species"] = self.species
        slide["stain"] = self.stain
        slide["accession_number"] = self.accession_number
        slide["source"] = self.source
        slide["contributor"] = self.contributor
        slide["processing"] = self.processing
        slide["comments"] = self.comments
        slide["date_collected"] = self.date_collected
        slide["date_received"] = self.date_received
        slide["date_sent_to_aperio"] = self.date_sent_to_aperio
        slide["sample"] = self.sample
        slide["infect"] = self.infect
        slide["study"] = self.study
        slide["collection_site"] = self.collection_site
        slide["histopathologic_description"] = self.histopathologic_description
        slide["attachment"] = self.attachment

        return slide

    # def __repr__(self):
    #     return "<Book(title='{}', author='{}', pages={}, published={})>" \
    #         .format(self.title, self.author, self.pages, self.published)
    #

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(Integer, primary_key=True)
    lastname = db.Column(String)
    firstname = db.Column(String)
    email = db.Column(String, nullable=False)
class Auth(db.Model):
    __tablename__ = 'auth'
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, db.ForeignKey('users.id'))
    password = db.Column(String)

class Courses(db.Model):
    __tablename__ = 'courses'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String, nullable=False)
    description = db.Column(String)
    def prop_map(self):
        course = {}
        course["id"] = self.id
        course["name"] = self.name
        course["description"] = self.description
        return course

class Lessons(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(Integer, primary_key=True)
    course_id = db.Column(Integer, db.ForeignKey('courses.id'))
    order = db.Column(Integer)
    name = db.Column(String, nullable=False)
    description = db.Column(String)
    def prop_map(self):
        lesson = {}
        lesson["id"] = self.id
        lesson["course_id"] = self.course_id
        lesson["order"] = self.order
        lesson["name"] = self.name
        lesson["description"] = self.description
        return lesson

class LessonSlides(db.Model):
    __tablename__ = 'lesson_slides'
    id = db.Column(Integer, primary_key=True)
    lesson_id = db.Column(Integer, db.ForeignKey('lessons.id'))
    slide_id = db.Column(Integer, db.ForeignKey('slides.id'))
    description = db.Column(String)
    def prop_map(self):
        lesson_slide = {}
        lesson_slide["id"] = self.id
        lesson_slide["lesson_id"] = self.lesson_id
        lesson_slide["slide_id"] = self.slide_id
        lesson_slide["description"] = self.description
        return lesson_slide

class Annotations(db.Model):
    __tablename__ = 'annotations'
    id = db.Column(Integer, primary_key=True)
    text = db.Column(String)