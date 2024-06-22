from flask_restful import Api, Resource
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import jsonify
from sqlalchemy import desc, func
from .models import Book, Book_issue, Rating

api = Api()

class ApiStats(Resource):
    def get(self, user_id):
        if user_id == 'admin':
            user_previews = (Book.query.join(Book_issue, Book.name == Book_issue.book_name).filter(Book_issue.request_status.in_(['preview_accept'])).group_by(Book.name)
             .with_entities(Book.name, func.count(Book_issue.id).label('previews')).all())
            user_paid = (Book.query.join(Book_issue, Book.name == Book_issue.book_name).filter(Book_issue.request_status.in_(['book_issued'])).group_by(Book.name)
             .with_entities(Book.name, func.count(Book_issue.id).label('paid')).all())
            if len(user_previews) == 0 and len(user_paid) == 0:
                return jsonify({'message': 'Data Unavailable.'})
            total_previews = sum([preview[1] for preview in user_previews])
            total_paid = sum([paid[1] for paid in user_paid])
            plt.pie([total_previews, total_paid], labels=["Previewed", "Paid"], autopct='%1.1f%%')
            plt.axis('equal')
            plt.title('Paid vs Previewed Books')
            plt.tight_layout()
            plt.savefig('static/img1.png')
            plot_img = '/static/img1.png'
            plt.clf()
            plt.close()
            ratings = Rating.query.with_entities(Rating.rating).distinct().all()
            rating_counts = [Rating.query.filter(Rating.rating == rating[0]).count() for rating in ratings]
            plt.pie(rating_counts, labels=[str(r[0]) for r in ratings], autopct='%1.1f%%')
            plt.axis('equal')
            plt.title('User Ratings')
            plt.tight_layout()
            plt.savefig('static/img2.png')
            ratings_plot_img = '/static/img2.png'
            plt.clf()
            plt.close()
            most_requested_book = (Book.query.join(Book_issue, Book.name == Book_issue.book_name).filter(Book_issue.request_status.in_(['preview_accept', 'book_issued']))
             .group_by(Book.name).with_entities(Book.name, func.count(Book_issue.id).label('requests')).order_by(desc(func.count(Book_issue.id))).first())
            top_rated_books = (Rating.query.join(Book, Rating.book_id == Book.id).group_by(Rating.book_id)
             .with_entities(Rating.book_id, func.avg(Rating.rating).label('average_rating')).order_by(desc(func.avg(Rating.rating))).all())
            top_rated_books_data = []
            book_ids = [rating[0] for rating in top_rated_books]
            book_query = Book.query.filter(Book.id.in_(book_ids))
            for book in book_query:
                for rating in top_rated_books:
                    if rating[0] == book.id:
                        top_rated_books_data.append({'name': book.name, 'average_rating': rating[1]})
            return jsonify({'previews_chart': f'{plot_img}',
                            'ratings_chart': f'{ratings_plot_img}',
                            'previews_data': [{'name': preview[0], 'count': preview[1]} for preview in user_previews],
                            'paid_data': [{'name': paid[0], 'count': paid[1]} for paid in user_paid],
                            'most_requested_book': {'name': most_requested_book[0], 'requests': most_requested_book[1]},
                            'top_rated_books': top_rated_books_data, 'user': user_id})
        else:
            user_id = int(user_id)
            user_previews = (Book.query.join(Book_issue, Book.name == Book_issue.book_name).filter(Book_issue.user_id == user_id, Book_issue.request_status.in_(['preview_accept'])).group_by(Book.name)
             .with_entities(Book.name, func.count(Book_issue.id).label('previews')).all())
            user_paid = (Book.query.join(Book_issue, Book.name == Book_issue.book_name).filter(Book_issue.user_id == user_id, Book_issue.request_status.in_(['book_issued'])).group_by(Book.name)
             .with_entities(Book.name, func.count(Book_issue.id).label('paid')).all())
            if len(user_previews) == 0 and len(user_paid) == 0:
                return jsonify({'message': 'No data available for this user.'})
            total_previews = sum([preview[1] for preview in user_previews])
            total_paid = sum([paid[1] for paid in user_paid])
            plt.pie([total_previews, total_paid], labels=["Previewed", "Paid"], autopct='%1.1f%%')
            plt.axis('equal')
            plt.title('Number of books previewed and paid by user')
            plt.tight_layout()
            plt.savefig('static/img3.png')
            preview_plot_img = '/static/img3.png'
            plt.clf()
            plt.close()
            return jsonify({'previews_chart': f'{preview_plot_img}',
                            'previews_data': [{'name': preview[0], 'count': preview[1]} for preview in user_previews],
                            'paid_data': [{'name': paid[0], 'count': paid[1]} for paid in user_paid]}) 

api.add_resource(ApiStats, '/api/stats/<string:user_id>')