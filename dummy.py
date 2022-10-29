import sqlite3
from datetime import datetime
import os
import time
from getpass import getpass

conn = sqlite3.connect('./temp.db')
cur = conn.cursor()


def start_session(id):
    # Implement Start a session
    print()
    cur.execute("select * from sessions where uid=?", (id,))
    data = cur.fetchall()

    # Storing all the Sno related to given Uid
    store = []
    for row in data:
        store.append(row[1])

    # Finding a unique Sno
    i = 1
    while True:
        if (i not in store):
            sno = i
            break
        i = i + 1

    now = datetime.now()
    current_date = now.date()

    query_vals = (id, sno, current_date)
    cur.execute("INSERT INTO sessions (uid, sno, start) VALUES (?,?,?)", query_vals)
    conn.commit()

    return sno


def search_songs_playlists():
    # Implement Search for songs and playlists
    clearTerminal()
    while True:
        keyword = input("Please enter one or more keywords to search for, each separated by a single space: ")
        keywords = keyword.split(' ')
        uniqueKeywords = []
        i = 1
        for k in keywords:
            if (k.lower() not in uniqueKeywords):
                uniqueKeywords.append(k.lower())
                cur.execute("SELECT * from songs where title like '%{}%';".format(k))
                data = cur.fetchall()
                # print(data)
                for row in data:
                    print('{}.\tSong ID: {} | Title: {} | Duration: {} seconds'.format(i, row[0], row[1], row[2]))
                    i += 1


def search_artists():
    keyword = input('Search for an artist\'s name: ').strip()
    cur.execute("with e1 as (Select a.name ename, count(a.name) num from songs s, artists a, perform p where a.aid = p.aid and s.sid = p.sid and (s.title like '%{}%' or a.name like '%{}%') group by ename)".format(keyword, keyword) + " Select a.name, a.nationality, count(s.sid) from songs s, artists a, perform p, e1 where a.aid = p.aid and s.sid = p.sid and e1.ename = a.name group by a.name order by num desc")
    data = cur.fetchall()

    if len(data) == 0:
        print('\nSorry! There is no artist with this name')

    i = 0
    print()
    print(str('Found ' + str(len(data)) + ' matching results (Name, Nationality, Number of Songs)').center(150, '-'))

    for j in data:
        print(j)
        i +=1
        if i == len(data):
            print('This is end of our search result.'.center(150, '-'))

        if i % 5 == 0:
            print()
            UserInput = input('Do you want to continue searching ' + str(len(data) -i) + ' left (Press Y/N) or Select an artist (type name)? ').strip()
            print()
            if UserInput.lower() == 'y':
                continue

            elif UserInput.lower() == 'n':
                print()
                print('This is end of our search result.'.center(150, '-'))
                break

            else:
                cur.execute("Select s.sid, s.title, s.duration from songs s, artists a, perform p where a.aid = p.aid and s.sid = p.sid and a.name = ?;", (UserInput.title(),))
                artist_data = cur.fetchall()

                if len(artist_data) == 0:
                    print('Invalid choice ')
                    break

                print(str('Songs of ' + UserInput.title() + ' (id, title, duration)').center(150, '-'))
                for i in artist_data:
                    print(i)

                print()
                SongSelection = input('Do you want to select any song - Enter it\'s name: ').strip()
                # Use this SongSelection variable to perform a song action
                break






def user_session(id):
    # User Session
    menu = "User Session\n1. Start a session\n2. Search for songs and playlists\n3. Search for artists\n4. End the session"
    while True:
        print(menu)

        user_option = input(str("Please enter an option #: "))
        while (user_option not in ["1", "2", "3", "4"]):
            clearTerminal()
            print(menu)
            user_option = input(str("Invalid option entered. Please enter an option #: "))

        if user_option == "1":
            returned_sno = start_session(id)

        elif user_option == "2":
            search_songs_playlists()

        elif user_option == "3":
            search_artists()

        elif user_option == "4":
            now = datetime.now()
            current_date = now.date()
            cur.execute("UPDATE sessions set end = ? where uid = ? and sno = ?", (current_date, id, returned_sno))
            conn.commit()
            break

        else:
            print("Please enter a valid Option #")


