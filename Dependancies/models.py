from .database import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer(), primary_key = True)
    user_name = db.Column(db.String(), nullable = False, unique = True)
    password = db.Column(db.String(), nullable = False)
    user_type = db.Column(db.String(), default = "general")
    issue_user = db.relationship("Book_issue", backref = "issue_user")

class Book_Section(db.Model):
    __tablename__ = 'Book_Section'
    id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    sec_name = db.Column(db.String(), nullable = False, unique = True)
    create_date = db.Column(db.Date(), nullable = False)
    sec_description = db.Column(db.String())
    books = db.relationship("Book", backref = "book_section")

class Book(db.Model):
    __tablename__ = 'Book'
    id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    name = db.Column(db.String(), nullable = False, unique = True)
    author_name = db.Column(db.String(), nullable=False)
    create_date = db.Column(db.Date(), nullable = False)
    book_section_name = db.Column(db.String(), db.ForeignKey("Book_Section.sec_name"), nullable = False)
    pdf_filename = db.Column(db.String(), nullable = False)
    thumbnail_filename = db.Column(db.String(), nullable = False)
    book_issues = db.relationship("Book_issue", foreign_keys='[Book_issue.id, Book_issue.book_name]', backref="book")
    ratings = db.relationship('Rating', backref='book_rating', cascade='all, delete-orphan')
    @property
    def avg_rating(self):
        if not self.ratings:
            return 'Not Rated'
        else:
            total = 0
            for k in self.ratings:
                total = total + k.rating
        return str(round(total/len(self.ratings), 2))+'/5'
     
class Book_issue(db.Model):
    __tablename__ = 'Book_issue'
    id = db.Column(db.Integer(), primary_key=True, autoincrement = True)
    book_name = db.Column(db.String(),db.ForeignKey('Book.name'), nullable = False )
    request_status = db.Column(db.String(), default = 'under_request')
    request_date = db.Column(db.Date())
    issued_date = db.Column(db.Date())
    return_date = db.Column(db.Date())
    user_id = db.Column(db.Integer(), db.ForeignKey("User.id"))
    book_id = db.Column(db.Integer(), db.ForeignKey("Book.id"))
    payment_amount = db.Column(db.Integer(), default = 0)
    def if_delete(self):
        if self.return_date and self.return_date <= datetime.now().date():
            return True
        return False

class Rating(db.Model):
    __tablename__ = 'Rating'
    user_id = db.Column(db.Integer(), db.ForeignKey('User.id'))
    book_id = db.Column(db.Integer(), db.ForeignKey('Book.id'))
    rating = db.Column(db.Float(), nullable=False)
    feedback = db.Column(db.String(), nullable=False)
    user = db.relationship('User', backref=db.backref('ratings', lazy=True))    
    


