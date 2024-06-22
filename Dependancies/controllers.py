from flask import render_template, redirect, request, url_for, send_file
from flask import current_app as app
from .models import *
import os
from datetime import datetime
import requests

with app.app_context():
    db.create_all()


@app.route('/', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form.get("user_name")
        password = request.form.get("password")
        if not user_name or not password:
            return render_template('alert.html', message_type='danger', reason='Login Failed', message='Username or Password cannot be NULL!',
                                       link='/', link_message='Try Again' )
        user = User.query.filter_by(user_name = user_name).first()
        if user:
            if user.password == password:
                if user.user_type == "admin":
                    return redirect('/admin')
                else:
                    return redirect(f'/login/{user.id}') 
            else:
                return render_template('alert.html', message_type='warning', reason='Login Failed', message='Please Check your Password!',
                                       link='/', link_message='Try Again' )
        else:
            return render_template('alert.html', message_type='warning', reason='Login Failed', message="Entered user does not exist!",
                                       link='/', link_message='Try Again' )
    else:
        return render_template('login.html')
    
@app.route('/register', methods = ['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        user_name = request.form.get("user_name")
        password = request.form.get("password")
        if not user_name or not password:
            return render_template('alert.html', message_type='danger', reason='Register Failed', message="Username or Password cannot be NULL!",
                                       link='/register', link_message='Try Again' ) 
        this_user = User.query.filter_by(user_name = user_name).first()
        if this_user:
            return render_template('alert.html', message_type='warning', reason='Register Failed', message="User already exists! Try using another username",
                                       link='/register', link_message='Try Again' )
        elif "@" not in user_name:
            return render_template('alert.html', message_type='warning', reason='Register Failed', message="Username should contain @",
                                       link='/register', link_message='Try Again' )
        elif len(password) < 8 or len(password) > 20:
             return render_template('alert.html', message_type='warning', reason='Register Failed', message="Your password must be 8-20 characters long.",
                                       link='/register', link_message='Try Again' )     
        else:
            new_user = User(user_name = user_name, password = password)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/') 
    return render_template('register.html')

@app.route('/login/<int:user_id>', methods=['GET', 'POST'])
def user(user_id):
    if user_id:    
        user = User.query.get(user_id)
        req_or_pay = Book_issue.query.filter((Book_issue.request_status=='preview_req') & (Book_issue.user_id==user_id) | (Book_issue.request_status=='pending_payment') & (Book_issue.user_id==user_id) | (Book_issue.request_status=='under_request') & (Book_issue.user_id==user_id)).all()
        issued_books = Book_issue.query.filter((Book_issue.request_status=='book_issued') & (Book_issue.user_id==user_id)).all()
        preview_books = Book_issue.query.filter_by(request_status = 'preview_accept').all()
        for book_issue in preview_books:
            if book_issue.if_delete():
                db.session.delete(book_issue)
        preview_accepted = Book_issue.query.filter((Book_issue.request_status=='preview_accept') & (Book_issue.user_id==user_id)).all()
        db.session.commit()
        Sections =  Book_Section.query.all()
        return render_template('user_dash.html', user = user, Requested = req_or_pay, preview_books=preview_accepted, Book_Section=Sections, issued_books=issued_books)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    under_request = Book_issue.query.filter_by(request_status = 'under_request').all()
    preview_request = Book_issue.query.filter_by(request_status = 'preview_req').all()
    preview_books = Book_issue.query.filter_by(request_status = 'preview_accept').all()
    for book_issue in preview_books:
        if book_issue.if_delete():
            db.session.delete(book_issue)
    preview_accepted = Book_issue.query.filter_by(request_status = 'preview_accept').all()
    pending_payment = Book_issue.query.filter_by(request_status = 'pending_payment').all()
    issued_books = Book_issue.query.filter_by(request_status = 'book_issued').all()
    Sections =  Book_Section.query.all()
    return render_template('admin_dash.html',issued_books=issued_books, preview_accepted=preview_accepted, under_request=under_request, pending_payment=pending_payment, Book_Section=Sections, preview_request=preview_request)

@app.route('/profile/<user_id>', methods=['GET', 'POST'])
def profile_data(user_id):
    if user_id:    
        response = requests.get(f"http://localhost:5000/api/stats/{user_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("message"):
                if user_id == 'admin':
                    return render_template('alert.html', message_type='warning', reason='Fetch Failed', message=data["message"],
                                        link='/admin', link_message='Go to Dashboard.' )
                else:
                    return render_template('alert.html', message_type='warning', reason='Fetch Failed', message=data["message"],
                                        link=f'/login/{user_id}', link_message='Go to Dashboard.' )
            elif user_id == 'admin':
                return render_template("profile.html", data=data)
            else:
                user = User.query.get(int(user_id))
                return render_template("profile.html", data=data, user=user)
        else:
            return f'<h2>Error: {response.status_code}</h2>'

@app.route('/request/<int:user_id>/<int:book_id>/', methods=['GET', 'POST'])
def new_req(user_id,book_id):
    if user_id and book_id:    
        book = Book.query.get(book_id)
        book_issue = Book_issue.query.filter((Book_issue.book_name == book.name) & (Book_issue.user_id == user_id)).first()
        section = Book_Section.query.filter_by(sec_name=book.book_section_name).first()
        if book_issue is not None :
            return render_template('alert.html', message_type='warning', reason='Request Failed', message='Book is Already under process!',
                                        link=f'/{user_id}/section/{section.id}', link_message='Try Another Book' )
        datetime_now = datetime.now()
        new_request = Book_issue(book_name=book.name, request_date=datetime_now, user_id=user_id)
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('user', user_id=user_id))

@app.route('/preview_request/<int:user_id>/<int:book_id>/', methods=['GET', 'POST'])
def preview_req(user_id,book_id):
    if user_id and book_id:    
        book = Book.query.get(book_id)
        book_issue1 = Book_issue.query.filter((Book_issue.book_name == book.name) & (Book_issue.user_id == user_id)).first()
        book_issue2 = Book_issue.query.filter((Book_issue.request_status=='preview_req') & (Book_issue.user_id==user_id)).count()
        if book_issue1 is not None :
            section = Book_Section.query.filter_by(sec_name=book.book_section_name).first()
            return render_template('alert.html', message_type='warning', reason='Preview Failed', message='Book is Already under Preview!',
                                        link=f'/{user_id}/section/{section.id}', link_message='Try Another Book' )
        elif book_issue2:
            if book_issue2 >= 5:
                return render_template('alert.html', message_type='warning', reason='Preview Failed', message='Book quota limit of 5 exceeded!',
                                        link=f'/login/{user_id}', link_message='Return Books and Try Again' )
        datetime_now = datetime.now()
        new_request = Book_issue(book_name=book.name, request_date=datetime_now, user_id=user_id, request_status = 'preview_req')
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('user', user_id=user_id))

@app.route('/cancel_request/<int:request_id>', methods=['GET', 'POST'])
def cancel_request(request_id):
    if request_id:    
        request_cancel = Book_issue.query.get(request_id)
        user_id = request_cancel.user_id
        db.session.delete(request_cancel)
        db.session.commit()
        return redirect(url_for('user', user_id=user_id))

@app.route('/cancel_payment_request/<int:request_id>', methods=['GET', 'POST'])
def cancel_payment_request(request_id):
    if request_id:
        request_cancel = Book_issue.query.get(request_id)
        db.session.delete(request_cancel)
        db.session.commit()
        return redirect(url_for('admin'))

@app.route('/accept_req/<int:req_id>', methods=['GET', 'POST'])
def review_req(req_id):
    if req_id:    
        book_issue = Book_issue.query.get(req_id)
        if book_issue.request_status == 'under_request':
            if request.method == 'POST':
                amount = request.form.get("amount")
                issue = Book_issue.query.get(req_id)
                issue.request_status="pending_payment"
                issue.payment_amount=amount
                db.session.commit()
                return redirect(url_for('admin'))
            else:
                return render_template('review_request.html', req_id=req_id, book=book_issue)
        elif  book_issue.request_status=="preview_req":
            if request.method == 'POST':
                return_date = request.form.get("return_date")
                returning_date = datetime.strptime(return_date, '%Y-%m-%d').date()
                issue = Book_issue.query.get(req_id)
                issue.request_status="preview_accept"
                issue.return_date=returning_date
                db.session.commit()
                return redirect(url_for('admin'))
            else:
                return render_template('preview_request.html', req_id=req_id, book=book_issue)    

@app.route('/make_payment/<int:request_id>', methods=['GET', 'POST'])
def payment_request(request_id):
    if request_id:     
        issue = Book_issue.query.get(request_id) 
        if request.method == 'POST':
            issue.request_status="book_issued"
            issue.issued_date=datetime.now() 
            db.session.commit()
            return render_template('alert.html', message_type='success', reason='Payment Success', message='Your payment is being processed!',
                                        link=f'/login/{issue.user_id}', link_message='Return to Dashboard' )
        else:      
            return render_template('make_payment.html', req_id=request_id, book=issue)   

@app.route('/return_book/<int:request_id>', methods=['GET'])
def return_request(request_id):
    if request_id:
        request_cancel = Book_issue.query.get(request_id)
        user_id = request_cancel.user_id
        db.session.delete(request_cancel)
        db.session.commit()
        return render_template('alert.html', message_type='success', reason='Return Success', message='Your return is successfully processed!',
                                        link=f'/login/{user_id}', link_message='Return to Dashboard' )

@app.route('/create/newbook/', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        author_name = request.form.get("author_name")
        book_name = request.form.get("book_name")
        is_book = Book.query.filter_by(name=book_name).first()
        if is_book:
             return render_template('alert.html', message_type='danger', reason='Add Error', message='Book with same name already exists. Try using a different name.',
                                        link='/create/newbook/', link_message='Go Back' )
        sec_name = request.form.get("sec_name")
        sec_description = request.form.get("sec_description")
        uploaded_pdf_file = request.files['pdf_file']
        uploaded_thumbnail_file = request.files['thumbnail_file']
        pdf_filename = uploaded_pdf_file.filename
        thumbnail_filename = uploaded_thumbnail_file.filename
        directory1 = os.path.dirname(os.path.join(app.config['pdf_folder'], pdf_filename))
        directory2 = os.path.dirname(os.path.join(app.config['thumbnail_folder'], thumbnail_filename))
        if not os.path.exists(directory1):
            os.makedirs(directory1)
        if not os.path.exists(directory2):
            os.makedirs(directory2)
        uploaded_pdf_file.save(os.path.join(app.config['pdf_folder'], pdf_filename))
        uploaded_thumbnail_file.save(os.path.join(app.config['thumbnail_folder'], thumbnail_filename))
        datetime_now = datetime.now()
        new_book= Book(name=book_name, author_name=author_name, create_date=datetime_now, 
                    book_section_name=sec_name, pdf_filename=pdf_filename,thumbnail_filename=thumbnail_filename)
        db.session.add(new_book)
        db.session.commit()
        db.session.close()
        sections = Book_Section.query.filter_by(sec_name=sec_name).first()
        if  not sections:
            datetime_now = datetime.now()
            new_section = Book_Section(sec_name=sec_name, create_date=datetime_now, sec_description=sec_description)
            db.session.add(new_section)
            db.session.commit()
        return redirect(url_for('admin'))
    else:
        return render_template('new_book.html')
    
@app.route('/<string:user_id>/section/<int:sec_id>', methods=['GET', 'POST'])
def section(user_id,sec_id):
     if user_id and sec_id:    
        book_section = Book_Section.query.get(sec_id)
        books = []
        for book in book_section.books:
            book_ratings = Rating.query.filter_by(book_id=book.id).all()
            feedbacks = [(User.query.get(rating.user_id).user_name, rating.feedback) for rating in book_ratings]
            books.append((book, feedbacks))
        user = User.query.get(user_id)
        return render_template('section.html', book_section=book_section, books=books,user=user)  

@app.route('/view/<int:request_id>/<int:user_id>', methods=['GET', 'POST'])
def view_book(request_id,user_id):
    if request_id and user_id:     
        issue = Book_issue.query.get(request_id)
        if issue.request_status == 'preview_accept':
            books = issue.book
            return  render_template('view_book.html', book=books, user_id=user_id)
    
@app.route('/viewbook/<int:book_id>/<string:sec_id>', methods=['GET', 'POST'])
def view(book_id,sec_id):
    if book_id and sec_id:
        book = Book.query.get(book_id)
        return  render_template('view_book.html', book=book, sec_id=sec_id)

@app.route('/editbook/<int:book_id>/', methods=['GET', 'POST'])
def edit_book(book_id):
    if book_id:    
        if request.method == 'POST':
            author_name = request.form.get("author_name")
            book_name = request.form.get("book_name")
            sec_name = request.form.get("sec_name")
            sec_description = request.form.get("sec_description")
            uploaded_pdf_file = request.files['pdf_file']
            uploaded_thumbnail_file = request.files['thumbnail_file']
            pdf_filename = uploaded_pdf_file.filename
            thumbnail_filename = uploaded_thumbnail_file.filename
            book = Book.query.get(book_id)
            section = book.book_section
            book.author_name = author_name
            book.name = book_name
            sections = Book_Section.query.filter_by(sec_name=sec_name).first()
            if  not sections:
                datetime_now = datetime.now()
                new_section = Book_Section(sec_name=sec_name, create_date=datetime_now, sec_description=sec_description)
                db.session.add(new_section)
                book.book_section = new_section
                book.book_section_name = sec_name
                db.session.commit()
                db.session.close()
            else:
                section.sec_description = sec_description
                book.book_section_name = sec_name
                book.book_section = section
                db.session.commit()
                db.session.close()
                
            if pdf_filename:
                previous_pdf_filename = book.pdf_filename
                os.remove(os.path.join(app.config['pdf_folder'], previous_pdf_filename))
                book.pdf_filename = pdf_filename
                uploaded_pdf_file.save(os.path.join(app.config['pdf_folder'], pdf_filename))
            if thumbnail_filename:    
                previous_thumbnail_filename = book.thumbnail_filename
                os.remove(os.path.join(app.config['thumbnail_folder'], previous_thumbnail_filename))
                book.thumbnail_filename = thumbnail_filename
                uploaded_thumbnail_file.save(os.path.join(app.config['thumbnail_folder'], thumbnail_filename))    
            db.session.commit()
            return redirect(url_for('admin'))
        else:
            book = Book.query.get(book_id)
            section = book.book_section
            return  render_template('new_book.html', book=book, section=section)

@app.route('/removebook/<int:book_id>/', methods=['GET', 'POST'])
def remove_book(book_id):
    if book_id:    
        book = Book.query.get(book_id)
        for book_issue in book.book_issues:
            db.session.delete(book_issue)
        db.session.delete(book)
        db.session.commit()
        return  redirect(url_for('admin'))

@app.route('/removesection/<int:sec_id>/', methods=['GET', 'POST'])
def remove_section(sec_id):
    if sec_id:
        book_section = Book_Section.query.get(sec_id)
        db.session.delete(book_section)
        db.session.commit()
        return  redirect(url_for('admin'))

@app.route('/download/pdf/<int:request_id>', methods=['GET', 'POST'])   
def download_book(request_id):
    if request_id:
        issue = Book_issue.query.get(request_id)
        if issue.request_status == 'book_issued':
            book =  issue.book
            return  send_file(f'static\\pdf_folder\\{book.pdf_filename}', as_attachment=True)
        

@app.route('/search/<string:any>', methods=['POST'])
def search(any):
    if any:
        if request.method == 'POST':
            if  any == "admin":
                search_query = request.form.get("search_query")
                books = Book.query.filter((Book.name.contains(search_query)) | (Book.author_name.contains(search_query)) | (Book.book_section_name.contains(search_query))).all()
                return render_template('search_results.html',user='admin', books=books, search_query=search_query)
            else:
                user =  User.query.filter_by(user_name=any).first()
                search_query = request.form.get("search_query")
                books = Book.query.filter((Book.name.contains(search_query)) | (Book.author_name.contains(search_query)) | (Book.book_section_name.contains(search_query))).all()
                return render_template('search_results.html',user=user, books=books, search_query=search_query)
    
@app.route('/book/<int:req_id>/rate', methods=['GET', 'POST'])
def rate_book(req_id):
    if req_id:    
        issue = Book_issue.query.get(req_id)
        book = Book.query.filter_by(name=issue.book_name).first()
        if request.method == 'POST':
            user_rating = Rating.query.filter((Rating.user_id==issue.user_id) & (Rating.book_id==book.id)).first()
            if user_rating:
                user_rating.feedback = request.form.get('feedback')
                user_rating.rating = request.form.get('rating')
                db.session.commit()
                return redirect(url_for('user', user_id=issue.user_id)) 
            else:
                rating = request.form.get('rating')
                feedback = request.form.get('feedback')
                rating = Rating(user_id=issue.user_id, book_id=book.id,  rating=rating, feedback=feedback)
                book_issue = Book_issue.query.filter_by(user_id=issue.user_id, request_status='book_issued').first()
                if book_issue:
                    db.session.add(rating)
                    db.session.commit()
                return redirect(url_for('user', user_id=issue.user_id))         
        return render_template('rating.html', req_id=req_id, book=book)