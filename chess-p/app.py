from flask import Flask, request, render_template, redirect, url_for, session, flash
import requests, mysql.connector, json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

def create_db_connection():
    connection = mysql.connector.connect(host='localhost', user='root', password='qwerty123', database='chess_analyzer')
    return connection

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = create_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
        
        cursor.close()
        connection.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = create_db_connection()
        cursor = connection.cursor()
        
        hashed_password = generate_password_hash(password)
        
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            connection.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username already exists', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/fetch', methods=['POST'])
def fetch():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    username = request.form['username']
    req_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }
    req_response = requests.get(req_url, headers=headers)
    if req_response.status_code == 200:
        game_archives = req_response.json()
        if game_archives:
            game_archive_latest_month = game_archives["archives"][-1]
            latest_month_game_data = requests.get(game_archive_latest_month, headers=headers)

            if latest_month_game_data.status_code == 200:
                return render_template('index.html', games=latest_month_game_data.json()["games"], username=username)
            else:
                return render_template('index.html', error=f"Couldn't fetch latest month game data. Status code:{latest_month_game_data.status_code}", username=username)
        else:
            return render_template('index.html', error=f"Archives are empty for the user {username}", username=username)
    else:
        return render_template('index.html', error=f"Couldn't fetch data for user {username}. Status code:{req_response.status_code}", username=username)

@app.route('/save_game', methods=['POST'])
def save_game():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    game_data = request.form.get('game_data')
    username = request.form.get('username')
    game = json.loads(game_data)
    game_pgn = game['pgn']
    game_white = game['white']['username']
    game_black = game['black']['username']
    
    connection = create_db_connection()
    cursor = connection.cursor()

    insert_query = "INSERT INTO games (user_id, chess_com_game_id, white_player, black_player, pgn) VALUES (%s, %s, %s, %s, %s)"
    values = (session['user_id'], game['url'], game_white, game_black, game_pgn)

    try:
        cursor.execute(insert_query, values)
        connection.commit()
        return render_template('index.html', success="Game saved successfully", username=username)
    except mysql.connector.Error as err:
        return render_template('index.html', error=f"Error saving game: {err}", username=username)
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)