def artist_session():
    print("Artist Session")


def clearTerminal():
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the system terminal to look cleaner


def main():
    while True:
        userfound = False
        artistfound = False

        clearTerminal()  # Clear the system terminal to look cleaner
        id = input("Login Screen: Please enter your ID:  ")
        cur.execute("select name from users where uid=?", (id,))
        data = cur.fetchall()

        if not data:
            userfound = False
        else:
            userfound = True
            foundUserName = data[0][0]

        cur.execute("select name from artists where aid=?", (id,))
        data = cur.fetchall()

        if not data:
            artistfound = False
        else:
            artistfound = True
            foundArtistName = data[0][0]

        # If the ID exists in both users and artists
        if (artistfound == True and userfound == True):
            print("This ID exists for both a user and an artist")
            print("Press 1 to log in as the user {}: {}".format(id, foundUserName))
            print("Press 2 to log in as the artist {}: {}".format(id, foundArtistName))

            user_option = 0
            user_option = input("\nPlease enter your option: ")

            while (user_option != "1" and user_option != "2"):
                print("\r", end="")
                user_option = input("Invalid option. Please enter either 1 for user or 2 for artist: ")

            userpass = getpass(
                prompt=("Please enter your password (as a" + (" user): " if user_option == "1" else "n artist): ")))
            cur.execute("select {} from {} where {}=? and pwd=?".format(
                "uid" if user_option == "1" else "aid", "users" if user_option == "1" else "artists",
                "uid" if user_option == "1" else "aid"), (id, userpass))
            data = cur.fetchall()

            while (not data):
                userpass = getpass(prompt="Incorrect password. Please try again: ")
                cur.execute("select {} from {} where {}=? and pwd=?".format(
                    "uid" if user_option == "1" else "aid", "users" if user_option == "1" else "artists",
                    "uid" if user_option == "1" else "aid"), (id, userpass))
                data = cur.fetchall()

            print("Log-in Successful! Navigating to main screen...")
            time.sleep(0)
            clearTerminal()
            user_session(id)


        # If the id exists for only the user
        elif (userfound == True and artistfound == False):
            userpass = getpass(prompt="Please enter your password: ")
            cur.execute("select uid from users where uid=? and pwd=?", (id, userpass))
            data = cur.fetchall()

            while (not data):
                userpass = getpass(prompt="Incorrect password. Please try again: ")
                cur.execute("select uid from users where uid=? and pwd=?", (id, userpass))
                data = cur.fetchall()
            else:
                print("Log-in Successful! Navigating to main screen...")
                time.sleep(0)
                clearTerminal()
                user_session(id)

        # If the id exists for only the artists
        elif (userfound == False and artistfound == True):
            userpass = getpass(prompt="Please Enter your Password: ")
            cur.execute("select aid from artists where aid=? and pwd=?", (id, userpass))
            data = cur.fetchall()

            while (not data):
                userpass = getpass(prompt="Incorrect password. Please try again: ")
                cur.execute("select aid from artists where aid=? and pwd=?", (id, userpass))
                data = cur.fetchall()
            else:
                print("Log-in Successful! Navigating to main screen...")
                time.sleep(0)
                clearTerminal()
                user_session(id)

                # Invalid Id. Ask for Sign-up
        else:
            print("No valid user or artist ID found. Would you like to sign-up as a new user?")
            user_option = input(str("Press 1 to continue!! "))

            if user_option == "1":
                id = input("Please provide a user-id: ")
                cur.execute("select uid from users where uid=?", (id,))
                data = cur.fetchall()

                if not data:
                    name = input("Please provide a name: ")
                    password = input("Please provide a Password: ")

                    query_vals = (id, name, password)
                    cur.execute("INSERT INTO users (uid, name, pwd) VALUES (?,?,?)", query_vals)
                    conn.commit()

                    print("Sign-Up Successfull! You are now logged-in")
                    user_session(id)

                else:
                    print("This user-id already exists.")


# main()
search_artists()