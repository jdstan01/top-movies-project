from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
API_KEY = "12082c915f8a659dbb5fcb79aa286bb2"
URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_INFO = "https://api.themoviedb.org/3/movie/"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie-ranking.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class RateMovieForm(FlaskForm):
    new_rating = StringField(label="Your Rating Out of 10 E.G. 7.5", validators=[DataRequired()])
    new_review = StringField(label='Your Review', validators=[DataRequired()])
    submit = SubmitField(label='Done')


class FindMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"<Book {self.title}>"


with app.app_context():
    db.create_all()

with app.app_context():
    new_movie = Movie(
        title="Phone Booth",
        year=2002,
        description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
        rating=7.3,
        ranking=10,
        review="My favourite character was the caller.",
        img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    )


@app.route("/")
def home():
    # order all the movies by rating
    all_movies = db.session.query(Movie).order_by("rating").all()
    # gets order from index[0]+++ index is index, movie is movie, len of movies start with number of movies
    # e.g. 10th movie = 10 - 0 || 9th movie = 10 - 1 || 8th movie = 10 - 2
    for index, movie in enumerate(all_movies):
        movie.ranking = len(all_movies) - index
    db.session.commit()

    return render_template("index.html", all_movies=all_movies)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    movie_title = Movie.query.filter_by(id=id).first()
    title_to_display = movie_title.title
    form = RateMovieForm()
    new_rating = request.form.get('new_rating')
    new_review = request.form.get('new_review')
    if request.method == "POST":
        movie_to_update = Movie.query.filter_by(id=id).first()
        movie_to_update.rating = new_rating
        movie_to_update.review = new_review
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("edit.html", form=form, title_to_display=title_to_display)


@app.route('/delete/<int:id>', methods=["GET", "POST"])
def delete(id):
    if request.method == "GET":
        movie_id = id
        movie_to_delete = Movie.query.get(movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=["GET", "POST"])
def add_movie():
    form = FindMovieForm()
    if form.validate_on_submit():
        params = {
            "api_key": API_KEY,
            "query": request.form.get('title')
        }
        response = requests.get(URL, params)
        results = response.json()['results']

        return render_template("select.html", results=results)

    return render_template('add.html', form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_INFO}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": API_KEY})
        data = response.json()
        new_movie = Movie(
            title=data['title'],
            year=data['release_date'].split('-')[0],
            description=data['overview'],
            rating=data['vote_average'],
            img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
        )
        with app.app_context():
            db.session.add(new_movie)
            db.session.commit()

        movie = Movie.query.filter_by(title=data['title']).first()
        movie_id = movie.id
        return redirect(url_for('edit', id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
