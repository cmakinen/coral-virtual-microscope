from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import *
import sqlite3
from app import db
from models import Slides

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True)
print(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

def recreate_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def loadpgsql():
    conn = sqlite3.connect('all_slides.db')
    c = conn.cursor()
    c.execute("select * from slides")
    records = c.fetchall()
    properties = {}
    print(Slides.query.all())

    for row in records:
        i = 0
        slide = Slides()
        for key in c.description:
            if key[0].title() == "Filename" :
                slide.filename = row[i]
            if key[0].title() == "Number" :
                slide.number = row[i]
            if key[0].title() == "Genus" :
                slide.genus = row[i]
            if key[0].title() == "Species" :
                slide.species = row[i]
            if key[0].title() == "Stain" :
                slide.stain = row[i]
            if key[0].title() == "Accession_Number" :
                slide.accession_number = row[i]
            if key[0].title() == "Source" :
                slide.source = row[i]
            if key[0].title() == "Contributor" :
                slide.contributor = row[i]
            if key[0].title() == "Processing" :
                slide.processing = row[i]
            if key[0].title() == "Comments" :
                slide.comments = row[i]
            if key[0].title() == "Date_Sent_To_Aperio" :
                slide.date_sent_to_aperio = row[i]
            if key[0].title() == "Date_Collected" :
                slide.date_collected = row[i]
            if key[0].title() == "Date_Received" :
                slide.date_received = row[i]
            if key[0].title() == "Sample" :
                slide.sample = row[i]
            if key[0].title() == "Infect" :
                slide.infect = row[i]
            if key[0].title() == "Study" :
                slide.study = row[i]
            if key[0].title() == "Collection_Site" :
                slide.collection_site = row[i]
            if key[0].title() == "Histopathologic_Description" :
                slide.histopathologic_description = row[i]
            if key[0].title() == "Attachment" :
                slide.attachment = row[i]

            properties[key[0].title()] = row[i]
            i = i + 1
        db.session.add(slide)
        db.session.commit()
        db.session.flush()
    conn.close()
    print(Slides.query.all())

db.session.close()

loadpgsql()